# Add a What's New Page to a Firefox RC

## When

What's New Page setup should be done shortly after updates are available on the release-localtest channel.

## Requirements

* Access to production Balrog
* A confirmed list of locales that should receive the WNP from Product
* A confirmed URL of the WNP from Product

## wnp
### How

* Download the existing Release Blob (e.g. `Firefox-59.0-build1`)
  * Go to https://aus4-admin.mozilla.org/releases
  * Search for the release blob you need
  * Click `Download`
  * Copy it to a -No-WNP version (you'll need this later). Eg: Firefox-59.0-build1-No-WNP.json.
* Make the following changes to the -No-WNP version:
  * Append "-No-WNP" to the `name` field.
* Make the following changes to the original file:
  * Change `schema_version` to `9`
  * Remove `detailsUrl` from the top level of the blob
  * Remove `platformVersion` from the top level of the blob, and every locale section
    * Be careful to not leaving trailing commas - this is not valid JSON!
      * Tip: You can use `:g/platformVersion/d` in [Vi](https://www.vim.org/) to trim all lines containing this string
      * Tip: Removing the `platformVersion` above leaves the json with trailing commas in too many places to be fixed manually. To automate this fix, load the entire json as a dictionary in Python and dump it as JSON afterwards
```py
# e.g. for Firefox-59.0-build1
data = ... (import dict from the original blob)
import json
with open('Firefox-59.0-build1.json', 'w') as fp:
    data = json.dump(data, fp, sort_keys=True, indent=4)
```

  * This will no longer be necessary once [bug 1431789](https://bugzilla.mozilla.org/show_bug.cgi?id=1431789) is fixed.
  * Add an `updateLine` section that looks something like the following:

```
  "updateLine": [
    {
      "for": {},
      "fields": {
        "detailsURL": "https://www.mozilla.org/%LOCALE%/firefox/59.0/releasenotes/",
        "type": "minor"
      }
    },
    {
      "for": {
        "channels": ["release", "release-localtest", "release-cdntest"],
        "locales": ["ast", "bg", "en-US", ...],
        "versions": ["<59.0"]
      },
      "fields": {
        "actions": "showURL",
        "openURL": "https://www.mozilla.org/%LOCALE%/firefox/59.0/whatsnew/?oldversion=%OLD_VERSION%"
      }
    }
  ]
```

The block above says that all responses constructed with this blob should include `detailsURL` and `type` (because the first `for` block is empty), while only requests matching `locales` and `versions` from the second `for` block should get `actions` and `openURL` in their response.
The list of locales and WNP URL should be whatever you received from Product before you began this process.

**A word on the** `locales` The final number of locales that are to be present within a certain WNP depends on each release. There's a certain cut-off date for each release, by which localized contents can be submitted. Once passed the cut-off date
the list of locales that have that content, are written in stone for that particular release; all others are being ignored in serving the WNP. Hence, the number of locales available changes per release, as the page changes. More context of this [here](https://bugzilla.mozilla.org/show_bug.cgi?id=1438633#c17).

Now that you have the new Release blobs in hand you can upload them to Balrog and update the Rules by doing the following:
* Add the -No-WNP Release to Balrog:
  * Go to https://aus4-admin.mozilla.org/releases
  * Click "Add a new Release"
  * Fill out the form, selecting the "-No-WNP" blob that you created, and click `Save Changes`
* Add the WNP Release to Balrog
  * Go to https://aus4-admin.mozilla.org/releases
  * Search for the Release blob again
  * Click `Update`
  * Fill out the form, selecting your new, locally modified blob, and click `Save Changes`

If there is no `Update` button present, this means the Release is already on a live channel, and you cannot modify it without Signoff. You can either Schedule an Update or upload it under a different name in this situation, but both of these are out of scope of this howto.

Once this is done the What's New Page should be active on both the release-localtest and release-cdntest channels.

# Remove previous release's What's New Page

## When

Shortly before we ship a major release, we need to remove the What's New Page from the previous release, to avoid users getting an old WNP while the new release is throttled, and then the latest release's WNP a day later.

## Requirements
* Access to production Balrog

## remove-wnp
### How

* Change the Firefox release rule to point at the -No-WNP blob.
  * Go to https://aus4-admin.mozilla.org/rules?product=Firefox&channel=release
  * Find the "firefox-release" Rule.
  * Click `Schedule an Update`
  * Change "Mapping" to the "-No-WNP" variant. Eg: if the Mapping is currently `Firefox-59.0-build5`, change it to `Firefox-59.0-build5-No-WNP`.
  * Click `Schedule Changes`
  * Signoff on the Scheduled Change, and ask RelMan to do the same.

# Ship RC Firefox releases

## Requirements

* taskcluster-cli installed
* releasewarrior-2.0 installed
* ssh access to `buildbot-master85.bb.releng.scl3.mozilla.com`

## Differences between Firefox RC and non-RC

* the `promote` action will be named `promote_firefox_rc` instead of `promote_firefox`
* there will be an action in between `promote` and `push`. This is `ship_firefox_rc`. The relpro flavors, in order, will be:

    1. `promote_firefox_rc`
    1. `ship_firefox_rc`
    1. `push_firefox`
    1. `ship_firefox`

    We may repeat the first two several times if there are issues we don't want to ship the real release with.

## ship-rc

### How

* [Find the promote-rc graphid](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/common/find-graphids.md#finding-graphids) for this release.

* For now, we have to ssh to bm85 to generate the ship-rc graph.

```
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from above, you should have found at least
# a promote taskid.
#   export PROMOTE_TASK_ID=...
ACTION_FLAVOR=ship_firefox_rc
python tools/buildfarm/release/trigger_action.py \
    ${PROMOTE_TASK_ID+--action-task-id ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ${ACTION_FLAVOR}
# Unset env vars to minimize the possibility of rerunning with different graph ids
unset ACTION_FLAVOR
unset PROMOTE_TASK_ID
# This will output the task definition and ask if you want to proceed.
```
  * The `taskId` of the action task will be the `taskGroupId` of the next graph.

* Update releasewarrior:
    ```sh
    release task ${product} ${version} --resolve ship-rc
    cd ../releasewarrior-data && git push
    ```

## push

### How

* [Find the promote-rc graphid](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/common/find-graphids.md#finding-graphids) for this release.  We can skip the ship-rc graphid.

* For now, we have to ssh to bm85 to generate the push graph.

```
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from above, you should have found at least
# a promote taskid.
#   export PROMOTE_TASK_ID=...
ACTION_FLAVOR=push_firefox
python tools/buildfarm/release/trigger_action.py \
    ${PROMOTE_TASK_ID+--action-task-id ${PROMOTE_TASK_ID}} \
    --release-runner-config /builds/releaserunner3/release-runner.yml \
    --action-flavor ${ACTION_FLAVOR}
# Unset env vars to minimize the possibility of rerunning with different graph ids
unset ACTION_FLAVOR
unset PROMOTE_TASK_ID
# This will output the task definition and ask if you want to proceed.
```
  * The `taskId` of the action task will be the `taskGroupId` of the next graph.

* Update releasewarrior:
    ```sh
    release task ${product} ${version} --resolve publish
    cd ../releasewarrior-data && git push
    ```

## ship

### Background

The `ship` phase should be triggered when the release is signed off. It runs the `update bouncer aliases`, `mark as shipped`, and `bump version` tasks.

### When

An email will arrive to the release-signoff mailing list asking for a release to be pushed to the appropriate channel, such as 'release' for major releases, 'beta' for betas, and so on.

Examples
- `[desktop] Please push Firefox 57.0 (build#4) to the release channel (25%)`

### How

* [Find the promote-rc and push graphids](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/release-promotion/common/find-graphids.md#finding-graphids) for this release.

* Then:

```bash
# ship action, after having run both promote and push (RC behavior)
ssh buildbot-master85.bb.releng.scl3.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# paste the export line from above, you should have found a
# decision taskid, and a promote taskid, and a push taskid.
#   export DECISION_TASK_ID=...
#   export PROMOTE_TASK_ID=...
#   export PUSH_TASK_ID=...
ACTION_FLAVOR=ship_firefox  # or ship_devedition
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
# This will output the task definition and ask if you want to proceed.
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
