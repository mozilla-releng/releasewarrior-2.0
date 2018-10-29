### Access Bouncer

Ensure you have access to Bouncer. You may need an account. Ask rail/mtabara/nthomas for more details if you have never done this before.

1. Create a SOCKS proxy on port `10000` using SSH via one of the masters (this should move to a jumphost after bug 1484055):
```
ssh -ND 10000  buildbot-master01.bb.releng.use1.mozilla.com
```
1. Setup Firefox (`Firefox` -> `Preferences` -> `Network Proxy` -> `Settings`) to use it like this:
![this](/docs/misc-operations/media/bouncer_setup_firefox.png?raw=true)
1. Navigate to [Bouncer](https://bounceradmin.mozilla.com/) to make sure you can login
