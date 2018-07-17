# Staging and merging instance

There is an AWS instance to run staging and merging instances so that we are fewer hops away from the hg repos. 

To access it, start the "mergeday1" instance in us-west-2 from the AWS console. You should be able to access it with:
 ssh -A buildduty@mergeday1.srv.releng.usw2.mozilla.com

It's important that you connect with agent forwarding enabled, and directly as buildduty to ensure that ssh connections to hg.mozilla.org will work.
