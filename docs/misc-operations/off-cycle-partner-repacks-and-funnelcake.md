Original docs are [here](https://mana.mozilla.org/wiki/display/RelEng/Partner+Repack+Creation).

# Background

We repackage Firefox for partners. Occasionally we'll have a new study (funnelcake) or a new partner or partner config that happens after a release is built, but before the next release is scheduled to be built, and we need to repack that partner off-cycle.

# When?

We'll get a bug for a new partner repack or funnelcake, in the Release Engineering :: Custom Release Requests component in Bugzilla.

These will need to run against a previously-promoted release.

**Warning:** Adding a new partner, or partner sub-config, can cause alarming failures for an in-progress Firefox release, but does not actually block the release. The problem usually occurs in the push or ship phase, where a new partner config since the previous phase causes extra partner tasks in the new graph and these fail. A resolution for this is tracked in [Bug 1496530](https://bugzilla.mozilla.org/show_bug.cgi?id=1496530), but in the meantime you can either delay the partner configuration change until the release is complete, or inform releaseduty to ignore the extra tasks.

# How?

These are the steps on how to trigger the repack/signing/repackage/repackage-signing/beetmover tasks for partner repacks and funnelcakes. We sometimes still have additional steps afterwards, until we automate everything.

## Preparation

1. Clone [braindump](https://hg.mozilla.org/build/braindump/) and set up a virtualenv with requests and pyyaml.
    ```
    hg clone https://hg.mozilla.org/build/braindump/
    cd braindump/releases-related
    python3 -m venv ./venv
    . venv/bin/activate
    pip install requests pyyaml
    ```
    or update your existing clone.

1. Determine the version and build number we're going to use. This is generally the most recent Firefox release, but might be ESR or beta.

1. Determine the partner name - this will be usually be given in the bug. There should be a repo at `https://github.com/mozilla-partners/<name>/` - you may have to figure out the parent of a sub-config.

    Until [Bug 1530231](https://bugzilla.mozilla.org/show_bug.cgi?id=1530231) is resolved we support a single, top-level config, eg `funnelcake`, but not `funnelcakeNNN` or `yandex,ironsource`. If more than one partner is needed create separate graphs using separate custom actions.

1. Generate the action input, eg
    ```
    ./off-cycle-parter-respin.py -v 65.0.2 -b release -p seznam
    ```

1. Load the Treeherder link given near the bottom of the output. Make sure you are logged into Treeherder. In the top-right corner of the UI for the push locate the small triangle, select `Custom Push Action...` from the dropdown list.

1. From the `Action` dropdown select `Release Promotion`.

1. Paste action input the script has generated into the `Payload` box, click the `Trigger` button.

1. Treeherder will display a link to the Taskcluster task for a few seconds, otherwise look for the `firefox_promote_partners` job in the  `Gecko Decision Task` line. The graphs are small enough they can be monitored in a browser tab, but you can also use `braindump//taskcluster/graph-progress.sh`.

1. When the graph is done, resolve the bug. If there are tasks in the graph matching `release-partner-repack-beetmover-*-public`, add the link to the candidates directory which the `off-cycle-parter-respin.py` script provides; otherwise the repacks will be available in the partners portal.

## Additional steps

For funnelcake, we still need to deal with bouncer. See the bouncer-related docs [here](https://mana.mozilla.org/wiki/display/RelEng/Partner+Repack+Creation#PartnerRepackCreation-Funnelcakebuilds).

# Future

In the future, we can use [action hooks](https://bugzilla.mozilla.org/show_bug.cgi?id=1415868) for this. In addition, we can do things like add bouncer tasks in a shipping phase that allow us to automate the final remaining manual steps.

Ideally, ship-it v2 will be the forward-facing UI instead of hooks or an ssh shell. This is tracked in [bug 1530859](https://bugzilla.mozilla.org/show_bug.cgi?id=1530859).
