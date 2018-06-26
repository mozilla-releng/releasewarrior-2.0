## Requirements

* taskcluster-cli installed
* releasewarrior-2.0 installed

## Push artifacts to releases directory

### Background

`releases`, `mirrors` and `CDN` are different terms for the same concept - the CDN from which published releases are served.

### When

* Release Management will send an email to the release-signoff mailing list, with a subject line of the form: `[desktop] Please push ${version} to ${channel}`

Examples:
- `[desktop] Please push Firefox 57.0.1 (build#2) to the release-cdntest channel`
- `[desktop] Please push Firefox 52.4.1esr to the esr-cdntest channel`

This subject is free-text and may not always be the same format, but will have the same information in. You shouldn't expect to see these emails for `devedition` or `beta` as they update the releases directory automatically.

Note: If they do not explicitly ask for `release-cdntest` it is okay to assume it is included. Please mention its inclusion in the reply, and ask for explicit channel names next time.

* The build should all be green - watch for failures in the update verify tests, especially.

### How - Plan A

* Check the `release` command for the link to the task graph.
* There should be a pending task with "push to releases human decision task" in the name
* Find the TaskID for this task, and resolve it:
    ```sh
    taskcluster task complete "${TASKID}"
    ```
* Update releasewarrior:
    ```sh
    release task ${product} ${version} --resolve mirrors
    cd ../releasewarrior-data && git push
    ```
If there is no "push to releases task" pending, check for it failing. These tasks have a deadline of **4 days** and so can expire if testing takes longer than that. If it has expired, we must start a new task graph to do these steps. Follow Plan B.

### How - Plan B

To create the second graph:

1. Get a TaskID from any task in graph 1. Yes, any task. This will be used by graph 2 for obtaining the release version, branch, etc.
2. Call releasetasks_graph_gen.py:
```bash
ssh `whoami`@buildbot-master85.bb.releng.scl3.mozilla.com  # host we release-runner and you generate/submit new release promotion graphs
sudo su - cltbld
TASK_TASKID_FROM_GRAPH1={insert a taskid from any task in graph 1}
BRANCH_CONFIG=prod_mozilla-esr52_firefox_rc_graph_2.yml

cd /home/cltbld/releasetasks/
git pull origin master  # make sure we are up to date. note: make sure this is on master and clean first
cd /builds/releaserunner/tools/buildfarm/release/
hg pull -u # make sure we are up to date. note: make sure this is on default and clean first
source /builds/releaserunner/bin/activate

# call releasetasks_graph_gen.py with --dry-run and sanity check the graph output that would be submitted
python releasetasks_graph_gen.py --release-runner-config=../../../release-runner.yml --branch-and-product-config="/home/cltbld/releasetasks/releasetasks/release_configs/${BRANCH_CONFIG}" --common-task-id=$TASK_TASKID_FROM_GRAPH1 --dry-run

# call releasetasks_graph_gen.py for reals which will submit the graph to Taskcluster
python releasetasks_graph_gen.py --release-runner-config=../../../release-runner.yml --branch-and-product-config="/home/cltbld/releasetasks/releasetasks/release_configs/${BRANCH_CONFIG}" --common-task-id=$TASK_TASKID_FROM_GRAPH1
```
* Update releasewarrior as shown in Plan A

## Publish the release

### Background

The `publish release human decision task` should be triggered after the release has been published in Balrog. It triggers the `update bouncer aliases`, `mark as shipped`, and `bump version` tasks.

### When

An email will arrive to the release-signoff mailing list asking for a release to be pushed to the appropriate channel, such as 'release' for major releases, 'beta' for betas, and so on.

Examples
- `[desktop] Please push Firefox 58.0b5 to beta and DevEdition to aurora`
- `[desktop] Please push Firefox 57.0 (build#4) to the release channel (25%)`

### How

* If Plan A happened for pushing to mirrors and graph expired, you'll need to create it according sans the pushing-to-mirrors (which at this point already happened).

```bash
ssh `whoami`@buildbot-master85.bb.releng.scl3.mozilla.com  # host we release-runner and you generate/submit new release promotion graphs
sudo su - cltbld
TASK_TASKID_FROM_GRAPH1={insert a taskid from any task in graph 1}
BRANCH_CONFIG=prod_mozilla-esr52_firefox_rc_graph_2.yml

cd /home/cltbld/releasetasks/
git pull origin master  # make sure we are up to date. note: make sure this is on master and clean first
vi releasetasks/release_configs/prod_mozilla-esr52_firefox_rc_graph_2.yml # remove push-to-mirrors task from second graph
git diff # you should have something similar to this
+++ b/releasetasks/release_configs/prod_mozilla-esr52_firefox_rc_graph_2.yml
@@ -29,7 +29,7 @@ updates_enabled: false
 checksums_enabled: false
 push_to_candidates_enabled: false
 update_verify_enabled: false
-push_to_releases_enabled: true
+push_to_releases_enabled: false
 channels:
     - "esr"
 publish_to_balrog_channels:
@@ -51,7 +51,7 @@ funsize_balrog_api_root: "http://balrog/api"
 balrog_api_root: "https://aus4-admin.mozilla.org/api"
 build_tools_repo_path: "build/tools"
 tuxedo_server_url: "https://bounceradmin.mozilla.com/api"
-push_to_releases_automatic: true
+push_to_releases_automatic: false
 beetmover_candidates_bucket: "net-mozaws-prod-delivery-firefox"
 snap_enabled: false
 update_verify_channel: null

cd /builds/releaserunner/tools/buildfarm/release/
hg pull -u # make sure we are up to date. note: make sure this is on default and clean first
source /builds/releaserunner/bin/activate

# call releasetasks_graph_gen.py with --dry-run and sanity check the graph output that would be submitted
python releasetasks_graph_gen.py --release-runner-config=../../../release-runner.yml --branch-and-product-config="/home/cltbld/releasetasks/releasetasks/release_configs/${BRANCH_CONFIG}" --common-task-id=$TASK_TASKID_FROM_GRAPH1 --dry-run

# call releasetasks_graph_gen.py for reals which will submit the graph to Taskcluster
python releasetasks_graph_gen.py --release-runner-config=../../../release-runner.yml --branch-and-product-config="/home/cltbld/releasetasks/releasetasks/release_configs/${BRANCH_CONFIG}" --common-task-id=$TASK_TASKID_FROM_GRAPH1

```
* If Plan A happened for pushing to mirrors and graph hasn't expired, proceed with the below instructions
* If Plan B happened for pushing to mirrors, the second graphh has already been created so it's safe to proceed with the below instructions

* Go to the task graph and find taskId of `publish release human decision task`
* Resolve the "publish release human decision" task:
    `taskcluster task complete <taskId>`
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

Using the Balrog Scheduled Changes UI: <https://aus4-admin.mozilla.org/rules/scheduled_changes>

Update releasewarrior:
```sh
release task ${product} ${version} --resolve signoff
cd ../releasewarrior-data && git push
```

Further details and examples can be found on the [[Balrog page|Balrog and Scheduled Changes]]

If this is a Release (not a beta, devedition or RC), then schedule an update in Balrog to change the background rate of the rule to 0% the next day.
* Go to Balrog and "Schedule an Update" for the "Firefox: release" rule that changes "backgroundRate" to 0 at 9am Pacific the following day. All other fields should remain the same.
