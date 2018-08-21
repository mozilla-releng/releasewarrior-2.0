# MergeDuty

Most code changes to Firefox and Fennec land in the [mozilla-central](https://hg.mozilla.org/mozilla-central) repository, and 'nightly' releases are built from that repo.
DevEdition and Beta are built from the [mozilla-beta](https://hg.mozilla.org/releases/mozilla-beta/) repository, Extended Support Releases from the relevant ESR repo, such as [mozilla-esr52](https://hg.mozilla.org/releases/mozilla-esr52/), and Release and Release Candidates are built from [mozilla-release](https://hg.mozilla.org/releases/mozilla-release/).

How are those repositories kept in sync? That's MergeDuty. You will be merging repositories to create new beta, release candidates, releases and extended support releases.

## Overview of Procedure

MergeDuty consists of multiple separate days of work. Each day you must perform several sequential tasks. The days are spread out over nearly three weeks, with 3 major days of activity.

The releng process usually operates like this:
* A week before the merge, do the prep work
  * Verify you have access to what you need
  * Make sure that all the dry-run migrations run cleanly
  * Sanity check you have no blocking migration bugs
* On Merge day
  * ask vcs to disable hg.m.o l10n hooks
  * mozilla-beta merges to mozilla-release
  * mozilla-central merges to mozilla-beta (relman may merge after this until we bump mozilla-central version)
  * mozilla-esr gets version bumped
  * Ask relman to create a mozilla-beta relbranch for Fennec
* A week after Merge day, bump mozilla-central and update bouncer
  * Ask relman to do final mozilla-central->mozilla-beta merge
  * bump the version and tag mozilla-central repo itself
  * update bouncer aliases
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

File a tracking migration bug if there isn't one. (e.g. [bug 1412962](https://bugzilla.mozilla.org/show_bug.cgi?id=1412962))

### Access and setup the merge remote instance

Ensure you have access and have setup [the merge remote instance](merge-and-staging-instance.md#access-and-setup-existing-merge-instance).

### Test access to Bouncer

Ensure you have access to Bouncer. You may need an account. Ask rail/mtabara/nthomas for more details if you have never done this before.

1. Create a SOCKS proxy on port `10000` using SSH via one of the masters (this should move to a jumphost after bug 1484055):
```
ssh -ND 10000  buildbot-master01.bb.releng.use1.mozilla.com
```
1. Setup Firefox (`Firefox` -> `Preferences` -> `Network Proxy` -> `Settings`) to use it like this:
![this](/docs/mergeduty/media/bouncer_setup_firefox.png?raw=true)
1. Navigate to [Bouncer](https://bounceradmin.mozilla.com/) to make sure you can login


### Do migration no-op trial runs

Doing a no-op trial run of each migration has two benefits

1. you ensure that the migrations themselves work prior to Merge day
2. you check out the necessary repos for migration which saves time before Merge day

NOTE: doing multiple gecko_migration runs is safe. Each run the script will purge hg outgoing csets and working dir so you start fresh

#### connect to remote instance and get a copy of mozharness
```sh
# connect to remote instance.
sudo su - buildduty
source /home/buildduty/mergeday/bin/activate
mkdir merge_day_${RELEASE_VERSION_FOR_CYCLE}
cd merge_day_${RELEASE_VERSION_FOR_CYCLE}
wget -O mozharness.tar.bz2 https://hg.mozilla.org/mozilla-central/archive/tip.tar.bz2/testing/mozharness/
tar --strip-components=2 -jvxf mozharness.tar.bz2
 ```

#### mozilla-beta->mozilla-release migration no-op trial run

```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/beta_to_release.py --ssh-user ${ldap_username}
hg -R build/mozilla-release diff  # have someone sanity check output with you
 ```

#### mozilla-central->mozilla-beta migration no-op trial run

```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/central_to_beta.py --ssh-user ${ldap_username}
hg -R build/mozilla-beta diff  # have someone sanity check output with you
 ```

#### esr version bump no-op trial run

```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr.py --ssh-user ${ldap_username}
hg -R build/mozilla-esr{$version} diff  # have someone sanity check output with you
 ```


## Release Merge Day

**When**: Wait for go from relman to release-signoff@mozilla.com. For date, see [Release Scheduling calendar](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ) or check with relman

### Disable migration blocking hg.m.o hooks

There are ftl check hooks on [hg.m.o](http://hg.mozilla.org/) that prevent users from pushing to certain files. Additionally, there are pretxnclose.vcsreplicator hooks that need to be disabled as it can cause a push with a lot of commits (like a merge push) to fail. Until [bug 1415233](https://bugzilla.mozilla.org/show_bug.cgi?id=1415233) is resolved, you must explicitly ask for this hook to be disabled or have an hg.m.o work around in place. File a Dev Services bug or ask in #vcs, specifying when you would like to disable/re-enable the hooks like this one. Example bug for this is [bug 1441782](https://bugzilla.mozilla.org/show_bug.cgi?id=1441782).

**Make sure you ask for the hooks to be disabled for both `mozilla-beta` and `mozilla-release`**.

### Merge beta to release

1. [Close mozilla-beta](https://mozilla-releng.net/treestatus/show/mozilla-beta). Check "Remember this change to undo later". Please enter a good message as the reason for the closure, such as "Mergeduty - closing beta for VERSION RC week"
1. Run the m-b->m-r [no-op trial run](#do-migration-no-op-trial-runs) one more time, and show the diff to another person on releaseduty.
1. The diff for `release` should be fairly similar to [this](https://hg.mozilla.org/releases/mozilla-release/rev/70e32e6bf15e), with updated branding as well as the version change.
1. Push your changes generated by no-op trial run:
```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py \
  -c selfserve/production.py -c merge_day/beta_to_release.py \
  --ssh-user ${ldap_username} --create-virtualenv --commit-changes --push
```
:warning: It's not unlikely for the push to take between 10-20 minutes to complete.

:warning: If an issue comes up during this phase, you may not be able to run this command (or the no-op one) correctly. You may need to publicly backout some tags/changesets to get back in a known state.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.

1. Upon successful run, `mozilla-release` should get a version bump and branding changes consisting of a `commit` like [this](https://hg.mozilla.org/releases/mozilla-release/rev/cbb9688c2eeb) and a `tag` like [this](https://hg.mozilla.org/releases/mozilla-release/rev/173d292663a1)
1. In the same time `mozilla-beta` should get a tag like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/0ed280054c9b)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/releases/mozilla-release/pushloghtml) and [Treeherder]( https://treeherder.mozilla.org/#/jobs?repo=mozilla-release). It may take a couple of minutes to appear.

:warning: The decision task of the resulting pushlog in the `mozilla-release` might fail in the first place with a timeout. A rerun might solve the problem which can be caused by an unlucky slow instance.

### Merge central to beta

1. Run the m-c->m-b [no-op trial run](#do-migration-no-op-trial-runs) one more time, and show the diff to another person on releaseduty.
1. The diff for `beta` should be fairly similar to [this](https://hg.mozilla.org/releases/mozilla-beta/rev/2191d7f87e2e)
1. Push your changes generated by the no-op trial run:
```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py \
  -c selfserve/production.py -c merge_day/central_to_beta.py \
  --ssh-user ${ldap_username} --create-virtualenv --commit-changes --push
```
:warning: It's not unlikely for the push to take between 10-20 minutes to complete.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.
1. Upon successful run, `mozilla-beta` should get a version bump and branding changes consisting of a `commit` like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/15334014dc67) and a `tag` like [this](https://hg.mozilla.org/releases/mozilla-beta/rev/fb732e4aebfc)
1. In the same time `mozilla-central` should get a tag like [this](https://hg.mozilla.org/mozilla-central/rev/426ef843d356)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/releases/mozilla-beta/pushloghtml) and [Treeherder]( https://treeherder.mozilla.org/#/jobs?repo=mozilla-beta). It may take a couple of minutes to appear.

:warning: The decision task of the resulting pushlog in the `mozilla-beta` might fail in the first place with a timeout. A rerun might solve the problem which can be caused by an unlucky slow instance.

### Bump ESR version

Note: you may have 1 or 2 ESRs to bump. If you are not sure, ask.

1. Steps are similar to a merge:
1. Run the bump-esr [no-op trial run]() one more time, and show the diff to another person on releaseduty.
1. Push your changes generated by the no-op trial run:
```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_esr.py \
  --ssh-user ${ldap_username} --commit-changes --push
```
:warning: It's not unlikely for the push to take between 10-20 minutes to complete.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.
1. Verify new changesets popped on https://hg.mozilla.org/releases/mozilla-esr`$ESR_VERSION`/pushloghtml

### Relbranch in m-b for Fennec

Ask RelMan, (e.g. [RyanVM](https://mozillians.org/en-US/u/RyanVM/)), to create [a relbranch like this one](https://hg.mozilla.org/releases/mozilla-beta/shortlog/FIREFOX_56b13_RELBRANCH).

### Run the l10n bumper

1. run l10n-bumper against beta

```sh
ssh buildbot-master01.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/l10n-bumper
lockfile -10 -r3 /builds/l10n-bumper/bumper.lock 2>/dev/null && (cd /builds/l10n-bumper && /tools/python27/bin/python2.7 mozharness/scripts/l10n_bumper.py -c l10n_bumper/mozilla-beta.py --ignore-closed-tree --build; rm -f /builds/l10n-bumper/bumper.lock)
```

### Re-enable hg.m.o hooks post-merging

Make sure you drop a comment in the bug to ask for re-enabling the hooks for `mozilla-beta` and `mozilla-release` again.


### Reply to relman migrations are complete

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

**When**: Wait for go from relman to release-signoff@mozilla.com. For date, see [Release Scheduling calendar](https://calendar.google.com/calendar/embed?src=bW96aWxsYS5jb21fZGJxODRhbnI5aTh0Y25taGFiYXRzdHY1Y29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ) or check with relman

### Merge central to beta one last time
Ask RelMan, (e.g. [RyanVM](https://mozillians.org/en-US/u/RyanVM/)), to do this as our automation [gecko_migrations.py](https://hg.mozilla.org/mozilla-central/file/tip/testing/mozharness/scripts/merge_day/gecko_migration.py) script will reset `mozilla-beta` version numbers which is **not** what we want.

### Tag central and bump versions

**What happens**: A new tag is needed to specify the end of the nightly cycle. Then clobber and bump versions in `mozilla-central` as instructions depict.

**How**: This is now done via the [remote instance](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/mergeduty/merge-and-staging-instance.md) and **gecko_migrations.py** similar to bumping **esr**:

1. connect to the [remote instance](https://github.com/mozilla-releng/releasewarrior-2.0/blob/master/docs/mergeduty/merge-and-staging-instance.md) and `cd` to the current `merge_day` work dir as did for the first part of the mergeduty
1. Run the tag/bump for m-c and show the diff to another person on releaseduty.
```sh
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_central.py
hg -R build/mozilla-central diff
 ```
1. The diff for `central` should be fairly similar to [this](https://hg.mozilla.org/mozilla-central/rev/d6957f004e9c)
1. Push your changes generated by the no-op trial run:
```sh
# Set this variable to your ldap e-mail address to make sure
# the push to hg.mozilla.org uses the correct username.
ldap_username=your_ldap_username@mozilla.com
python mozharness/scripts/merge_day/gecko_migration.py -c merge_day/bump_central.py \
  --ssh-user ${ldap_username} --commit-changes --push
```
:warning: It's usually a quick step (1-2 minutes) but not unlikely for the push to take slightly longer

:warning: If an issue comes up during this phase, you may not be able to run this command (or the no-op one) correctly. You may need to publicly backout some tags/changesets to get back in a known state.

:warning: If an **auth** issue comes up during this phase, most likely you need to switch from `https` to `ssh`, something like `default-push = ssh://${repo}`.

1. Upon successful run, `mozilla-central` should get a version bump consisting of a `commit` like [this](https://hg.mozilla.org/mozilla-central/rev/d6957f004e9c) and a `tag` like [this](https://hg.mozilla.org/mozilla-central/rev/a1171de0b81e)
1. Verify changesets are visible on [hg pushlog](https://hg.mozilla.org/mozilla-central/pushloghtml) and [Treeherder](https://treeherder.mozilla.org/#/jobs?repo=mozilla-central). It may take a couple of minutes to appear.

### Turn off the long living merge instance

Until we are using the puppetized instance (Bug 1469284) and it automatically stops, we should manually stop the merge instance inbetween merge days (6-8 weeks apart)



### Reply to relman central bump completed

1. Reply to the migration request with the template:

```
This is now complete:
* mozilla-central has been tagged and version bumped
* new nightlies have been trigged
```

### Update wiki versions

1. Updating is done automatically with the proper scripts at hand:
```sh
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/wiki_functions.sh
wget https://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/update_merge_day_wiki.sh
export WIKI_USERNAME=asasaki
export WIKI_PASSWORD=*******
NEW_ESR_VERSION=52  # Only if a new ESR comes up (for instance 52.0esr)
./update_merge_day_wiki.sh # Or ./update_merge_day_wiki.sh -e $NEW_ESR_VERSION
```
:warning: This script was broken at one point. If script fails, update the wiki pages manually by bumping the gecko version in below urls

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

1. After the bump, when it's confirmed we have good nightlies for `mozilla-central` with a new gecko version (nightlies auto run twice a day), take time to update the [bouncer](https://bounceradmin.mozilla.com) locations as well in order to reflect the new version for following aliases:
    1. [firefox-nightly-latest](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=2005)
    1. [firefox-nightly-latest-ssl](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6508)
    1. [firefox-nightly-latest-l10n](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6506)
    1. [firefox-nightly-latest-l10n-ssl](https://bounceradmin.mozilla.com/admin/mirror/location/?product__id__exact=6507)


:warning: Be careful on how you make changes to bouncer entries. If it is just the version that gets bumped, that's totally fine, but if you also need to change some installer names or anything alike, `space` needs to be encoded to `%20%` and such. See [bug 1386765](https://bugzilla.mozilla.org/show_bug.cgi?id=1386765) for what happened during 57 nightlies migration.

:warning: It is expected that the two stub products have a `win` and `win64` location which both point to the same location. We don't have a `win64` stub installer, instead the mislabeled 32bit stub selects the correct full installer at runtime.

### Re-opening the tree(s)

This step is performed by Sherrifs and RelMan when green builds are present so you don't have to worry about anything here.
