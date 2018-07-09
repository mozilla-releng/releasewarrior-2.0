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
  [Screenshots [[1]](#01) [[2]](#02) [[3]](#03) and [[4]](#04)]
* Once there click over to `My Addons` and sort the list by "Created"
  (this brings the newest created addons to the top of the list)
  [Screenshots [[5]](#05) [[6]](#06) and [[7]](#07)]
* Select the relevant language(s) to go to the extension detail page. [[Screenshot 8]](#08)
* Select to Upload a new version, to see the following page [[Screenshot 9]](#09)
* **IMPORTANT** On this page be SURE TO CLICK **CHANGE** to make the extension listed
  follow prompts to alter the input [Screenshots [[10]](#10), [[11]](#11), and [[12]](#12)]
* Finally upload the .xpi with "Select a file..." and then you'll see some results
  [Screenshots [[13]](#13) and [[14]](#14)]
* Continue
* You'll need to fill out a few required fields [Screenshots [[15]](#15), [[16]](#16) and [[17]](#17)]
  * Summary can be simple "Language pack for <locale code>"
  * License is to be set to MPL 2.0
  * Submit this page with no further changes
* In the slim chance you get hit with AMO's restriction of path length, feel free
  to edit it in an attempt to be descriptive but within the limits, this is purely
  convenience. [Screenshot [[18]](#18), [[19]](#19)]
* Success! [[Screenshot 20]](#20)
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

### 01
![Login Flow 1](/docs/addons/Screenshot_01.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 02
![Login Flow 2](/docs/addons/Screenshot_02.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 03
![Login Flow 3](/docs/addons/Screenshot_03.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 04
![Login Flow 4](/docs/addons/Screenshot_04.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 05
![Find Langpack Flow 1](/docs/addons/Screenshot_05.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 06
![Find Langpack Flow 2](/docs/addons/Screenshot_06.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 07
![Find Langpack Flow 3](/docs/addons/Screenshot_07.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 08
![Details Page](/docs/addons/Screenshot_08.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 09
![Upload Version Flow 1](/docs/addons/Screenshot_09.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 10
![Upload Version Flow 2](/docs/addons/Screenshot_10.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 11
![Upload Version Flow 3](/docs/addons/Screenshot_11.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 12
![Upload Version Flow 4](/docs/addons/Screenshot_12.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 13
![Upload Version Flow 5](/docs/addons/Screenshot_13.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 14
![Upload Version Flow 6](/docs/addons/Screenshot_14.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 15
![Upload Version Flow 7](/docs/addons/Screenshot_15.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 16
![Upload Version Flow 8](/docs/addons/Screenshot_16.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 17
![Upload Version Flow 9](/docs/addons/Screenshot_17.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 18
![Adjust Human URL 1](/docs/addons/Screenshot_18.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 19
![Adjust Human URL 2](/docs/addons/Screenshot_19.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
### 20
![Success](/docs/addons/Screenshot_20.png?raw=true)
[Back to how to section](#how-to-handle-new-languages-for-release)
