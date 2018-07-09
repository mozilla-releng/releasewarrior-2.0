# Addon Submission Pipeline
## Terminology:

* listed - Addon is viewable on AMO by end-users. 
* unlisted - Addon is available only to the addon uploader for download, and servable
  outside of AMO.
* Language Pack - A translation pack for Gecko strings bundled as an addon.

## Background

Langauge packs now need to be signed (as of Gecko 60.1esr/61.0) to be run inside of
Firefox. In order to do that our release process submits every language pack to AMO
for signing.

### Restrictions

In order to achieve this we have to contend with a few current restrictions of AMO
itself, as well as Firefox the product, and correlate them with our release process.

* Version number of the language pack is baked into the language pack itself.
* AMO only accepts one copy of each language pack for each specific version (a
  new upload needs a new version)
* AMO does not support "promoting" an upload to `listed` if it was previously
  `unlisted`
* AMO needs the first `listed` version of an addon to be submitted via the admin web
  interface manually, the first time.

### Process

* Firefox, for every code checkin, builds an English (US) copy that is suitable for
  shipping to end users, as part of this build we generate the en-US language pack.
* Once Release Management indicates we want to build a release, we kickoff the 'promote'
  phase of the release process, which starts the Localized Repackages, which generate
  each langauges language pack.
* The language packs get sent off to AMO on an addon submission task, this task
  submits and retries while it waits for AMO to sign the langpacks. Timing
  out (with a signal to retry the task) if needed.
* The Addon Submission task is idempotent, so if a given langpack version is uploaded
  it will retrieve the same upload on subsequent calls (and resubmit any uploads
  which failed)
* The Addon Submission task exposes the signed langpacks as task artifacts.
* Beetmover moves the language packs to the release folder, allowing them to be
  easily downloaded by users not on AMO.

## How To...
### How to handle New Languages for Release

* Once the promote phase is kicked off, any new language packs will fail the addon
  submission task, and require human intervention.
* Go to the failed task, and look for its dependency on a nightly-l10n task,
  locally download the .xpi for the language in question.
* Decrypt the AMO user/pass from our private repo, and in Firefox log into
  AMO's Developer Hub (Private Browsing Mode recommended)
  [Screenshots [1] [2] [3] and [4]]
* Once there click over to `My Addons` and sort the list by "Created"
  (this brings the newest created addons to the top of the list)
  [Screenshots [5] [6] and [7]]
* Select the relevant language(s) to go to the extension detail page. [Screenshot 8]
* Select to Upload a new version, to see the following page [Screenshot 9]
* **IMPORTANT** On this page be SURE TO CLICK **CHANGE** to make the extension listed
  follow prompts to alter the input [Screenshots [10], [11], and [12]]
* Finally upload the .xpi with "Select a file..." and then you'll see some results
  [Screenshots [13] and [14]]
* Continue
* You'll need to fill out a few required fields [Screenshots [15], [16] and [17]]
  * Summary can be simple "Language pack for <locale code>"
  * License is to be set to MPL 2.0
  * Submit this page with no further changes
* In the slim chance you get hit with AMO's restriction of path length, feel free
  to edit it in an attempt to be descriptive but within the limits, this is purely
  convenience. [Screenshot [18], [19]]
* Success! [Screenshot [20]]
* Go back and rerun the addon submission task that failed, to unblock the release.

### What if I don't do the important step in the manual process above?

If you forget to do the **CHANGE** to make the addon listed when manually uploading it
above. The release can still be unblocked, AMO will see the requests and see "hey we have
that version" and hand the release process back the unlisted version. **HOWEVER** this
means, the new language pack will not be listed for this version of Firefox.

In order to make it listed we need a new build number (on a new buildid), relman may be
ok with waiting for another RC, or they may be ok letting the new locale stay off AMO for
the release cycle (until a dot release), this is mostly a value judgement on which path
forward.

## Screenshots relevant to above

