# Releasewarrior 2.0

Your assistant while on Release Duty

![squirrel spartan](https://pbs.twimg.com/profile_images/571907614906310658/HDB_I-Nr.jpeg)

In the spirit of [taskwarrior](https://taskwarrior.org/), releasewarrior is a tool that manages and provides a checklist for human decision tasks with releases in flight while providing documentation and troubleshooting for each task.

Rather than manually managing a wiki of releases, releasewarrior provides a set of commands to do this work for you.

## Installing

Get a copy of releasewarrior
```
git clone git@github.com:mozilla-releng/releasewarrior-2.0.git && cd releasewarrior-2.0
mkvirtualenv --python=/path/to/python3 releasewarrior
python setup.py develop
```
Using the develop target ensures that you get code updates along with data when pulling in changes.

## Configuring
The minimal configuration required is the absolute local path of the releasewarrior-data repository.

```
# clone data repo somewhere on your system
git clone git@github.com:mozilla-releng/releasewarrior-data.git
cp releasewarrior/configs/config_example.yaml releasewarrior/configs/config.yaml
# edit config.yaml
#   releasewarrior_data_repo: /path/to/repo/releasewarrior-data
```


## Common terminology

- `gtb`: Go to build
- `buildnum`: buildnumber

## Quick start

`releasewarrior` is made up of a number of subcommands. `status`, `track`, `newbuild`, `prereq`, `issue`, and `sync`.

At its core, releasewarrior tracks three todo lists:
- `prereq` - prerequite "Go to build" (GTB) tasks
- `task` - Expected operational tasks for a release in-flight
- `issue` - Issues/Problems that have been addressed, or need to be worked on, for a release in-flight.

The usage for resolving and adding these lists are identical:

```
# add an item to a list
release {prereq, task, issue} $product $version # uses CLI inputs to add
# resolve a list item
release {prereq, task, issue} $product $version --resolve $id
```

Aside from the readonly `status` command, every command does the following:

1. Updates the data file:  releasewarrior-data/{inflight,upcoming}/fennec-release-17.0.json
2. Wiki file rendered from data:  releasewarrior-data/{inflight,upcoming}/fennec-release-17.0.md
3. Changed files are committed **but not currently pushed**.

**pro tip**: use `release --help` and `release <subcommand> --help`

## More on each subcommand

**note:** unlike previous versions of releasewarrior, the branch is inferred from the product and version. Less typing for you, more validation internally to catch mistakes.

### status

Checks the current state of releases

Usage:

```
release status
```

What happens:

`status` will tell you all of the upcoming releases with prerequisite tasks before gtb as well as current tasks and issues for releases inflight.

Examples:

```
$ release status
INFO: UPCOMING RELEASES...
INFO: ===============================================================================
INFO: Upcoming Release: firefox 57.0b1
INFO: Expected GTB: 2017-11-09
INFO:   Incomplete prerequisites:
INFO:           * ID: 1, deadline: 2017-12-01, bug 123 - bump in tree version manually
INFO:
INFO: INFLIGHT RELEASES...
INFO: ===============================================================================
INFO: RELEASE IN FLIGHT: firefox 57.0 build1 2017-11-08
INFO:   Incomplete human tasks:
INFO:           * ID 6  - check with marketing re: mobile promotion wnp
INFO:           * ID 7 (alias: publish) - publish release tasks
INFO:           * ID 8 (alias: signoff) - signoff in Balrog
INFO:   Unresolved issues:
INFO: ===============================================================================
INFO: RELEASE IN FLIGHT: firefox 57.0b2 build2 2017-11-06
INFO: Graph 1: https://tools.taskcluster.net/task-group-inspector/#/123
INFO: Graph 2: https://tools.taskcluster.net/task-group-inspector/#/456
INFO:   Incomplete human tasks:
INFO:           * ID 2 (alias: publish) - publish release tasks
INFO:           * ID 3 (alias: signoff) - signoff in Balrog
INFO:   Unresolved issues:
INFO:           * ID: 1 bug: none - update verify perma failing. investigating
INFO:           * ID: 2 bug: 999 - beetmover l10n tasks missing config key "dest-location"
```


### track

Start tracking an upcoming release. This is a required command before `newbuild`, below.

Usage:

`release track $PRODUCT $VERSION --date YYYY-MM-DD`

`release track $PRODUCT $VERSION  # --date defaults to today`

What it does:

- Creates and commits json and markdown files in releasewarrior-data/upcoming/
- Release is primed to either "gtb" or add/resolve `prereq`uisites

Examples:

```
$ release track fennec 17.0b1 --date 2017-11-02
```


### prereq

Add or resolve a prerequisite task for an upcoming (tracked) release.

Usage:

```
# Create a prerequisite
release prereq $PRODUCT $VERSION
# Resolve an existing prerequisite
release prereq $PRODUCT $VERSION --resolve $prerequisite_id
```

What it does:

Prerequisites are tasks that must be completed before go-to-build. They do not carry over as part of post gtb.

`prereq` when run without options will add a prereq by asking for details through CLI inputs. Examples of both below.

**note:** this replaces the previous FUTURE/ style from releasewarrior 1.

Examples:

```
# add a prereq
$ release prereq firefox 57.0rc
INFO: ensuring releasewarrior repo is up to date and in sync with upstream
Bug number if exists [none]: 123
Description of prerequisite task: bump in tree version manually
When does this have to be completed [2017-11-09]: 2017-12-01
```

```
# resolve a prereq
$ release status  # list prereqs and IDs
$ release prereq firefox 57.0rc --resolve $prerequisite_id
```


### newbuild

Marking gtb for a tracked release, or start a new build number for an existing build.

Usage:

`release newbuild $PRODUCT $VERSION --graphid $graph1 --graphid $graph2`


What it does:

If this is first gtb (buildnum1), the data and wiki files are moved to: releasewarrior-data/inflight/

If this release is already in flight, the data file's most recent buildnum
marked as aborted, any previous unresolved issues are carried forward to new
buildnum. This means it is safe to use `release newbuild` for a product and
version that are already listed, it will just start a new build number.


Example:

```
$ release newbuild firefox release-rc 15.0 --graphid 1234
```

**note:** if you forget to include all the graphids, manually add them to the json files and run `release sync $PRODUCT $VERSION`


### task

Add or resolve a human task for an inflight release

Usage:

`release task $PRODUCT $VERSION --resolve $task_id_or_alias`

What it does:

Tasks are tracked work that must be completed during an in-flight release. When you start a new buildnum, the previous human tasks are reset to unresolved and carried over to next buildnum.

`task` when run without options will add a task by asking for details through CLI inputs. Examples of both below.

Examples:

```
# add a task
$ release task firefox 57.0b2
INFO: ensuring releasewarrior repo is up to date and in sync with upstream
INFO: Current existing inflight tasks:
INFO: ID: 1 - submit to Shipit
INFO: ID: 2 - publish release tasks
INFO: ID: 3 - signoff in Balrog
After which existing task should this new task be run? Use ID [1]: 2
Description of the inflight task: setup wnp
Docs for this? Use a URL if possible []: github.com/releasewarrior/how-tos/wnp.md
```

```
# resolve a task
$ release status  # list human_task warrior IDs and aliases
$ release task firefox 57.0rc --resolve $task_id_or_alias
```


### issue

Add or resolve an issue for an inflight release

Usage:

```
release issue $PRODUCT $VERSION
release issue $PRODUCT $VERSION --resolve $issue_id
```

What it does:

Issues are tracked failures or problems while a release is inflight. When you start a new buildnum, the previous unresolved issues are carried over to next buildnum.
`issue` when run without options will add a task by asking for details through CLI inputs. Examples of both below.

Examples:

```
# add an issue
$ release issue firefox 57.0rc
INFO: ensuring releasewarrior repo is up to date and in sync with upstream
Bug number if exists [none]: 12345
Description of issue: Update verify tests failing bc of release-localtest rule 234
```

```
# resolve an issue
$ release status  # list issue IDs from inflight releases
$ release issue firefox 57.0rc --resolve $issue_id
```



### postmortem

Generate postmortem file for releaseduty weekly meeting

Usage:

```
release postmortem YYYY-MM-DD
```

What it does:

Creates a postmortem file based on completed releases and their unresolved
issues. Archives release files that are completed using the same date will
only append and archive releases as they are updated.

Example:

```
$ release postmortem 2018-01-25
WARNING: No recently completed releases. Nothing to do!
```


### sync

Semi-manually updating releasewarrior

Usage:

```
release sync $PRODUCT $VERSION
```

What it does:

The data is just a json file and changes are tracked by the repository's
revision history, you can always manually update the data and have the tool
re-create the wiki presentation.

Example:

```
$ vim releasewarrior-data/inflight/firefox-esr-27.0esr.json  # change some value
$ release sync firefox 27.0esr
```
