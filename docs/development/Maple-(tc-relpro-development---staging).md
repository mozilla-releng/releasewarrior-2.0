Currently, maple is our taskcluster beta relpro migration area, and birch is our taskcluster RC relpro staging area.

---
# Current status

## Trello

The [Trello board](https://trello.com/b/EGWsGSXT/tc-migration-release-h1-2018) has the latest human tasks. As of Feb 8, we're working on removing buildbot and buildbot-bridge from releases.

Please feel free to add tasks there if we're missing any!

---

## Dep vs release

Right now, we're set up with release signing, until we remove that as a staging release requirement.

---

# how-to
## Trigger relpro: promote

Launch a new promotion graph using [ship-it dev](https://ship-it-dev.allizom.org/).

1. Click "Ship a new release"
1. Fennec, Devedition, or Firefox
1. The version will be displayed [here](https://hg.mozilla.org/projects/maple/file/tip/browser/config/version_display.txt) -- `59.0b6` as of this writing.
1. The branch is `projects/maple`
1. Choose partials. It's probably easiest to copy prior art here; Aki is unfamiliar with what staging voodoo we use to choose the proper partials.
1. Enter the maple revision... probably the latest from [here](https://hg.mozilla.org/projects/maple/summary)
1. Click "Gimme a <product>"
1. Click "View releases" -> "Submitted"
1. Click "Ready" and "Do eet"
1. The new relpro action should be on [treeherder](https://treeherder.mozilla.org/#/jobs?repo=maple). The name should be `promote_PRODUCT` or `promote_PRODUCT_rc` based on the version number.
1. the taskId is on the lower left. Clicking on it will bring you to the log
1. pasting the taskid into the url `https://tools.taskcluster.net/groups/TASKID` will bring you to the promotion graph. [These bookmarks](https://github.com/mozilla-releng/releasewarrior-2.0/wiki/ReleaseDuty-Day-1-Checklist-and-FAQ#firefox-bookmarks) will probably help a lot!

## Trigger relpro: push and ship

2018-02-08: The releaseduty push and ship docs may be more up to date at this point.

The `ACTION_FLAVOR` should be one of [these actions](https://hg.mozilla.org/build/tools/file/default/buildfarm/release/trigger_action.py#l20)

For a standard post-promote action (
* generally everything but an RC `ship`,
* the same revision used to build and promote is acceptable to push and ship with), run this:

```bash
# standard action after a promote. This will be a ship-without-a-push or a push.
ssh buildbot-master83.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# set the action task id to the taskId of the promotion relpro action
PROMOTE_TASK_ID=M1QFL1R7RWCTReFLsRWmGw
ACTION_FLAVOR=ship_fennec
python tools/buildfarm/release/trigger_action.py --action-task-id $PROMOTE_TASK_ID --release-runner-config /builds/releaserunner3/release-runner.yml --action-flavor $ACTION_FLAVOR
```

For a standard post-promote action with some push or ship fixes in a newer revision (
* generally every relpro flavor but an RC `ship`,
* the revision wanted to push and ship with has some graph fixes that landed after the build and promote revision), run this:

```bash
# standard action on a newer revision after a promote.
# This will be a ship-without-a-push or a push
ssh buildbot-master83.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# set the action task id to the taskId of the promotion relpro action
PROMOTE_TASK_ID=M1QFL1R7RWCTReFLsRWmGw
# use the decision task id *of the revision you want to use to push and ship with*
DECISION_TASK_ID=Ov8k7qUoQG2PHCK5sRfzHw
ACTION_FLAVOR=ship_fennec
python tools/buildfarm/release/trigger_action.py --action-task-id $PROMOTE_TASK_ID --decision-task-id $DECISION_TASK_ID --release-runner-config /builds/releaserunner3/release-runner.yml --action-flavor $ACTION_FLAVOR
```

During RCs, we run `promote`, then `push`. To run `ship`, do the following:

```bash
# ship action, after having run both promote and push (RC behavior)
ssh buildbot-master83.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# set the action task id to the taskId of the push relpro action
PUSH_TASK_ID=Xiz4JZ20SwijU7bXrbVOaw
ACTION_FLAVOR=ship_firefox
PROMOTE_TASK_ID=Iym4bESbSqyrA8M2TsxAiw
# use the decision task id *of the revision you want to use to push and ship with*
DECISION_TASK_ID=VXZvAlW5TMy078ekVwpl_A
python tools/buildfarm/release/trigger_action.py --action-task-id $PUSH_TASK_ID --decision-task-id $DECISION_TASK_ID --previous-graph-ids $PROMOTE_TASK_ID --release-runner-config /builds/releaserunner3/release-runner.yml --action-flavor $ACTION_FLAVOR
```

The action should show up on treeherder; its taskId is the graph's group id as above.

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
