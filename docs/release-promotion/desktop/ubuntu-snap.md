# (Ubuntu) Snap

Snap is a package format supported by Canonical. It's targeted to support every Linux distribution but it's mainly available on Ubuntu at the moment. We've made Firefox publicly available on https://snapcraft.io/firefox since Firefox 59.0.


## Channels used

The snap store comes with the concept of tracks (à la Google Play Store). For more explanation about them, see https://docs.snapcraft.io/reference/channels. Release promotion automatically uploads to these tracks:

| Brand name              | Track        | Notes |
| ----------------------- | ------------ | ----- |
| Firefox                 | `candidate`  | A human has to manually promote the Snap to the `stable` channel |
| Firefox Beta            | `beta`       |       |
| Firefox Developer Edition | N/A        | Not supported yet |
| Firefox Nightly         | N/A          | Not supported yet |
| Firefox ESR             | `esr` aka `esr/stable` | We plan to use `esr/candidate` whenever the next major ESR version comes out | 


## How to promote a snap to the `stable` channel?

1. Install `snapcraft`. The simplest way is to `docker pull snapcore/snapcraft:stable`, then `docker run -ti snapcore/snapcraft:stable bash`
1. `snapcraft login`. Your credentials will be prompted, your 2FA code too. If it doesn't, 'select "Always" for "Require an authentication device", and click "Update"' like explained [on this page](https://help.ubuntu.com/community/SSO/FAQs/2FA#How_do_I_add_a_new_authentication_device_and_start_using_2-factor_authentication.3F).
1. `snapcraft status firefox` outputs something like:
```
Track    Arch    Channel    Version      Revision
esr      amd64   stable     60.0.2esr-2  98
                 candidate  ^            ^
                 beta       ^            ^
                 edge       ^            ^
latest   amd64   stable     60.0.1-2     89
                 candidate  60.0.2-1     97
                 beta       61.0b14-1    101
                 edge       ^            ^
```
1. Note the revision of the `latest/candidate` (aka `candidate`) snap. In this example: `97`
1. `snapcraft release firefox $REVISION stable`, `$REVISION` being the number found in the previous (e.g.: `97`).

## How to manually push a snap to the store, in case automation failed?

1. Install `snapcraft` and login (see previous paragraph)
1. `snapcraft push target.snap --release $CHANNEL`, `$CHANNEL` being one of `esr`, `candidate`, `beta`.
1. If you forgot `--release` in the previous command, you can still use `snap release [...]` (see previous paragraph) to make the snap available to a channel.
