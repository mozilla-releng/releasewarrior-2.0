Currently, maple is our taskcluster beta relpro migration area.

---
## diff taskgraphs

[`taskgraph-gen.py`](https://hg.mozilla.org/build/braindump/file/tip/taskcluster/taskgraph-diff/taskgraph-gen.py) lets you generate a bunch of graphs from a given revision. Once you generate graphs from 2 revisions, [`taskgraph-diff.py`](https://hg.mozilla.org/build/braindump/file/tip/taskcluster/taskgraph-diff/taskgraph-diff.py) lets you diff the two sets of graphs. This means you can diff the graphs generated from tip of central against the tip of maple, or from the tip of maple against maple + your patch, or whatever.

e.g.

```
# First create virtualenv with dictdiffer and activate it
# Then run:
cd mozilla-unified
hg up -r central
../taskgraph-diff/taskgraph-gen.py --overwrite central
hg up -r maple
../taskgraph-diff/taskgraph-gen.py --overwrite maple
../taskgraph-diff/taskgraph-diff.py central maple
# diffs are in ../taskgraph-diff/json/maple/*.diff
```

In the above example, I've softlinked my `braindump/taskcluster/taskgraph-diff` directory to be a sibling of `mozilla-unified`.

Caveats:

- the diffs are kind of interesting to read. They're [dictdiffer](https://dictdiffer.readthedocs.io/en/latest) diffs [1]. Once you get the hang of them they work.
- the params are checked in along with the scripts. These will break over time as people add and remove required parameters. Also, if we rename our `target_tasks_methods` we'll see breakage.

We have a [`params_pre_buildnum`](https://hg.mozilla.org/build/braindump/file/tip/taskcluster/taskgraph-diff/params-pre-buildnum) directory we can use if we're generating task graphs from a pre-[bug 1415391](https://bugzilla.mozilla.org/show_bug.cgi?id=1415391) revision.

## Triggering graphs on separate revisions

Sometimes we land a graph fix on a separate revision from the builds we promoted.

### Command

```bash
# ship action, after having run both promote and push (RC behavior)
ssh buildbot-master77.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# set the action task id to the taskId of the most recent relpro action, e.g. push
ACTION_TASK_ID=Xiz4JZ20SwijU7bXrbVOaw
ACTION_FLAVOR=ship_firefox
# use the decision task id *of the revision you want to use to push and ship with*
DECISION_TASK_ID=VXZvAlW5TMy078ekVwpl_A
# populate the PREVIOUS_GRAPH_IDS:
# 1) if the DECISION_TASK_ID is *not* the same as the builds' decision taskId, add that
# 2) if we ran other actions before ACTION_TASK_ID, add those, in chronological order
# so PREVIOUS_GRAPH_IDS could look like "BUILD_DECISION_TASK_ID,PROMOTE_ACTION_TASK_ID"
PREVIOUS_GRAPH_IDS="..."
python tools/buildfarm/release/trigger_action.py --action-task-id $ACTION_TASK_ID --decision-task-id $DECISION_TASK_ID --previous-graph-ids $PREVIOUS_GRAPH_IDS --release-runner-config /builds/releaserunner3/release-runner.yml --action-flavor $ACTION_FLAVOR
```

### Concept

We need to use a `--decision-task-id` of the new revision, but we need to include the decision task id of the old revision in `--previous-graph-ids`. Ideally, the order will be

`NEW_REV_DECISION, ORIG_REV_DECISION, PROMOTE, PUSH` if applicable.

We use `--decision-task-id` as the source of truth for `actions.json`, `label-to-taskid.json`, and `parameters.yml`. However, we use `previous_graph_ids` to determine where to take taskIds from for previous graphs (the rightmost takes precedence). So if I want to find the linux64 build taskId, I'd look for it in the `push` graph, fail over to the `promote` graph, then find it in the `ORIG_REV_DECISION` graph.

`trigger_action.py` will prepend the `--decision-task-id` to the beginning of `previous_graph_ids` and append the `--action-task-id` to the end of `previous_graph_ids`. This is what we want; we only have to pass `--previous-graph-ids "ORIG_REV_DECISION,PROMOTE"` for a `ship` action.

---
## debug release promotion action

We can use `./mach taskgraph test-action-callback` to debug.

I used

```
./mach taskgraph test-action-callback --task-group-id LR-xH1ViTTi2jrI-N1Mf2A --input /src/gecko/params/promote_fennec.yml -p /src/gecko/params/maple-promote-fennec.yml release_promotion_action > ../promote.json
```

`promote_fennec.yml`:

(This is also the input I use in the action in treeherder)

```yaml
build_number: 1
release_promotion_flavor: promote_fennec
```

For the parameters file, use the appropriate one from [braindump](https://hg.mozilla.org/build/braindump/file/tip/taskcluster/taskgraph-diff/params).

I'm not 100% sure if it's important to use a promotion parameters file or an on-push one.

---
# hg / git - how Aki's muddling through

I'm open to how we do this; I'm absolutely certain my method is not an ideal one.

I like hg bookmarks for smaller projects, but for big ones like this one, I prefer git's rebase behavior to keep my patch queue sane. However, I haven't solved the push-to-hg part yet, so I'm working on maple, landing when I have a probably-good patch, debugging, and then rebasing my work on github.

## Github
- fork [gecko-dev](https://github.com/mozilla/gecko-dev/)
- pull in [gecko-projects](https://github.com/mozilla/gecko-projects/) to your fork, by cloning, adding a remote, and fetching
- after an m-c to maple merge, I pull gecko-dev's `master` branch and gecko-project's `maple` branch. Then I update to my `maple-staging` branch, and `git rebase -i master` and deal with any conflicts.
- then I diff against `maple`. Sometimes it's easiest to export the revs from hg and `patch -p1 < patchfile` and `git commit`, then `git rebase -i master` to clean up the patches.

I haven't tried cinnabar; it's based off a different set of changesets and doesn't follow maple. However, it would allow for pushing to hg.

### git rebase

## Hg

Bookmarks are good for a single branch. I tend to clump all my unlanded patches into a single bookmark, `hg histedit` to edit the patches, and `hg rebase -b BOOKMARK -d maple` to rebase my bookmark against maple. Once the patches look good, I land and move over to git for my patch queue.

### hg histedit + rebase
