

# Requirements

* All steps followed from Day1 documentation
* Ability to run the `release` command and find the task group inspector URLs for releases in flight.

# Actions for Desktop related releases

## Summary

1. Push artifacts to releases directory (also known as mirrors / CDN)
2. Obtain sign-offs for changes
3. Publish the release
4. Post-release steps

Instructions vary slightly depending on the type of release, so please be careful when following the instructions.

## Notes and Background

* `-cdntest` and `-localtest` channels serve releases from the releases directory (mirrors or CDN) or candidates directory depending on the release and channel. They are testing channels used before we serve from the _real_ update channel, but they use the _actual files_ that will be served once a release is published.
* We should notify release-signoff once updates are available on the ${branch}-{cdntest,localtest} channel because we don't have taskcluster email notifications yet.
