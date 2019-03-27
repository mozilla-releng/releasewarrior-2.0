# measure-ci release-scanner.py

release-scanner.py is not meant to be used as a lambda function and should be run manually weekly by releaseduty.

## Steps

1. `git clone git@github.com:mozilla-releng/measuring_ci.git` # checkout measure-ci repo
1. Create a python3 environment for measure-ci
1. install dependencies
    1. `pip install -r requirements/main.in`
    1. `pip install -e git+https://github.com/mozilla-releng/taskhuddler#egg=taskhuddler`
    1. `pip install awscli
1. Set the AWS environment with access keys for the mozilla-releng-metrics S3 bucket and Taskcluster Cost Explorer
    1. You can find the credentials within metrics_keys.txt.gpg in the private repo (⚠️ Have someone add you if you're not alredy there).
    1. In order to set the AWS environment, export the 5 environment variables locally
1. `aws s3 ls s3://mozilla-releng-metrics/measuring_ci/releases/v3/` # verify you have bucket access
1. connect to the VPN
1. Run `python ./releases_scanner.py`
1. Test it worked. If all goes well and you populate the S3 bucket with the latest set of releases, you should be seeing those in the releases.parquet file. Something like:
    1. `import pandas as pd;  pd.read_parquet('s3://mozilla-releng-metrics/measuring_ci/releases/v3/releases.parquet')`
