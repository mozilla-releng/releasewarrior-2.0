# Staging and merging instance

There is an AWS instance to run staging and merging instances so that we are fewer hops away from the hg repos.

To access it, you can either
1. Create an new instance with the AMI named ```Mozilla release staging/merge machine```.  I used a M3.large instance with 32 gb space added.
2. Use the existing instance named "Mozilla release staging/merge machine" in use1. See access and setup instructions below for using  existing instance.

note: There is also a Dockerfile attached to <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1400015">1400015</a> that can be used to install the requirements for this machine, however, there is still some work to be done to address the credentials issue.

### Access and setup existing merge instance

1. the instance may be stopped. Use the aws web console and search for Mozilla release staging/merge instance (currently i-0a18b39a0efc11658). Start the instance from the UI actions
2. Decrypt the pem key (keys/aws-staging-mergeday.pem.gpg) from the usual location so you can ssh to the host, setup ssh forwarding and hg so you can push to hg.m.o, and clear up unneeded disk space. See below

```bash
$ # copy the public DNS from AWS console and connect through vpn+jumphost using the `ubuntu` user : e.g. ubuntu@ec2-54-83-67-250.compute-1.amazonaws.com
$ # verify you can ssh. Then copy your mozilla ssh *public* key to the remote merge instance
$ scp -i aws-staging-mergeday.pem ~/.ssh/${YOUR_MOZILLA_SSH_PUB} ubuntu@${DNS_OF_MERGE_INSTANCE}:~/.ssh/${USER}_rsa.pub
$ ssh -i aws-staging-mergeday.pem ubuntu@${DNS_OF_MERGE_INSTANCE}
$ chmod 600 ~/.ssh/${USER}_rsa.pub
$ vim ~/.ssh/config # comment out previous users and add you. e.g.
$ cat ~/.ssh/config
Host hg.mozilla.org git.mozilla.org
    User jlund@mozilla.com
    IdentityFile ~/.ssh/jlund_rsa.pub
    # User sfraser@gmail.com
    # IdentityFile ~/.ssh/sfraser_rsa.pub
    Compression yes
    ServerAliveInterval 300
$ vim ~/.hgrc # add your public key as the key to use for hg. e.g.
$ cat ~/.hgrc
[ui]
# ssh = ssh -C -i ~/.ssh/sfraser_rsa.pub
ssh = ssh -C -i ~/.ssh/jlund_rsa.pub

[extensions]
strip =
$ df -h  # check disk space. You will need at least 25gb on /
$ rm -rf ~/merge_day_57.0 # if needed, you can clear previous cycle migrations that were completed, like so
$ mkdir ~/merge_day_${RELEASE_VERSION_FOR_CYCLE} # create a new work dir. This will be used for all migrations in the current cycle
```
