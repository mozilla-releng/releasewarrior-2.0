# MergeDuty

All code changes to Firefox land in the [mozilla-central](https://hg.mozilla.org/mozilla-central) repository while the Fennec counterpart land to [mozilla-esr68](https://hg.mozilla.org/releases/mozilla-esr68).
* The `nightly` releases are built from that repo twice a day.
* DevEdition and Beta releases are built from the [beta](https://hg.mozilla.org/releases/mozilla-beta/) repository
* Extended Support Releases follow-up from the relevant ESR repo, such as [mozilla-esr68](https://hg.mozilla.org/releases/mozilla-esr68/)
* Release and Release Candidates are built from [mozilla-release](https://hg.mozilla.org/releases/mozilla-release/) repository

How are those repositories kept in sync? That's `MergeDuty` and is part of the `releaseduty` responsibility.

## Overview of Procedure

`MergeDuty` consists of multiple separate days of work. Each day you must perform several sequential tasks. The days are spread out over nearly three weeks, with *three* major days of activity:

* Do the prep work a week before the merge
  * [Set up mergeduty trello tracking board](#set-up-mergeduty-trello-tracking-board)
  * [File tracking migration bug](#file-tracking-migration-bug)
  * [Run staging releases](#run-staging-releases)
  * [Access and setup the merge remote instance](#access-and-setup-the-merge-remote-instance)
  * [Do migration no-op trial runs](#do-migration-no-op-trial-runs)
  * [Sanity check no blocking migration bugs](#sanity-check-no-blocking-migration-bugs)
  * [Land whatsnewpage list of locales](#land-whatsnewpage-list-of-locales)
* On Merge day:
  * [Merge beta to release](#merge-beta-to-release)
  * [Reply migrations are complete](#reply-to-relman-migrations-are-complete)
* A week after Merge day, bump mozilla-central:
  * [Merge central to beta](#merge-central-to-beta)
  * [Re-open trees](#re-opening-the-trees)
  * [Run l10n bumper](#run-the-l10n-bumper)
  * [Tag central and bump versions](#tag-central-and-bump-versions)
  * [Bump mozilla-esr](#bump-esr-version)
  * [Turn off merge instance](#turn-off-the-long-living-merge-instance)
  * [Reply to RelMan that procedure is completed](#reply-to-relman-central-bump-completed)
  * [Update wiki versions](#update-wiki-versions)
  * [Bump Nightly version in ShipIt](#bump-nightly-shipit)


Historical context of this procedure:

Originally, the `m-c` -> `m-b` was done a week after `m-b` -> `m-r`. Starting at `Firefox 57`, Release Management wanted to ship DevEdition `b1` week before the planned mozilla-beta merge day. This meant Releng had to merge both repos at the same time.
With 71.0, we're back to the initial workflow with merging `m-b` -> `m-r` in the first week and then `m-c` -> `m-b` in the follow-up week.


## Do the prep work a week before the merge

### Set up mergeduty trello tracking board

Rather than extend Releasewarrior with more complexity, the idea here is to try Trello and use Templated cards for todo tracking.

To track human tasks and issues during merges, we use the following [trello board](https://trello.com/b/AyyFAEbS/mergeduty-tasks).

**First, ensure the board is clean**:

- In the `Merge Tasks` list, select `Archive all cards in this list`
- Sanity check that all items in `Postmortem Issues` and `Postmortem Action Items` lists have been resolved then:
  - In the `Postmortem Issues` list, select `move all cards in this list` to the `Archived Postmortem Issues` list
  - In the `Postmortem Action Items` list, select `move all cards in this list` to the `Archived Postmortem Action Items` list

**Now prep the board for this cycle's planned merges**:

- For each card in the `Templates` list, select the card then under Actions, choose `Copy` and put in the `Merge Tasks` list
- For each newly copied card in the `Merge Tasks` list
  - Add the people on mergeduty to the members list
  - Set a deadline for each that correspond with the current [merge schedule](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)

**For each merge task**:

As you go through the steps documented below, update the checklists within the cards under `Merge Tasks`. This helps with handoff and tracking state.

As issues arise, add a card under the `Merge Issues` list. Associate with bugs where appropriate. Use labels for issues. Each issue should either be `Resolved` or `Unresolved` and some `Resolved` issues may be also labeled as `Future Threats`.

**For postmortems**:

After merge days, schedule a postmortem (or use current releaseduty postmortem) and move all issues to the `Postmortem Issues` list. During the postmortem, if any action items come up, track those in the `Postmortem Action Items` list.

### File tracking migration bug

File a tracking migration bug if there isn't one (e.g. [bug 1412962](https://bugzilla.mozilla.org/show_bug.cgi?id=1412962))

### Run staging releases

In order to prepare a smooth `b1` and `RC`, staging releases are to be run in the week before the mergeday day 1. In order for this to happen, we're using [staging releases submitted to try](https://firefox-source-docs.mozilla.org/tools/try/selectors/release.html).

**For central to beta migration**

- hop on `central` repository
- make sure you're up to date with the tip of the repo
- `mach try release --version <future-version.0b1> --migration central-to-beta --tasks release-sim`

**For beta to release migration**

- hop on `beta` repository
- make sure you're up to date with the tip of the repo
- `mach try release --version <future-version.0> --migration beta-to-release --tasks release-sim`

These will create try pushes that look-alike the repos once they are merged. Once the decision tasks of the newly created CI graphs
are green, staging releases can be created off of them via the [shipit-staging](https://shipit.staging.mozilla-releng.net/) instance.

One caveat here is the list of partials that needs to be filled-in.
:warning: The partials need to exist in [S3](http://ftp.stage.mozaws.net/pub/firefox/releases/) and be valid releases in [Balrog staging](https://balrog-admin-static-stage.stage.mozaws.net/).

Ideally staging releases are triggered both on _Monday/Tuesday_ but also on _Thursday/Friday_ to ensure that we're up to date with all the patches that
Sheriffs are landing before the `RC` week.

Once the staging releases are being triggered, it's highly recommended that at least a comment is being dropped to Sherrifs team (e.g. `Aryx`) to let them know these are happening in order to:
* avoid stepping on each others toes as they may run staging releases as well
* make sure we're up-to-date to recent patches that they may be aware of

:warning: Allow yourself enough time to wait for these staging releases to be completed. Since they are running in `try`, they have the lowest priority even on the staging workers so it usually takes longer for them to complete.

### Access and setup the merge remote instance

Ensure you have access and have setup the merge remote instance. While possible to do locally, the remote instance is strongly recommended.

There is an AWS instance to run staging and merging instances so that we are fewer hops away from the hg repos.
1. To access it, make sure to start the `mergeday1` instance in `us-west-2` from the `AWS console`. That is, finding
it in the instance list, hover over to `Actions` -> `Instance state` -> `Start`. It will get puppetized as soon as it's started.

2. You should be able to access it with:

```sh
 ssh mergeday1.srv.releng.usw2.mozilla.com
```

### Do migration no-op trial runs

Doing a no-op trial run of each migration has two benefits

1. you ensure that the migrations themselves work prior to Merge day
2. you check out the necessary repos for migration which saves time before Merge day

NOTE: doing multiple gecko_migration runs is safe. Each run the script will purge hg outgoing csets and working dir so you start fresh

#### connect to remote instance and get a copy of mozharness
```sh
# connect to remote instance.
sudo su - buildduty
# create a screen session to be disconnect-proof and allow for session sharing
script /dev/null
screen
# proceed inside the screen session
source /home/buildduty/mergeday/bin/activate
mkdir merge_day_${RELEASE_VERSION_FOR_CYCLE}
cd merge_day_${RELEASE_VERSION_FOR_CYCLE}
wget -O mozharness.zip https://hg.mozilla.org/mozilla-central/archive/tip.zip/testing/mozharness/
unzip mozharness.zip
wget -O mozbase.zip https://hg.mozilla.org/mozilla-central/archive/tip.zip/testing/mozbase/
unzip mozbase.zip
for package in manifestparser mozinfo mozprocess mozfile; do cp -pr mozbase/${package}/${package} mozharness/; done
 ```

#### mozilla-beta->mozilla-release migration no-op trial run

```sh
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/beta_to_release.py
hg -R build/mozilla-release diff  # have someone sanity check output with you
 ```

#### mozilla-central->mozilla-beta migration no-op trial run

```sh
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/central_to_beta.py
hg -R build/mozilla-beta diff  # have someone sanity check output with you
 ```

#### mozilla-esr bump no-op trial run

#### ESR bump requires a different copy of mozharness

You need to download a different set of mozharness because ESR68 has a different configuration due to Fennec ESR.

```sh
export version=68
export full_version=68.4.0
mkdir ~/merge_day_esr_${full_version}
cd ~/merge_day_esr_${full_version}
wget -O mozharness.zip https://hg.mozilla.org/releases/mozilla-esr${version}/archive/tip.zip/testing/mozharness/
unzip mozharness.zip
wget -O mozbase.zip https://hg.mozilla.org/releases/mozilla-esr${version}/archive/tip.zip/testing/mozbase/
unzip mozbase.zip
for package in manifestparser mozinfo mozprocess mozfile; do cp -pr mozbase/${package}/${package} mozharness/; done
 ```

Run the bump-esr [no-op trial run](#do-migration-no-op-trial-runs), and show the diff to another person on releaseduty.

```sh
export version=68
export full_version=68.4.0
cd ~/merge_day_esr_${full_version}
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr${version}.py --ssh-user ffxbld-merge
hg -R build/mozilla-esr${$version} diff  # have someone sanity check output with you
 ```

Diff should be similar to [this one](https://hg.mozilla.org/releases/mozilla-esr68/rev/2d43ffaa9d1adf29b71f0b7354374463c8d7b621).

### Sanity check no blocking migration bugs

Make sure the bug that tracks the migration has no blocking items.

### Land whatsnewpage list of locales
**TODO** - this needs to change, as the process no longer assumes this, but apply them; the l10n drivers provide the final list of locales to receive the WNP on the Tuesday prior to the ship date.

1. For each release, there should already be a bug flying around named `Setup WNP for users coming from < X and receiving the X release`. Find it for the current release. e.g. [Bug 1523699](https://bugzilla.mozilla.org/show_bug.cgi?id=1523699).
We should always aim to chain this bug to our main mergeduty tracking bug. That is, block the WNP bug against the `tracking XXX migration day`. If not already, please do so. This way, it's easier to find deps and nagivate via bugs.
1. By the Friday prior to merge day, the l10n (most likely `Peiying Mo [:CocoMo]`) team will have posted the final list of locales for whatsnewpage.
Double-check with them again to make sure that is the final list. The list of locales comes in two forms: attachment in bug directly to be `hg import`ed, but also as a comment.
Make sure to double-check they match as that's generated automatically and sometimes there could be fallouts resulting in mismatches.
1. Update the [in-tree whatsnewpage list of locales](https://hg.mozilla.org/mozilla-central/file/tip/browser/config/whats_new_page.yml) on central and uplift that to beta. Similar to [this patch](https://hg.mozilla.org/mozilla-central/rev/55c218c9489b). It will uplift to release when the merge happens
    1. On development machine, update `browser/config/whats_new_page.yml` with the list of locales from the bug
    1. Commit the change and create Phabricator patch request as usual
    1. Once the patch request is approved and landed, `hg pull`
        * The revision should appear in the `autoland`
    1. `hg up beta`, `hg graft ${COMMIT_REVISION}`
    1. Confirm your changes with `hg out -p -r . beta`, then push with `hg push -r . beta`


## Release Merge Day - part I

**When**: Wait for go from relman to release-signoff@mozilla.com. Relman might want to do the migration in two steps. Read the email to understand which migration you are suppose to do, and then wait for second email. For date, see [Release Scheduling calendar](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ) or check with relman

### Merge beta to release

1. [Close mozilla-beta](https://mozilla-releng.net/treestatus/show/mozilla-beta). Check _"Remember this change to undo later"_. Please enter a good message as the reason for the closure, such as "Mergeduty - closing beta for $VERSION RC week".
1. Run the `m-b -> m-r` [no-op trial run](#do-migration-no-op-trial-runs) one more time, and show the diff to another person on releaseduty.
1. The diff for `release` should be fairly similar to [this](https://hg.mozilla.org/releases/mozilla-release/rev/0eae18af659f087056bce0f62a325e5e595fff72), with updated the version change.
1. Push your changes generated by no-op trial run:
```sh
python mozharness/scripts/merge_day/gecko_migration.py \
  -c merge_day/beta_to_release.py \
 --create-virtualenv --commit-changes --push
```
:warning: It's not unlikely for the push to take between 10-20 minutes to complete.

:warning: If an issue comes up during this phase, you may not be able to run this command (or the no-op one) correctly. You may need to publicly backout some tags/changesets to get back in a known state.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.

1. Upon successful run, `mozilla-release` should get a version bump and branding changes consisting of a `commit` like [this](https://hg.mozilla.org/releases/mozilla-release/rev/2fb19d0466d2f61674c0af80813645cccd510593) and a `tag` like [this](https://hg.mozilla.org/releases/mozilla-release/rev/be8c618fd8ad921642e04e1552fbad46a044fe9e)
1. In the same time `mozilla-beta` should get a tag like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/d87f9b66ddd19a973ec3ef26a9163bab9383c438)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/releases/mozilla-release/pushloghtml) and [Treeherder]( https://treeherder.mozilla.org/#/jobs?repo=mozilla-release). It may take a couple of minutes to appear.

:warning: The decision task of the resulting pushlog in the `mozilla-release` might fail in the first place with a timeout. A rerun might solve the problem which can be caused by an unlucky slow instance.


### Reply to relman migrations are complete

Reply to the migration request with the template:

```
This is now complete:
* mozilla-beta is merged to mozilla-release, new version is XX.Y
* beta will stay closed until next week
```

## Release Merge Day - part II - a week after Merge day

**When**: Wait for go from relman to release-signoff@mozilla.com. For date, see [Release Scheduling calendar](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ) or check with relman

### Merge central to beta

1. Run the `m-c -> m-b` [no-op trial run](#do-migration-no-op-trial-runs) one more time, and show the diff to another person on releaseduty.
1. The diff for `beta` should be fairly similar to [this](https://hg.mozilla.org/releases/mozilla-beta/rev/2191d7f87e2e).
1. Push your changes generated by the no-op trial run:
```sh
python mozharness/scripts/merge_day/gecko_migration.py \
  -c merge_day/central_to_beta.py \
 --create-virtualenv --commit-changes --push
```
:warning: It's not unlikely for the push to take between 10-20 minutes to complete.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.
1. Upon successful run, `mozilla-beta` should get a version bump and branding changes consisting of a `commit` like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/53ea74d2bd09de0972820d6264abf1e17c1f1a79) and a `tag` like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/eec47871f86e569dfcae03712cdc98acd57d8c3b)
1. In the same time `mozilla-central` should get a tag like [this](https://hg.mozilla.org/mozilla-central/rev/7573050ba145afe5c0f9fcb28f5fead5e240cba9)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/releases/mozilla-beta/pushloghtml) and [Treeherder]( https://treeherder.mozilla.org/#/jobs?repo=mozilla-beta). It may take a couple of minutes to appear.

:warning: The decision task of the resulting pushlog in the `mozilla-beta` might fail in the first place with a timeout. A rerun might solve the problem which can be caused by an unlucky slow instance.

### Re-opening the tree(s)

Ask Sheriffs and RelMan to re-open trees (either `open` or `approval-only`) so that l10n bumper can run.

### Run the l10n bumper

Run `l10n-bumper` against beta:

We now have automated cron jobs in Taskcluster to perform this step for us. Trigger [this hook](https://firefox-ci-tc.services.mozilla.com/hooks/project-releng/cron-task-releases-mozilla-beta%2Fl10n-bumper) to run l10n bumper on `mozilla-beta`.
It takes a few min to run because of the robustcheckouts, even though they are sparse. The job queries Treestatus for trees status so it will **fail** if the trees are still closed.
It is safe to rerun in case of failure. It requires that the mozilla-beta merge push is visible on the hg webheads. So either wait a few min after the `m-c` => `m-b` push step or verify it's visible on [mozilla-beta](https://hg.mozilla.org/releases/mozilla-beta).

### Tag central and bump versions

**What happens**: A new tag is needed to specify the end of the nightly cycle. Then clobber and bump versions in `mozilla-central` as instructions depict.

**How**: This is now done via [the merge remote instance](#access-and-setup-the-merge-remote-instance) and **gecko_migrations.py** similar to bumping **esr**:

1. connect to [the merge remote instance](#access-and-setup-the-merge-remote-instance) and `cd` to the current `merge_day` work dir as did for the first part of the mergeduty
1. Run the tag/bump for m-c and show the diff to another person on releaseduty.
```sh
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_central.py
hg -R build/mozilla-central diff
 ```
1. The diff for `central` should be fairly similar to [this](https://hg.mozilla.org/mozilla-central/rev/d6957f004e9c)
1. Push your changes generated by the no-op trial run:
```sh
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_central.py \
 --commit-changes --push
```
:warning: It's usually a quick step (1-2 minutes) but not unlikely for the push to take slightly longer

:warning: If an issue comes up during this phase, you may not be able to run this command (or the no-op one) correctly. You may need to publicly backout some tags/changesets to get back in a known state.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.

1. Upon successful run, `mozilla-central` should get a version bump consisting of a `commit` like [this](https://hg.mozilla.org/mozilla-central/rev/d6957f004e9c) and a `tag` like [this](https://hg.mozilla.org/mozilla-central/rev/a1171de0b81e)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/mozilla-central/pushloghtml) and [Treeherder](https://treeherder.mozilla.org/#/jobs?repo=mozilla-central). It may take a couple of minutes to appear.

### Bump ESR version

Note: You could have one ESR to bump, or two. If you are not sure, ask.

Run the bump-esr [no-op trial run](#do-migration-no-op-trial-runs) one more time, and show the diff to another person on releaseduty.

```sh
export version=68
export full_version=68.4.0
cd ~/merge_day_esr_${full_version}
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr${version}.py --ssh-user ffxbld-merge
hg -R build/mozilla-esr${version} diff  # have someone sanity check output with you
 ```

Diff should be similar to [this one](https://hg.mozilla.org/releases/mozilla-esr68/rev/2d43ffaa9d1adf29b71f0b7354374463c8d7b621).

Push your changes generated by the no-op trial run:
```sh
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr${version}.py \
  --ssh-user ffxbld-merge --commit-changes --push
```

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.
1. Upon successful run, `mozilla-esr${VERSION}` should get a `commit` like [this](https://hg.mozilla.org/releases/mozilla-esr68/rev/2d43ffaa9d1adf29b71f0b7354374463c8d7b621).
1. Verify new changesets popped on https://hg.mozilla.org/releases/mozilla-esr`$ESR_VERSION`/pushloghtml

### Reply to relman central bump completed

Reply to the migration request with the template:

```
This is now complete:
* mozilla-central is merged to mozilla-beta, new version is XX.Y
* mozilla-central has been tagged and version bumped
* mozilla-esr has been version bumped
* newly triggered nightlies will pick the version change on cron-based schedule
```

### Turn off the long living merge instance

The machine is not configured to automatically shut down. We should manually stop the merge instance inbetween merge days (6-8 weeks apart)


### Update wiki versions

The following steps don't work anymore because of [bug 1414278](https://bugzilla.mozilla.org/show_bug.cgi?id=1414278).

~~1. Updating is done automatically with the proper scripts at hand:~~
```sh
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/wiki_functions.sh
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/update_merge_day_wiki.sh
export WIKI_USERNAME=asasaki
export WIKI_PASSWORD=*******
NEW_ESR_VERSION=52  # Only if a new ESR comes up (for instance 52.0esr)
./update_merge_day_wiki.sh # Or ./update_merge_day_wiki.sh -e $NEW_ESR_VERSION
```
~~:warning: This script was broken at one point. If script fails, update the wiki pages manually by bumping the gecko version in below urls~~

1. ~~Check~~ Edit the new values manually:
  * [NEXT_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/release/next)
  * [CENTRAL_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/central/current)
  * [BETA_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/beta/current)
  * [RELEASE_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/release/current)
  * [Next release date](https://wiki.mozilla.org/index.php?title=Template:NextReleaseDate). This updates
    * [The next ship date](https://wiki.mozilla.org/index.php?title=Template:FIREFOX_SHIP_DATE)
    * [The next merge date](https://wiki.mozilla.org/index.php?title=Template:FIREFOX_MERGE_DATE)
    * [The current cycle](https://wiki.mozilla.org/index.php?title=Template:CURRENT_CYCLE)


### Bump Nightly version in ShipIt

ShipIt currently hardcodes the version of Nightly that's being released. It doesn't automatically updated
because it would need to know when a new nightly was available, not just when the version had been updated in-tree.
Everything up to merging this pull request can be done early, but the PR must not be merged before the
first nightly has been built and published with the new version.

1. `git clone git@github.com:mozilla-releng/shipit.git`
2. `git checkout -b nightly_version_bump_${version}`
3. Edit both FIREFOX_NIGHTLY and FENNEC_NIGHTLY in https://github.com/mozilla-releng/shipit/blob/master/api/src/shipit_api/config.py#L41
4. Commit, and submit a pull request
5. Merge the pull request _after_ a new nightly version has been pushed to CDNs


