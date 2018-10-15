
## Background

When a new release goes to build, we need to track its progress in releasewarrior to ensure the right things happen at the right time. Following these instructions adds a release to releasewarrior.

## Prerequisites
- [releasewarrior-2.0](https://github.com/mozilla-releng/releasewarrior-2.0#installing) installed and working, with write access to that repository.


## When to perform these steps

The release-signoff mailing list will receive a message alerting us to a new build being created in ship-it. Here is an example email:

    
    subject: [desktop] Build of Firefox-58.0b5-build1

    A new build has been submitted through ship-it:

    Commit: https://hg.mozilla.org/releases/mozilla-beta/rev/f155e109bb419696beb422b5afbfd7299b2b2500
    Task group: https://tools.taskcluster.net/push-inspector/#/C8umMF6qSKy3X1tntYk1pA
    Locales: https://ship-it.mozilla.org/releases/Firefox-58.0b5-build1/l10n (requires VPN access)

    Created by release manager @ mozilla.com
    Started by release manager @ mozilla.com

    Comparing Mercurial tag FIREFOX_58_0b4_RELEASE to FIREFOX_58_0b5_RELEASE:
    Bugs since previous changeset: https://mzl.la/2j8Tbfe
    Full Mercurial changelog: https://hg.mozilla.org/releases/mozilla-beta/pushloghtml?
    fromchange=FIREFOX_58_0b4_RELEASE&tochange=f155e109bb419696beb422b5afbfd7299b2b2500&full=1

## What to do

1. Get the product, version and task group ID from the email. In the example above these are:
    ```sh
    product=firefox
    version=58.0b5 # Remove any -build suffix.
    graphid="C8umMF6qSKy3X1tntYk1pA"
    ```
1. Ensure releasewarrior is working by typing: `release status`. You may need to go to the `releasewarrior-data` directory and run `git pull`
1. If `release status` does not show the release in the 'UPCOMING RELEASES' section, you will need to track it:
    ```sh
    release track ${product} ${version}
    ```
1. Create a new build in releasewarrior:
    ```sh
    release newbuild --graphid ${graphid} ${product} ${version} 
    ```
1. Tell releasewarrior about the promotion graph id:
    ```sh
    release graphid --phase promote ${graphid} ${product} ${version} 
    ```
1. Change to the `releasewarrior-data` repository and push changes
    ```sh
    cd ../releasewarrior-data # Assuming both are cloned into the same parent
    git push
    ```
1. No email reply is necessary when creating a new build.

## Example of success

```
$ release newbuild --graphid C8umMF6qSKy3X1tntYk1pA firefox 58.0b5
INFO: ensuring releasewarrior repo is up to date and in sync with origin
INFO: generating wiki from template and config
INFO: writing to data file: /Users/sfraser/github/mozilla-releng/releasewarrior-data/inflight/firefox/firefox-beta-58.0b5.json
INFO: writing to wiki file: /Users/sfraser/github/mozilla-releng/releasewarrior-data/inflight/firefox/firefox-beta-58.0b5.md
INFO: writing to corsica file: /Users/sfraser/github/mozilla-releng/releasewarrior-data/index.html
INFO: committing changes with message: firefox 58.0b5 - new buildnum started. 
```

## Troubleshooting

Symptom:
```
$ release newbuild --graphid d4EXAosbTPuxWoSHOGkdXQ devedition 58.0b5 
CRITICAL: data file was expected to exist in either upcoming or inflight path: /Users/sfraser/github/mozilla-releng/releasewarrior-data/upcoming/devedition/devedition-devedition-58.0b5.json, /Users/sfraser/github/mozilla-releng/releasewarrior-data/inflight/devedition/devedition-devedition-58.0b5.json
INFO: ensuring releasewarrior repo is up to date and in sync with origin
```
Cause:
You have not tracked this release. Track it with `release track ${product} ${version}` before creating a new build for it.

Symptom:
```
$ release track devedition 58.0b5 
CRITICAL: data file already exists in one of the following paths: /Users/sfraser/github/mozilla-releng/releasewarrior-data/upcoming/devedition/devedition-devedition-58.0b5.json, /Users/sfraser/github/mozilla-releng/releasewarrior-data/inflight/devedition/devedition-devedition-58.0b5.json
INFO: ensuring releasewarrior repo is up to date and in sync with origin
```
Cause: You have already tracked this release. Continue with the next step.
