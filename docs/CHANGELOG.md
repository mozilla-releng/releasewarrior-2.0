Every time a new releaseduty cycle begings, new RelEng people are (re)ramping up. To ease the transition, we're keeping this CHANGELOG that should trace all the tools/productivity/infrastructure changes. This include high-level changes and should come into compliance with the rest of the documentation.

This page best serves the people that have previously been into the releaseduty cycle. Starting from the baseline, people coming back after `N` cycles can ramp up incrementally with the latest changes.

_**As releaseduty squirrels are the ones with the best context when it comes to releases, they are the ones to edit this page and amend it accordingly. Keep in mind that changes should be in compliance with the other pieces of documentation.**_

## During 59.0 >= 2018-01-24

### Added
- we track all major changes in this newly added CHANGELOG

### Changed
- old release promotion based on [releasetasks](https://github.com/mozilla/releasetasks/) is dead. Everything is in-tree scheduled now. Changes are riding the trains. More on this [here](https://github.com/mozilla-releng/releasewarrior-2.0/wiki/Release-Promotion-Overview-TC) and [here](https://github.com/mozilla-releng/releasewarrior-2.0/wiki/Release-Promotion-Tasks-TC)
- all releaseduty related documentation has been moved out of the wiki under [warrior's](https://github.com/mozilla-releng/releasewarrior-2.0) `docs` subfolder.

### Changed
- in-tree release notifications going away in favor of native taskcluster notifications. pulse-notify is to be retired whenever we kill esr52

## During 58.0 >= 2017-11-15

### Added
- the use of the new [releasewarrior](https://github.com/mozilla-releng/releasewarrior-2.0)

### Changed
- old how-tos are now gathered under one roof in releasewarrior-2.0/old-howtos[releasewarrior-2.0/old-how-tos](https://github.com/mozilla-releng/releasewarrior-2.0/tree/master/old-how-tos) but they are gradually being migrated to the [wiki](https://github.com/mozilla-releng/releasewarrior-2.0/wiki) which becomes the single source of truth
- authentication method for [taskcluster-cli](https://github.com/taskcluster/taskcluster-cli#installation) changed. If you are upgrading from an older version of taskcluster-cli, you may have to remove the `${HOME}/.config/taskcluster.yml` file to work with the new authentication method.

### Removed
- dropped support for old [releasewarrior](https://github.com/mozilla/releasewarrior/)
- dropped the need for QE signoffs in Balrog

## During 57.0 >= 2017-09-27

### Added
- a merge day instance has been added to ease the handover during mergedays but also for speed and reliability. More on this [here](https://github.com/mozilla-releng/releasewarrior-2.0/wiki/Merge-Duty). When connecting  to the merge day instance, keep in mind to ensure its environment is clean and ready for use
- simplified documentation for mid-betas and release checklists. If not already, duplicate an existing sheet in this [google docs checklist](https://docs.google.com/spreadsheets/d/1hhYtmyLc0GEk_NaK45KjRvhyppw7s7YSpC9xudaQZgo/edit#gid=1158959417) and clear out the status that was carried over from the previous release.

### Changed
- mergeduty dates shifted. We now merge `beta` to `release` and `cetral` to `beta` in the same day, keeping a relbranch for `beta` and hold `central` from version bump until before the release.
- because of 57 and the aforementioned mergeduty change, *the exception becomes rule* so that for each new beta cycle X, we have X.0b1 and X.b2 **just** for `Devedition`, while `Firefox` starts at X.b3

### Removed
- dropped support for [tctalker](https://github.com/mozilla/tctalker) and solely rely on [taskcluster-cli](https://github.com/taskcluster/taskcluster-cli). More on its installation [here](https://github.com/taskcluster/taskcluster-cli#installation)
