# Widevine updates

Widevine is a system addon allowing Firefox user to read DRM'd content (like Netflix). We provide updates via Balrog.  

## When

The request comes from the media team. They usually file a bug like this one.  

Sometimes updates must be done because Google (the owner of Widevine) deprecates a version that still may be used by a supported Firefox version (e.g.: Firefox ESR).

## How

### Ensure what Firefox version is able to run the new version

:warning: There are 2 types of patches the Media team makes:

1. The actual patch to make Firefox compatible with the new API (for example: [bug 1420836](https://bugzilla.mozilla.org/show_bug.cgi?id=1420836)). This kind of patch must happen **before** the balrog rule is set.
1. Another patch that updates the fallback downloader (like [bug 1479579](https://bugzilla.mozilla.org/show_bug.cgi?id=1479579)). This kind of patch can be landed **after** the balrog rule is set

Take a look at Widevine version numbers to determine whether Firefox needs to be updated.


#### Old schema (< 1.4.9.X)

For instance: 1.4.9.1088.

| Digit | Name         | Notes                                                             |
|-------|--------------|-------------------------------------------------------------------|
| 1     | Major        | It has always been 1, so far                                      |
| 4     | Module       | Significant changes must happen on the Firefox side               |
| 9     | Interface    | If this number changes, some Firefox internals must be changed    |
| 1088  | Revision     | This number keeps increasing even if the other numbers got bumped |

If the API level (or higher) is bumped, please check with the Media team what Firefox is able to run this Widevine.

#### New schema (> 1.4.9.x)

For instance: TBD

| Digit | Name         | Notes                                                             |
|-------|--------------|-------------------------------------------------------------------|
|       | Major        | See old schema                                                    |
|       | Interface    | See old schema                                                    |
|       | Revision     | See old schema                                                    |
|       | ?            | TDB                                                               |


### Create the blob

// TODO 

### Create the balrog rule

Unlike Firefox updates, Widevine ones all happen in the same channel (except for the nightlytest, the internal testing channel). This means users are given a new widevine based on their Firefox version. For instance: if we provide a new widevine to 62.0 at the time 62.0b15 ships, then users with 62.0b1-b14 will also get this version. Make sure with the media team these betas are compatible! In the case it's not, please remind Firefox doesn't send which beta it's on to Balrog. You have to filter out based on the version **and** the buildID (the buildID alone doesn't work if a 61 dot release happens afterwards).

In the end, a rule looks that filters on both like this one: ![Balrog rule](/docs/misc-operations/widevine-balrog-rule.png?raw=true)

### Testing 

You can use the nightlytest channel to test changes before sending them to production. A widevine request to balrog is like this one: https://aus5.mozilla.org/update/3/GMP/62.0/20180802174131/WINNT_x86_64-msvc-x64/en-US/nightlytest/default/default/default/update.xml

:warning: Reminder: In this URL, 62.0 can't be 62.0b14. Even though it works from Balrog's point of view, Firefox doesn't send this piece of data.
