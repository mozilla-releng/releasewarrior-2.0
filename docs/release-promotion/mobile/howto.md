
## Background

QA will test a potential Fennec release and let us know the results. If the tests all pass, we will have to push the `apk` to Google Play.

To do this we create a new task graph to perform all the release promotion steps.

## Prerequisites

- VPN Access
- SSH Access to `buildbot-master01.bb.releng.use1.mozilla.com`
- (Optional, convenient) [taskcluster-cli](https://github.com/taskcluster/taskcluster-cli) set up

## When to perform these steps

The release-signoff mailing list will receive a message alerting us that testing of Fennec has been completed.
If the testing is successful, they will ask us to push the result to the Google Play store.

Below is an example email. The key text to look for will be `Testing status:GREEN / DONE` or something similar.

```
Subject: [mobile] Firefox 58 Beta 5 build 2 - Sign Off of Manual Functional Testing - please push to google play

Hi all,

Here are the results for the Fennec 58 Beta 5 build 2.

Testing status:GREEN / DONE
*1. Overall build status after testing:* GREEN/OK - No blockers or major
bugs found

*2. Recommendation from QE*:  ship to partner's markets
*3. Manual Testing Summary :*
*4. New bugs:
*5. Known Issues:*
```

## Ship

### Finding the Action Task ID

* [Find the promote graphid](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/common/find-graphids.md#finding-graphids) for this release.

### Creating the ship graph

1. We will create a new task with the label 'Action: Release Promotion' in the existing on-push graph.
1. This action will create a new ship graph

```bash
ssh buildbot-master01.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from above, you should have found a
# decision taskid, and a promote taskid, and a push taskid.
#   export PROMOTE_TASK_ID=...
ACTION_FLAVOR=ship_fennec
python tools/buildfarm/release/trigger_action.py \
    ${PROMOTE_TASK_ID+--action-task-id ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ${ACTION_FLAVOR}
# Unset PROMOTE_TASK_ID to minimize the possibility of rerunning with different graph ids
unset PROMOTE_TASK_ID
```

  * The `taskId` of the action task will be the `taskGroupId` of the next graph.

* Announce to release-signoff that the release is live
* Update releasewarrior:
    ```sh
    release graphid --phase ship ${taskId} ${product} ${version}
    release task ${product} ${version} --resolve pushapk
    cd ../releasewarrior-data && git push
    ```
