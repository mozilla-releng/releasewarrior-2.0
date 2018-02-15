## Requirements

* taskcluster-cli installed
* releasewarrior-2.0 installed
* ssh access to `buildbot-master85.bb.releng.scl3.mozilla.com`

## Push artifacts to releases directory

### Context - Beta and DevEdition
In the beta cycle, `Firefox` and `Devedition` are different products built based on the same in-tree revision. Their functionality is the same but branding options differ.
For version `X`, the following happens in a cycle:
- We only ship Devedition `X.b1` and `X.b2` for the beta cycle. For the final push to the `aurora` channel, we wait for *Relman* consent.
- Starting with b3 we ship `Firefox` along with `Devedition`. For the final push to `beta` and `aurora` respectively, we wait for *QA* consent and we're pushing them together as soon as the QA signs-off for `Firefox`.
- **Disclaimer!** Once every two weeks, QA signs-off for Devedition *after* we ship the release. As counter-clockwise as it may sound, this makes sense given the two products actually share the in-tree revision, hence the functionalities.

### Background

`releases`, `mirrors` and `CDN` are different terms for the same concept - the CDN from which shipped releases are served.

In the new taskcluster release promotion for Fx59+, pushing doesn't happen automatically in ship-it (yet). We can [address this](https://trello.com/c/vOP7fml4/282-update-releaserunner3-to-automatically-run-the-push-flavor-rather-than-promote-for-certain-release-types). Until then, all pushing will be manually triggered.

### When - b2+ betas

- For beta we want to push to releases directories as soon as the builds are ready. Releng can trigger the `push` action as soon as the `promote` action task finishes (you do not need to wait for all of the tasks in the promote phase to complete). In the future we can have this [happen automatically](https://trello.com/c/vOP7fml4/282-update-releaserunner3-to-automatically-run-the-push-flavor-rather-than-promote-for-certain-release-types). (We are also in [discussion with relman](https://bugzilla.mozilla.org/show_bug.cgi?id=1433284) about future plans around this step)

### When - releases

* Release Management will send an email to the release-signoff mailing list, with a subject line of the form: `[desktop] Please push ${version} to ${channel}`

Examples:
- `[desktop] Please push Firefox 57.0.1 (build#2) to the release-cdntest channel`
- `[desktop] Please push Firefox 52.4.1esr to the esr-cdntest channel`

This subject is free-text and may not always be the same format, but will have the same information in. You shouldn't expect to see these emails for `devedition` or `beta` as they update the releases directory automatically.

Note: If they do not explicitly ask for `release-cdntest` it is okay to assume it is included. Please mention its inclusion in the reply, and ask for explicit channel names next time.

* The build should all be green - watch for failures in the update verify tests, especially.

### How

* [Find the promote graphid](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/misc/find-graphids.md#finding-graphids) for this release.

* For now, we have to ssh to bm85 to generate the push graph.

```
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from get_graphids.py, you should have
# found at least a promote taskid.
#   export PROMOTE_TASK_ID=...
ACTION_FLAVOR=push_firefox  # For devedition, use push_devedition
# This will output the task definition and ask if you want to proceed.
python tools/buildfarm/release/trigger_action.py \
    ${PROMOTE_TASK_ID+--action-task-id ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ${ACTION_FLAVOR}
# Unset env vars to minimize the possibility of rerunning with different graph ids
unset ACTION_FLAVOR
unset PROMOTE_TASK_ID
```
  * The `taskId` of the action task will be the `taskGroupId` of the next graph.

* Update releasewarrior:
    ```sh
    release task ${product} ${version} --resolve publish
    cd ../releasewarrior-data && git push
    ```

## Ship the release

### Background

The `ship` phase should be triggered when the release is signed off. It runs the `update bouncer aliases`, `mark as shipped`, and `bump version` tasks.

### When

An email will arrive to the release-signoff mailing list asking for a release to be pushed to the appropriate channel, such as 'release' for major releases, 'beta' for betas, and so on.

Examples
- `[desktop] Please push Firefox 58.0b5 to beta and DevEdition to aurora`
- `[desktop] Please push Firefox 57.0 (build#4) to the release channel (25%)`

### How

* [Find the promote and push graphids](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/misc/find-graphids.md#finding-graphids) for this release.

* Then:

```bash
# ship action, after having run both promote and push (RC behavior)
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from get_graphids.py, you should have
# found a decision taskid, and a promote taskid, and a push taskid.
#   export DECISION_TASK_ID=...
#   export PROMOTE_TASK_ID=...
#   export PUSH_TASK_ID=...
ACTION_FLAVOR=ship_firefox  # or ship_devedition
# This will output the task definition and ask if you want to proceed.
python tools/buildfarm/release/trigger_action.py \
    ${PUSH_TASK_ID+--action-task-id ${PUSH_TASK_ID}} \
    ${DECISION_TASK_ID+--decision-task-id ${DECISION_TASK_ID}} \
    ${PROMOTE_TASK_ID+--previous-graph-ids ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ${ACTION_FLAVOR}
# Unset env vars to minimize the possibility of rerunning with different graph ids
unset ACTION_FLAVOR
unset DECISION_TASK_ID
unset PROMOTE_TASK_ID
unset PUSH_TASK_ID
```
  * The `taskId` of the action task will be the `taskGroupId` of the next graph.

* Announce to release-signoff that the release is live
* Update releasewarrior:
    ```sh
    release task ${product} ${version} --resolve publish
    cd ../releasewarrior-data && git push
    ```

## Obtain sign-offs for changes

### Background

To guard against bad actors and compromised credentials we require that any changes to primary release channels (beta, release, ESR) in Balrog are signed off by at least two people.

### When

After the scheduled change has been created by the "updates" task, and prior to the desired release publish time

### How

* In context of the other rules, eg
    * Firefox release: <https://aus4-admin.mozilla.org/rules?product=Firefox&channel=release>
    * Firefox beta: <https://aus4-admin.mozilla.org/rules?product=Firefox&channel=beta>
    * DevEdition: <https://aus4-admin.mozilla.org/rules?product=Firefox&channel=aurora>
* Or using the Balrog Scheduled Changes UI: <https://aus4-admin.mozilla.org/rules/scheduled_changes>

Update releasewarrior:
```sh
release task ${product} ${version} --resolve signoff
cd ../releasewarrior-data && git push
```

Further details and examples can be found on the [[Balrog page|Balrog and Scheduled Changes]]

If this is a Release (not a beta, devedition or RC), then schedule an update in Balrog to change the background rate of the rule to 0% the next day.
* Go to Balrog and "Schedule an Update" for the "Firefox: release" rule that changes "backgroundRate" to 0 at 9am Pacific the following day. All other fields should remain the same.
