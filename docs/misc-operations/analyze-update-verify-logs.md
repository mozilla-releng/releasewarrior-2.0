# When?

When update verify tasks fail it is your responsibility as releaseduty to analyze them and determine whether or not any action needs to be taken for any differences found.

# How? 

Update verify tasks that have failed should have a "diff-summary.log" in their artifacts. This file shows you all of the differences found for each update tested. In the diffs, `source` is an older version Firefox that a MAR file from the current release has been applied to, and `target` is the full installer for the current release.

Here's an example of a very alarming difference:
```
Found diffs for complete update from https://aus5.mozilla.org/update/3/Firefox/59.0/20180215111455/WINNT_x86-msvc/en-US/beta-localtest/default/default/default/update.xml?force=1

Files source/bin/xul.dll and target/bin/xul.dll differ
```

In the above log, `xul.dll' is shown to be different between an applied MAR and a full installer. If we were to ship a release with a difference like this, partial MARs would fail to apply for many users in the _next_ release. Usually a case like this represents an issue in the build system or release automation, and requires a rebuild. If you're not sure how to proceed, ask for help.

If no diff-summary.log is attached to the Task something more serious went wrong. You will need to have a look at live.log to investigate.

# Known differences

There are a few known cases where diffs are expected, and ignorable.

## Beta channel/ACCEPTED_MAR_CHANNEL_IDS during secondary update verify in RCs

```
Found diffs for complete update from https://aus5.mozilla.org/update/3/Firefox/59.0/20180215111455/Linux_x86-gcc3/en-US/beta-localtest/default/default/default/update.xml?force=1
diff -r source/firefox/defaults/pref/channel-prefs.js target/firefox/defaults/pref/channel-prefs.js
5c5
< pref("app.update.channel", "beta");
---
> pref("app.update.channel", "release");
diff -r source/firefox/update-settings.ini target/firefox/update-settings.ini
5c5
< ACCEPTED_MAR_CHANNEL_IDS=firefox-mozilla-beta,firefox-mozilla-release
---
> ACCEPTED_MAR_CHANNEL_IDS=firefox-mozilla-release
```

The differences shown tell us that when a user is running Beta and applies an RC MAR file, they end up with the same Firefox that a fresh RC install does, except they maintain their Beta update channel and ACCEPTED_MAR_CHANNEL_IDS. This is expected and OK (if we didn't have this diff, it would mean that we switched Beta users to the release channel!).

## channel-prefs.js comment changes

```
diff -r source/Firefox.app/Contents/Resources/defaults/pref/channel-prefs.js target/Firefox.app/Contents/Resources/defaults/pref/channel-prefs.js^M
5d4^M
< //@line 6 "/builds/worker/workspace/build/src/browser/app/profile/channel-prefs.js"^M
```

channel-prefs.js contains comments that have the full path to a file in the build directory. If the build directory changes between a previous version and the latest version, this will show up as a difference in update verify. Being a comment change, this is totally ignorable.

Newer versions of Firefox have removed this comment from channel-prefs.js, so this difference should go away entirely after the next round of watersheds.
