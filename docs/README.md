
# ReleaseWarrior and ReleaseDuty

_ReleaseDuty_ is a duty cycle where an engineer is responsible for operational
and monitoring tasks related to releasing the new versions of Mozilla's products.

_ReleaseWarrior_ is a tool to help the on-duty engineers perform those tasks,
and to keep track of release progress and issues. It is the single source of truth
where the coordination happens among the releaseduty squirrels.

## Table of contents

This folder gathers all releaseduty documentation under one single umbrella. The structure is as follows:

[Overview](#Overview)
[Release Duties](#Release Duties)
[CHANGELOG](#TODO) - to track large changes to the workflow and tools of releaseduty
[balrog](#TODO) - to track all Balrog related information and understanding
[day1](#TODO) - day1 documentation for all releng folks starting/resuming their releaseduty cycle
[development](#TODO) - documentation for various related pieces that are still under development (e.g. tcmigration or Ship It v2. stuff)
[mergeduty](#TODO) - single point of truth for all that matters during mergeduty processes
[misc-operations](#TODO) - various other pieces of documentation that come into handy while releaseduty
[release-promotion](#TODO) - to track the bread and butter of releaseduty for all products and platforms
[signing](#TODO) - to track any related signing duties that releaseduty must perform occasionally

## Overview

Two people are assigned to ReleaseDuty every six weeks, preferably in different timezones to extend
available coverage.  There are specific days in a cycle when set tasks must be
done, such as creating a beta or release candidate, and other unscheduled work
that depends on issues that need fixing, and special requirements that specific
release might have.

# Release Duties

* Performing operational tasks for incoming Nightly, DevEdition, Beta, ESR, Release Candidate and final releases
* Merging repositories to create new beta, release candidates, releases and extended support releases.
* Coordinating with other teams, such as Release Management, Quality Engineering, Sheriffs, and other developers
* Fixing and improving the release automation, including both tools and processes
* Maintaining a logbook of issues and progress using releasewarrior.
* Arranging event post-mortems, if required.

The individual accountable for a release is known as the 'release owner',
and this is usually a specific member of Release Management.
Details about release owners and people on release duty can be found at
<https://wiki.mozilla.org/Release_Management/Release_owners>

Known regular meetings are the Channel Meeting, every Tuesday and Thursday, and the ReleaseDuty standup on Mondays.
