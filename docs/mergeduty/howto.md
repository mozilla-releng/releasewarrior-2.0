# MergeDuty

Most code changes to Firefox and Fennec land in the [mozilla-central](https://hg.mozilla.org/mozilla-central) repository, and 'nightly' releases are built from that repo.
DevEdition and Beta are built from the [mozilla-beta](https://hg.mozilla.org/releases/mozilla-beta/) repository, Extended Support Releases from the relevant ESR repo, such as [mozilla-esr52](https://hg.mozilla.org/releases/mozilla-esr52/), and Release and Release Candidates are built from [mozilla-release](https://hg.mozilla.org/releases/mozilla-release/).

How are those repositories kept in sync? That's MergeDuty. You will be merging repositories to create new beta, release candidates, releases and extended support releases.

## Overview of Procedure

MergeDuty consists of multiple separate days of work. Each day you must perform several sequential tasks. The days are spread out over nearly three weeks, with 3 major days of activity.

The releng process usually operates like this:
* A week before the merge, do the prep work
  * Verify you have access to what you need
  * Create the buildbot-config version bump patches that will land on Merge day
  * Make sure that all the dry-run migrations run cleanly
  * Sanity check you have no blocking migration bugs
* On Merge day
  * ask vcs to disable hg.m.o l10n hooks
  * bump mozilla-beta and mozilla-release buildbot gecko versions
  * mozilla-beta merges to mozilla-release
  * mozilla-central merges to mozilla-beta (relman may merge after this until we bump mozilla-central version)
  * mozilla-esr gets version bumped
  * Ask relman to create a mozilla-beta relbranch for Fennec
* A week after Merge day, bump mozilla-central and update bouncer
  * Ask relman to do final mozilla-central->mozilla-beta merge
  * bump mozilla-central buildbot gecko versions
  * bump the version and tag mozilla-central repo itself
  * Trigger new nightlies
  * update bouncer aliases
  * Trim bouncer's Check Now list
  * bump wiki versions


For history of this procedure:

Originally, the m-c->m-b was done a week after m-b->m-r. Starting at Firefox 57, Release Management wanted to ship DevEdition b1 week before the planned mozilla-beta merge day. This meant Releng had to merge both repos at the same time.

## Requirements

1. For migrations: access and setup of [the merge remote instance](merge-and-staging-instance.md#access-and-setup-existing-merge-instance). While possible to do locally, the remote instance is strongly recommended.
1. For updating bouncer aliases: Access to Bouncer
1. Access to Treestatus
1. A tracking migration bug

# Tasks

## Prep day - 1 week prior to Merge day

### File tracking migration bug

File a tracking migration bug if there isn't one. e.g. [example bug](https://bugzilla.mozilla.org/show_bug.cgi?id=1412962)

### Access and setup the merge remote instance

Ensure you have access and have setup [the merge remote instance](merge-and-staging-instance.md#access-and-setup-existing-merge-instance).

### Test access to Bouncer

Ensure you have access to Bouncer. You may need an account. Ask nthomas for more details if you have never done this before. TODO add instructions for connecting.

### Create buildbot-config patches

1. Make sure you have a fresh and up to date copy of [buildbot-configs](https://hg.mozilla.org/build/buildbot-configs/)
1. On the merge day bug, create two patches to bump [gecko_versions.json](https://dxr.mozilla.org/build-central/source/buildbot-configs/mozilla/gecko_versions.json). Get them reviewed but **don't land them yet**. Note that reviewboard can't land on buildbot-configs, you will need to push changes manually.
   * patch 1: bump the version for **mozilla-release** and **mozilla-beta**. [Example](https://bugzilla.mozilla.org/show_bug.cgi?id=1412962#c14).
   * patch 2: bump the version for **mozilla-central**. [Example](https://bugzilla.mozilla.org/show_bug.cgi?id=1412962#c15).

### Do migration no-op trial runs

Doing a no-op trial run of each migration has two benefits

1. you ensure that the migrations themselves work prior to Merge day
2. you check out the necessary repos for migration which saves time before Merge day

NOTE: doing multiple gecko_migration runs is safe. Each run the script will purge hg outgoing csets and working dir so you start fresh

#### connect to remote instance and get a copy of mozharness
```sh
# connect to remote instance.
cd merge_day_${RELEASE_VERSION_FOR_CYCLE}
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/utils/archiver_client.py
python archiver_client.py mozharness --destination mozharness-central --repo mozilla-central --rev default --debug  # mozharness-central must be used against every branch
 ```

#### mozilla-beta->mozilla-release migration no-op trial run

```sh
python mozharness-central/scripts/merge_day/gecko_migration.py -c merge_day/beta_to_release.py
hg -R build/mozilla-release diff  # have someone sanity check output with you
 ```

#### mozilla-central->mozilla-beta migration no-op trial run

```sh
python mozharness-central/scripts/merge_day/gecko_migration.py -c merge_day/central_to_beta.py
hg -R build/mozilla-beta diff  # have someone sanity check output with you
 ```

#### esr version bump no-op trial run

```sh
python mozharness-central/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr.py
hg -R build/mozilla-esr{$version} diff  # have someone sanity check output with you
 ```


## Release Merge Day

When: Wait for go from relman to release-signoff@mozilla.com. For date, see [Release Scheduling calendar](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ) or check with relman

### Disable migration blocking hg.m.o hooks

There are ftl check hooks on hg.m.o that prevent users from pushing to certain files. File a Dev Services bug or ask in #vcs, specifying when you would like to disable/re-enable the hook like this one:

[Bug 1441782 - disable hg ftl (l10n) check hook during merge day, Thurs Feb 1st for mozilla-beta and mozilla-release repos](https://bugzilla.mozilla.org/show_bug.cgi?id=1441782)

### Buildbot Re-config part 1

when: this can happen before relman request migration. e.g. the same day but in the morning

1. Look at the merge day bug and see if patches need to land at this stage.
1. Land "patch 1" (the mozilla-release/mozilla-beta version bump) to `default` branch of buildbot-configs and wait for tests to run and confirm they pass in `#releng`
1. The reconfiguration is triggered by a cron job every hour exactly on the hour (`0 * * * *` in crontab). Your options are:
   * Wait for the reconfig to happen via cron.
   * Ask buildduty to manually trigger it.
   * Run it yourself, see [how-to-manually-perform-reconfig](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/misc-operations/manually-perform-bb-reconfig-generate-partials.md) for instructions

### Merge beta to release

1. [Close mozilla-beta](https://mozilla-releng.net/treestatus/show/mozilla-beta). Check "Remember this change to undo later". Please enter a good message as the reason for the closure, such as "Mergeduty - closing beta for VERSION RC week"
1. Run the m-b->m-r [no-op trial run]() one more time, and show the diff to another person on releaseduty.
1. The diff for `release` should be fairly similar to [this](https://hg.mozilla.org/releases/mozilla-release/rev/70e32e6bf15e), with updated branding as well as the version change.
1. Push your changes generated by no-op trial run:
```sh
python mozharness-central/scripts/merge_day/gecko_migration.py \
  -c selfserve/production.py -c merge_day/beta_to_release.py \
  --create-virtualenv --commit-changes --push
```
:warning: If an issue comes up during this phase, you may not be able to run this command (or the no-op one) correctly. You may need to publicly backout some tags/changesets to get back in a known state.
1. Upon pushing, `beta` should get a version bump consisting of a `commit` like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/52cefa439a7d) and a `tag` like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/907a3a5c6fed)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/releases/mozilla-release/pushloghtml) and [Treeherder]( https://treeherder.mozilla.org/#/jobs?repo=mozilla-release). It may take a couple of minutes to appear.

### Merge central to beta

1. Run the m-c->m-b [no-op trial run]() one more time, and show the diff to another person on releaseduty.
1. The diff for `beta` should be fairly similar to [this](https://hg.mozilla.org/releases/mozilla-beta/rev/2191d7f87e2e)
1. Push your changes generated by the no-op trial run:
```sh
python mozharness-central/scripts/merge_day/gecko_migration.py \
  -c selfserve/production.py -c merge_day/central_to_beta.py \
  --create-virtualenv --commit-changes --push
```
1. Upon pushing, `central` should get a version bump consisting of a `commit` like [this](https://hg.mozilla.org/mozilla-central/rev/52285ea5e54c) and a `tag` like [this](https://hg.mozilla.org/mozilla-central/rev/d6c0df73518b)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/releases/mozilla-beta/pushloghtml) and [Treeherder]( https://treeherder.mozilla.org/#/jobs?repo=mozilla-beta). It may take a couple of minutes to appear.

### Bump ESR version

Note: you may have 1 or 2 ESRs to bump. If you are not sure, ask.

1. Steps are similar to a merge:
1. Run the bump-esr [no-op trial run]() one more time, and show the diff to another person on releaseduty.
1. Push your changes generated by the no-op trial run:
```sh
python mozharness-central/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr.py \
  --commit-changes --push
```
1. Verify new changesets popped on https://hg.mozilla.org/releases/mozilla-esr`$ESR_VERSION`/pushloghtml

### Relbranch in m-b for Fennec

Ask relman, e.g. ryanvm, to create [a relbranch like this one](https://hg.mozilla.org/releases/mozilla-beta/shortlog/FIREFOX_56b13_RELBRANCH).

### Run the l10n bumper

1. run l10n-bumper against beta

```sh
ssh buildbot-master01.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/l10n-bumper
python2.7 mozharness/scripts/l10n_bumper.py -c mozharness/configs/l10n_bumper/mozilla-beta.py --ignore-closed-tree
```

### reply to relman migrations are complete

1. Reply to the migration request with the template:

```
This is now complete:
* mozilla-beta is merged to mozilla-release, new version is XX.Y
* mozilla-central is merged to mozilla-beta, new version is XX.Y
* mozilla-central will continue to merge to mozilla-beta over the week until mozilla-central is version bumped
* esr is now XX.Y.Z
* beta will stay closed until next week
```


## Bump and tag mozilla-central - 1 week after Merge day

When: Wait for go from relman to release-signoff@mozilla.com. For date, see [Release Scheduling calendar](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ) or check with relman

### Buildbot re-config part 2

Do the same things as buildbot-configs patch 1 from Merge day, except you should land "patch 2" instead.

### Merge central to beta one last time

You can ask relman, e.g. ryanvm, to do this as gecko_migrations.py logic will reset mozilla-beta version numbers, etc which is not what we want.

### Tag central and bump versions

What happens: A new tag is needed to specify the end of the nightly cycle, for instance: [FIREFOX_NIGHTLY_57_END](https://hg.mozilla.org/mozilla-central/rev/1ca411f5e97b). Then you have to clobber and bump versions in m-c, just [like the following](https://hg.mozilla.org/mozilla-central/rev/835a92b19e3d).

How: This is now done via the remote instance and gecko_migrations.py similar to bumping esr:


1. connect to the remote instance and cd to the current merge_day work dir as earlier
```sh
python mozharness-central/scripts/merge_day/gecko_migration.py -c merge_day/bump_central.py
hg -R build/mozilla-central diff  # have someone sanity check output with you
 ```
1. Push your changes generated by the no-op trial run:
```sh
python mozharness-central/scripts/merge_day/gecko_migration.py -c merge_day/bump_central.py \
  --commit-changes --push
```
1. Verify new changesets popped on https://hg.mozilla.org/mozilla-central/pushloghtml


### Trigger new nightlies

1. Trigger nightlies for central. This can be done by:
    1. trigger [nightly-desktop/mozilla-central](https://tools.taskcluster.net/hooks/#project-releng/nightly-desktop%252fmozilla-central) hook
    1. trigger [nightly-fennec/mozilla-central](https://tools.taskcluster.net/hooks/#project-releng/nightly-fennec%252fmozilla-central) hook


### reply to relman central bump completed

reply to relman email request that:

* mozilla-central has been tagged and version bumped
* new nightlies have been trigged

### Update wiki versions

:warning: this script was broken at one point. If script fails, update the wiki pages manually by bumping the gecko version in below urls

1. Updating is done automatically with the proper scripts at hand:
```sh
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/wiki_functions.sh
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/update_merge_day_wiki.sh
export WIKI_USERNAME=asasaki
export WIKI_PASSWORD=*******
NEW_ESR_VERSION=52  # Only if a new ESR comes up (for instance 52.0esr)
./update_merge_day_wiki.sh # Or ./update_merge_day_wiki.sh -e $NEW_ESR_VERSION
```
1. Check the new values:
  * [NEXT_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/release/next)
  * [CENTRAL_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/central/current)
  * [BETA_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/beta/current)
  * [RELEASE_VERSION](https://wiki.mozilla.org/Template:Version/Gecko/release/current)
  * [Next release date](https://wiki.mozilla.org/index.php?title=Template:NextReleaseDate). This updates
    * [The next ship date](https://wiki.mozilla.org/index.php?title=Template:FIREFOX_SHIP_DATE)
    * [The next merge date](https://wiki.mozilla.org/index.php?title=Template:FIREFOX_MERGE_DATE)
    * [The current cycle](https://wiki.mozilla.org/index.php?title=Template:CURRENT_CYCLE)


### Bump bouncer versions

1. When we have good nightlies from `mozilla-central` bump with the new version, update the [bouncer](https://bounceradmin.mozilla.com) locations to reflect the new version for following aliases:
    1. [firefox-nightly-latest](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=2005)
    1. [firefox-nightly-latest-ssl](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6508)
    1. [firefox-nightly-latest-l10n](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6506)
    1. [firefox-nightly-latest-l10n-ssl](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6507)
    1. [firefox-nightly-stub](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6509)
    1. [firefox-nightly-stub-l10n](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6512)


:warning: Be careful on how you make changes to bouncer entries. If it is just the version that gets bumped, that's totally fine, but if you also need to change some installer names or anything alike, `space` needs to be encoded to `%20%` and such. See [bug 1386765](https://bugzilla.mozilla.org/show_bug.cgi?id=1386765) for what happened during 57 nightlies migration.

NB: it is expected that the two stub products have a win and win64 location which both point to the same location. We don't have a win64 stub installer, instead the mislabeled 32bit stub selects the correct full installer at runtime.

### Trim bouncer's Check Now list

:warning: this may not be required now that we removed sentry. Confirm with nthomas [More details](https://github.com/mozilla-releng/releasewarrior-2.0/pull/74#discussion_r171249691)

1. Once per release cycle we should stop checking old releases to see if they're present
1. Visit the [list of check now enabled products](https://bounceradmin.mozilla.com/admin/mirror/product/?all=&checknow__exact=1)
1. you should leave all current and upcoming releases enabled, as well as the updates for watershed releases. Typically this is about 100 products
1. Select all the old releases not covered above, and use the 'Remove Check Now on selected products' option in the Action dropdown

