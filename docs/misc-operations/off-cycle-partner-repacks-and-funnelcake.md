Original docs are [here](https://mana.mozilla.org/wiki/display/RelEng/Partner+Repack+Creation).

# Background

We repackage Firefox for partners. Occasionally we'll have a new study (funnelcake) or a new partner or partner config that happens after a release is built, but before the next release is scheduled to be built, and we need to repack that partner off-cycle.

# When?

We'll get a bug for a new partner repack or funnelcake.

These will need to run against a previously-promoted release.

# How?

These are the steps on how to trigger the repack/signing/repackage/repackage-signing/beetmover tasks for partner repacks and funnelcakes. We sometimes still have additional steps afterwards, until we automate everything.

## Preparation

1. Determine the version and build number we're going to use. This is generally the most recent Firefox release.

1. Determine the `PROMOTE_TASK_ID` for that release. This is in releasewarrior.

1. Determine the partner list. Until [Bug 1469757](https://bugzilla.mozilla.org/show_bug.cgi?id=1469757) is resolved we only support a single, top-level config, eg `funnelcake`, not `funnelcakeNNN` or `yandex,ironsource`. If more than one partner is needed create separate graphs with different `PARTNER_SUBSET` exports.

1. Determine if these are public or private partners. You can look at the `release_partner_config` in the previous promote task's `public/parameters.yml` artifact. If the partner has `upload_to_candidates` set to `True`, then it's a public partner, and it'll be uploaded to the candidates directory along with the release. Otherwise, it's a private partner, and it'll be uploaded to the partner bucket.

1. Determine the partner build number we're going to use. This is the `v1` or `v2` in the directory path on S3, designed to bypass the CDN cache for public partner builds. We want to increment past the most recent: if we haven't done any off-cycle partner repack creation for this build, we'll use `2`. If we've run off-cycle partner repacks 3 times (using up `2`, `3`, and `4`), then we'd use `5`.

1. Trigger the graph via `trigger_action.py`:

```
ssh buildbot-master01.bb.releng.use1.mozilla.com
sudo su - cltbld
cd /builds/releaserunner3/
source bin/activate
# Set the PROMOTE_TASK_ID
# export PROMOTE_TASK_ID=...
# Set the PARTNER_BUILD_NUM to an int
# export PARTNER_BUILD_NUM=...
# Set the partner subset to a comma-delimited set of partners to repack
# e.g. funnelcake,mozillaonline
# export PARTNER_SUBSET=...
python tools/buildfarm/release/trigger_action.py --action-task-id $PROMOTE_TASK_ID --release-runner-config /builds/releaserunner3/release-runner.yml --action-flavor promote_firefox_partners --partner-build-num $PARTNER_BUILD_NUM --partner-subset $PARTNER_SUBSET
```

1. Follow the graph via [graph-progress](https://hg.mozilla.org/build/braindump/file/tip/taskcluster/graph-progress.sh):

```
# on your own laptop:
cd braindump/taskcluster
PARTNER_TASK_ID=...
# mac
sh graph-progress.sh $PARTNER_TASK_ID && say "off-cycle partner repack done"
# linux
sh graph-progress.sh $PARTNER_TASK_ID && (echo "off-cycle partner repack done" | espeak)
```

## Additional steps

For funnelcake, we still need to deal with bouncer. See the bouncer-related docs [here](https://mana.mozilla.org/wiki/display/RelEng/Partner+Repack+Creation#PartnerRepackCreation-Funnelcakebuilds).

# Future

In the future, we can use [action hooks](https://bugzilla.mozilla.org/show_bug.cgi?id=1415868) for this. In addition, we can do things like add bouncer tasks in a shipping phase that allow us to automate the final remaining manual steps.

Ideally, ship-it v2 will be the forward-facing UI instead of hooks or an ssh shell.
