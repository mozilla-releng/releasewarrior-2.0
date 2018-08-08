import re

from git import Repo


def find_upstream_repo(repo, logger, config, pattern_key='upstream_repo_url_pattern',
                       simplified_pattern_key='simplified_repo_url'):
    upstream_repo_url = re.compile(config[pattern_key])
    upstream_repos = [
        repo for repo in repo.remotes if upstream_repo_url.match(repo.url) is not None
    ]
    number_of_repos_found = len(upstream_repos)
    if number_of_repos_found == 0:
        raise Exception('No remote repository pointed to "{}" found!'.format(
            config[simplified_pattern_key]
        ))
    elif number_of_repos_found > 1:
        raise Exception('More than one repository is pointed to "{}". Found repos: {}'.format(
            config[simplified_pattern_key], upstream_repos
        ))

    correct_repo = upstream_repos[0]
    logger.debug('{} is detected as being the remote repository pointed to "{}"'.format(
        correct_repo, config[simplified_pattern_key]
    ))
    return correct_repo


def commit(files, msg, logger, config):
    logger.info("committing changes with message: %s", msg)

    repo = Repo(config['releasewarrior_data_repo'])
    repo.index.add(files)

    if not repo.index.diff("HEAD"):
        logger.fatal("nothing staged for commit. has the data or wiki file changed?")

    commit = repo.index.commit(msg)
    for patch in repo.commit("HEAD~1").diff(commit, create_patch=True):
        logger.debug(patch)


def move(src, dest, logger, config):
    logger.debug("archiving {src} to {dest}", src, dest)
    repo = Repo(config['releasewarrior_data_repo'])
    repo.index.move([src, dest])


def push(logger, config):
    repo = Repo(config['releasewarrior_data_repo'])
    upstream = find_upstream_repo(repo, logger, config)
    logger.info("pushing changes to %s", list(upstream.urls)[0])
    push_info = upstream.push(refspec='master:master')
    logger.info("Summary of push: {}".format(push_info[0].summary))


def pull(logger, config):
    repo = Repo(config['releasewarrior_data_repo'])
    upstream = find_upstream_repo(repo, logger, config)
    logger.info("pulling changes from %s", list(upstream.urls)[0])
    fetch_info = upstream.pull(refspec='master', ff_only=True)
    logger.info("Summary of pull: {}".format(fetch_info[0].note))
