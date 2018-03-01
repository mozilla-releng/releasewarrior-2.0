## Perform a manual reconfig

A note on reconfigs. If you land any changes to [buildbotcustom](http://hg.mozilla.org/build/buildbotcustom/) or [buildbot-configs](https://hg.mozilla.org/build/buildbot-configs/) repos and want them in production, you'd need a reconfig.
In order to do that, there are a couple of steps needed:

1. Push your changes to `default` branch (can be to either of the two repos if to both if you need to change both)
1. Dump and complete the contents of this file under `~/merge_duty/reconfig.source.sh` with your own credentials
```sh
# Needed if updating wiki - note the wiki does *not* use your LDAP credentials...
export WIKI_USERNAME='Joe Doe'
export WIKI_PASSWORD='********'
```
No need to define Bugzilla integration anymore. Ever since Bugzilla turned on the 2FA, the auth has been troublous so we're not using it anymore for reconfigs. Hence the use of `-b` when calling the script, below.
1. GPG encrypt the file to `reconfig.source.sh.gpg`, so you are the only user to be able to read your credentials.
1. Securely delete the plain text file: `shred --iterations=7 --remove 'reconfig.source.sh'`
1. Run reconfig. This will:
   * clone locally and merge `default` to `production` for [buildbotcustom](http://hg.mozilla.org/build/buildbotcustom/)
   * clone and merge `default` to `production` for [buildbot-configs](https://hg.mozilla.org/build/buildbot-configs/)
   * perform a forced reconfig
   * update wikiwith details about date/time of the reconfig


```sh
now="$(date +'%d-%m-%Y')"
cd ~/merge_duty
# create a temporary directory where all the files and clones are downloaded
# (optional if not having it already)
hg clone http://hg.mozilla.org/build/tools/
cd tools/buildfarm/maintenance/
bash end_to_end_reconfig.sh -b -w <(gpg -d ~/merge_duty/reconfig.source.sh.gpg) -r "$now"   # A folder with the current date will be created
```
:warning: You may be prompted for your gpg key to decrypt the file, but end_to_end_reconfig.sh won't wait. Ensure your password is cached.

