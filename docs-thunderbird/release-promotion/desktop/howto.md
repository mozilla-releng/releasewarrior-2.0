## Requirements

* taskcluster-cli installed
* releasewarrior-2.0 installed
* ssh access to `buildbot-master01.bb.releng.use1.mozilla.com`

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

### When - b1 betas/devedition

- For b1, we do not push to the releases directory until after some QA has happened. No formal e-mail is sent for this - so check with RelMan for specific timing.

### When - b2+ betas/devedition

- For beta we want to push to releases directories as soon as the builds are ready. You can tell the builds are ready because one of the final steps is sending an email from Taskcluster, with a subject line similar to `firefox 60.0b10 build1/mozilla-beta is in the candidates directory`
- Releng can trigger the `push` action as soon as the `promote` action task finishes (you do not need to wait for all of the tasks in the promote phase to complete). In the future we can have this [happen automatically](https://trello.com/c/vOP7fml4/282-update-releaserunner3-to-automatically-run-the-push-flavor-rather-than-promote-for-certain-release-types). (We are also in [discussion with relman](https://bugzilla.mozilla.org/show_bug.cgi?id=1433284) about future plans around this step)

### When - releases

* Release Management will send an email to the release-signoff mailing list, with a subject line of the form: `[desktop] Please push ${version} to ${channel}`

Examples:
- `[desktop] Please push Firefox 57.0.1 (build#2) to the release-cdntest channel`
- `[desktop] Please push Firefox 52.4.1esr to the esr-cdntest channel`

This subject is free-text and may not always be the same format, but will have the same information in. You shouldn't expect to see these emails for `devedition` or `beta` as they update the releases directory automatically.

Note: If they do not explicitly ask for `release-cdntest` it is okay to assume it is included. Please mention its inclusion in the reply, and ask for explicit channel names next time.

* The build should all be green - watch for failures in the update verify tests, especially.

### When - thunderbird

* Thunderbird Release Management will send an email to the thunderbird-drivers mailing list, with a subject line of the form: `${version} - releng, please push to ${channel}`

### How

* [Find the promote graphid](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/common/find-graphids.md#finding-graphids) for this release.

* For now, we have to ssh to bm85 to generate the push graph.

```
ssh buildbot-master01.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export lines from rw status, you should have
# found at least a promote taskid.
#   export PROMOTE_TASK_ID=...
ACTION_FLAVOR=push_firefox  # or ACTION_FLAVOR=push_devedition or ACTION_FLAVOR=push_thunderbird
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
    release graphid --phase push ${taskId} ${product} ${version}
    release task ${product} ${version} --resolve mirrors
    cd ../releasewarrior-data && git push
    ```

## Ship the release

### Background

The `ship` phase should be triggered when the release is signed off. It runs the `update bouncer aliases`, `mark as shipped`, and `bump version` tasks.

### When

An email will arrive to the release-signoff mailing list asking for a release to be pushed to the appropriate channel, such as 'release' for major releases, 'beta' for betas, and so on. (For thunderbird, the mail will be to the thunderbird-drivers list).

Examples
- `[desktop] Please push Firefox 58.0b5 to beta and DevEdition to aurora`
- `[desktop] Please push Firefox 57.0 (build#4) to the release channel (25%)`
-  (thunderbird) `${version} releng, please make live on beta channel`
- `[desktop] Please push Firefox 52.9.0esr-build2 and 60.1.0esr-build2 to the esr channel`

### How

* [Find the promote and push graphids](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/common/find-graphids.md#finding-graphids) for this release.

* Then:

```bash
# ship action, after having run both promote and push (RC behavior)
ssh buildbot-master01.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export lines from rw status, you should have
# found a decision taskid, and a promote taskid, and a push taskid.
#   export DECISION_TASK_ID=...
#   export PROMOTE_TASK_ID=...
#   export PUSH_TASK_ID=...
ACTION_FLAVOR=ship_firefox  # or ACTION_FLAVOR=ship_devedition or ACTION_FLAVOR=ship_thunderbird
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
    release graphid --phase ship ${taskId} ${product} ${version}
    release task ${product} ${version} --resolve ship
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
    * Thunderbird beta: <https://aus4-admin.mozilla.org/rules?product=Thunderbird&channel=beta>
* Or using the Balrog Scheduled Changes UI: <https://aus4-admin.mozilla.org/rules/scheduled_changes>

Update releasewarrior:
```sh
release task ${product} ${version} --resolve signoff
cd ../releasewarrior-data && git push
```

Further details and examples can be found on the [[Balrog page|Balrog and Scheduled Changes]]

If this is a Release (not a beta, devedition or RC), then schedule an update in Balrog to change the background rate of the rule to 0% the next day.
* Go to Balrog and "Schedule an Update" for the "Firefox: release" rule that changes "backgroundRate" to 0 at 9am Pacific the following day. All other fields should remain the same.

## Bump the Election Edition bouncer entries

### Background

The Firefox Election Edition is a long-lived repack of Firefox associated with the 2018 US
 mid-term elections, with a special download page on
 [www.mozilla.org](https://www.mozilla.org/en-US/firefox/election/).
We need to manually update the bouncer locations when we ship a new build on the
release channel, so that the repack stays in sync with the vanilla Firefox.

[Bug 1497097](https://bugzilla.mozilla.org/show_bug.cgi?id=1497097) is to automate this
process (in general).

### When
This is done as part of the ship phase, ideally after the `release-bouncer-aliases-firefox
` task completes. This is for all releases on the release channel (but not beta or ESR).

### How
[Log in to bouncer](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/misc-operations/accessing-bouncer.md)
and update the three locations for the
[firefox-election-edition](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=9829) product.

In each location, update two version values, and adjust the buildN to shipping build.
For now it's normal to  serve these from the candidates directory.

For example, Mac changes from

`/firefox/candidates/63.0-candidates/build2/partner-repacks/firefox/firefox-election-edition/v1/mac/en-US/Firefox%2063.0.dmg`

to

`/firefox/candidates/63.0.1-candidates/build4/partner-repacks/firefox/firefox-election-edition/v1/mac/en-US/Firefox%2063.0.1.dmg`

Verify the links work by running this in a terminal:
```
$ for os in osx win win64; do
    echo "-------- OS: ${os} --------";
    curl -sIL "https://download.mozilla.org/?product=firefox-election-edition&os=${os}&lang=en-US" |grep -E '^HTTP|^Location';
done
```
The output should look similar to
```
OS: osx
HTTP/1.1 302 Found
Location: https://download-installer.cdn.mozilla.net/pub/firefox/candidates/63.0.1-candidates/build4/partner-repacks/firefox/firefox-election-edition/v1/mac/en-US/Firefox%2063.0.1.dmg
HTTP/2 200
----------------
OS: win
HTTP/1.1 302 Found
Location: https://download-installer.cdn.mozilla.net/pub/firefox/candidates/63.0.1-candidates/build4/partner-repacks/firefox/firefox-election-edition/v1/win32/en-US/Firefox%20Setup%2063.0.1.exe
HTTP/2 200
----------------
OS: win64
HTTP/1.1 302 Found
Location: https://download-installer.cdn.mozilla.net/pub/firefox/candidates/63.0.1-candidates/build4/partner-repacks/firefox/firefox-election-edition/v1/win64/en-US/Firefox%20Setup%2063.0.1.exe
HTTP/2 200
----------------
```

Bouncer should return a 302 to the actual file location, which should be a 200 rather than 404.
