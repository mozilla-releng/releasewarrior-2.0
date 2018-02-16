
## Background

For Fennec RCs, we roll out to Google Play at 5% until we know if it's a good RC (via the `ship_fennec_rc` relpro flavor).

At that point, we run the `ship_fennec` graph to mark it as shipped.

## Prerequisites

- VPN Access
- SSH Access to buildbot-master85
- (Optional, convenient) [taskcluster-cli](https://github.com/taskcluster/taskcluster-cli) set up

## When to perform these steps

The release-signoff mailing list will receive a message alerting us that testing of Fennec has been completed.
If the testing is successful, they will ask us to push the result to the Google Play store.

Below is an example email. The key text to look for will be `Testing status:GREEN / DONE` or something similar.

```
Subject: [mobile] Firefox 60 RC 5 build 2 - Sign Off of Manual Functional Testing - please push to google play

Hi all,

Here are the results for the Fennec 60 RC 5 build 2.

Testing status:GREEN / DONE
*1. Overall build status after testing:* GREEN/OK - No blockers or major
bugs found

*2. Recommendation from QE*:  ship to partner's markets
*3. Manual Testing Summary :*
*4. New bugs:
*5. Known Issues:*
```

## ship-rc

* [Find the graphids](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/misc/find-graphids.md#finding-graphids) for this release.

### Creating the RC ship graph

1. We will create a new task with the label 'Action: Release Promotion' in the existing on-push graph.
1. This action will create a new ship-rc graph

```sh
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from above, you should have found a
# promote taskid
#   export PROMOTE_TASK_ID=...
python tools/buildfarm/release/trigger_action.py \
    ${PROMOTE_TASK_ID+--action-task-id ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ship_fennec_rc
# Unset PROMOTE_TASK_ID to minimize the possibility of rerunning with different graph ids
unset PROMOTE_TASK_ID
```

This will show you a task definition and ask if you want to submit it (y/n). If you're ready to ship, choose `y`. The ship action taskId will be near the bottom of the output; this taskId is also used as the task graph ID for the ship graph.

For example, the last output from `trigger_action.py` will look something like this:
```O - Result:
{u'status': {u'workerType': u'gecko-3-decision', u'taskGroupId': u'bjVsVQdfSQWjdq9NTBYySA', u'runs': [{u'scheduled': u'2017-11-21T15:40:38.710Z', u'reasonCreated': u'scheduled', u'state': u'pending', u'runId': 0}], u'expires': u'2018-11-21T15:40:09.109Z', u'retriesLeft': 5, u'state': u'pending', u'schedulerId': u'gecko-level-3', u'deadline': u'2017-11-22T15:40:08.109Z', u'taskId': u'OG1t0QchSj209mV9_3tCHA', u'provisionerId': u'aws-provisioner-v1'}}
```

We see `u'taskId': u'OG1t0QchSj209mV9_3tCHA'` and know that there should be a task graph with that ID, too.

```sh
taskcluster group list OG1t0QchSj209mV9_3tCHA --all
```

You can also see the new 'Action: Release Promotion' task on [tools.taskcluster.net](https://tools.taskcluster.net/groups)

### Resolve push-apk-breakpoint task

In the new ship-rc graph, there will be a task with 'push-apk-breakpoint' in the label. To push the `apk` to Google Play, we must resolve this task.

1. Find the Task ID of the `push-apk-breakpoint` task using either [tools.taskcluster.net](https://tools.taskcluster.net/groups) or the taskcluster command-line:
```sh
taskcluster group list "${TASKGROUPID}" --all
```
1. Complete the push-apk task
```sh
taskcluster task complete <TASKID>
```
1. The rest of the ship graph should now run, and eventually complete. One of the tasks is a notification, so no email is required to be manually sent.

## ship

### Finding the Action Task IDs

* [Find the promote and ship-rc graphids](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/misc/find-graphids.md#finding-graphids) for this release.

### Creating the ship graph

1. We will create a new task with the label 'Action: Release Promotion' in the existing on-push graph.
1. This action will create a new ship graph

```sh
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from above, you should have found a
# promote taskid
#   export PROMOTE_TASK_ID=...
#   export RC_TASK_ID=...
python tools/buildfarm/release/trigger_action.py \
    ${RC_TASK_ID+--action-task-id ${RC_TASK_ID}} \
    ${PROMOTE_TASK_ID+--previous-graph-ids ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ship_fennec_rc
# Unset PROMOTE_TASK_ID and RC_TASK_ID to minimize the possibility of rerunning with different graph ids
unset PROMOTE_TASK_ID
unset RC_TASK_ID
```

This will show you a task definition and ask if you want to submit it (y/n). If you're ready to ship, choose `y`. The ship action taskId will be near the bottom of the output; this taskId is also used as the task graph ID for the ship graph.

For example, the last output from `trigger_action.py` will look something like this:
```O - Result:
{u'status': {u'workerType': u'gecko-3-decision', u'taskGroupId': u'bjVsVQdfSQWjdq9NTBYySA', u'runs': [{u'scheduled': u'2017-11-21T15:40:38.710Z', u'reasonCreated': u'scheduled', u'state': u'pending', u'runId': 0}], u'expires': u'2018-11-21T15:40:09.109Z', u'retriesLeft': 5, u'state': u'pending', u'schedulerId': u'gecko-level-3', u'deadline': u'2017-11-22T15:40:08.109Z', u'taskId': u'OG1t0QchSj209mV9_3tCHA', u'provisionerId': u'aws-provisioner-v1'}}
```

We see `u'taskId': u'OG1t0QchSj209mV9_3tCHA'` and know that there should be a task graph with that ID, too.

```sh
taskcluster group list OG1t0QchSj209mV9_3tCHA --all
```

You can also see the new 'Action: Release Promotion' task on [tools.taskcluster.net](https://tools.taskcluster.net/groups)

## Update Releasewarrior

1. Run `release status` to find the incomplete human tasks.
```sh
INFO: RELEASE IN FLIGHT: fennec 60.0 build2 2017-11-20
INFO: Graph 1: https://tools.taskcluster.net/task-group-inspector/#/NnPn1IvtQqq9ur84LyqhWg
INFO: 	Incomplete human tasks:
INFO: 		* ID 3 (alias: pushapk) - run pushapk
INFO: 		* ID 4 (alias: publish) - published release tasks
INFO: 	Unresolved issues:
```
1. Use the `release graphid` command to add the new graph id.
1. Resolve the tasks you have performed, using the ID
```sh
$ release task fennec 60.0 --resolve 3
INFO: ensuring releasewarrior repo is up to date and in sync with origin
INFO: generating wiki from template and config
INFO: writing to data file: /Users/sfraser/github/mozilla-releng/releasewarrior-data/inflight/fennec/fennec-release-rc-60.0.json
INFO: writing to wiki file: /Users/sfraser/github/mozilla-releng/releasewarrior-data/inflight/fennec/fennec-release-rc-60.0.md
INFO: writing to corsica file: /Users/sfraser/github/mozilla-releng/releasewarrior-data/index.html
INFO: committing changes with message: fennec 60.0 - updated inflight tasks. Resolved ('3',)
```

Remember to run `git push` in the `releasewarrior-data` repository, if needed.
