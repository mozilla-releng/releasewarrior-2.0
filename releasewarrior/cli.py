import os
import collections
import json
from copy import deepcopy

import click
import arrow
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from git import Repo

from releasewarrior.helpers import get_config, load_json
from releasewarrior.helpers import get_logger


LOGGER = get_logger()
CONFIG = get_config()

Release = collections.namedtuple('Release', 'product, version, branch, date')
Prerequisite = collections.namedtuple('Prerequisite', 'bug, deadline, description, resolved')


def get_branch(version):
    # TODO
    return "beta"


def validate(release, logger, config):
    # TODO validate version
    # TODO check if local release-pipeline repo is dirty
    # TODO sanity check if local release-pipeline repo is behind upstream
    pass

def validate_track(release, logger, config):
    validate(release, logger, config)
    # TODO ensure release doesn't already exist
    pass

def generate_tracking_data(release, logger, config):
    logger.info("generating data from template and config")

    data_template = os.path.join(
        config['templates_dir'],
        config['templates']["data"][release.product][release.branch]
    )

    data = load_json(data_template)

    data["version"] = release.version
    data["date"] = release.date

    return data

def load_release_data(release, logger, config, build_started=True):
    logger.info("loading current release data")
    release_file = "{}-{}-{}.json".format(release.product, release.branch, release.version)
    release_path = config['releases']["upcoming"][release.product]

    if build_started:
        release_path = config['releases']["inflight"][release.product]

    abs_release_path = os.path.join(
        config['release_pipeline_repo'],
        release_path, release_file
    )
    data = load_json(abs_release_path)

    return data


def generate_wiki(data, release, logger, config):
    logger.info("generating wiki from template and config")

    # TODO convert issues to bugs

    wiki_template = config['templates']["wiki"][release.product][release.branch]

    env = Environment(loader=FileSystemLoader(config['templates_dir']),
                      undefined=StrictUndefined, trim_blocks=True)

    template = env.get_template(wiki_template)
    return template.render(**data)


def write_data(path, content, release, logger, config):
    data_path = os.path.join(
        path, "{}-{}-{}.json".format(release.product, release.branch, release.version)
    )

    logger.info("writing to data file: %s", data_path)
    with open(data_path, 'w') as data_file:
        json.dump(content, data_file, indent=4, sort_keys=True)

    return data_path


def write_wiki(path, content, release, logger, config):
    wiki_path = os.path.join(
        path, "{}-{}-{}.md".format(release.product, release.branch, release.version)
    )

    logger.info("writing to wiki file: %s", wiki_path)
    with open(wiki_path, 'w') as wp:
        wp.write(content)

    return wiki_path


def commit(files, msg, logger, config):
    logger.info("committing changes with message: %s", msg)

    repo = Repo(config['release_pipeline_repo'])
    repo.index.add(files)

    if not repo.index.diff("HEAD"):
        logger.fatal("nothing staged for commit. has the data or wiki file changed?")

    commit = repo.index.commit(msg)
    for patch in repo.commit("HEAD~1").diff(commit, create_patch=True):
        logger.info(patch)


def generate_prereq_from_input():
    bug = click.prompt('Bug number if exists', type=str, default="no bug")
    description = click.prompt('Description of prerequisite task', type=str)
    deadline = click.prompt('When does this have to be completed', type=str,
                            default=arrow.now('US/Pacific').format("YYYY-MM-DD"))
    return Prerequisite(bug, deadline, description, resolved=False)


def update_prereq_tasks(data, resolve):
    data = deepcopy(data)
    if resolve:
        for id in resolve:
            # 0 based index so -1
            id = int(id) - 1
            data["preflight"]["human_tasks"][int(id)]["resolved"] = True
    else:
        # create a new prerequisite task through interactive inputs
        new_prereq = generate_prereq_from_input()
        data["preflight"]["human_tasks"].append(
            {
                "bug": new_prereq.bug, "deadline": new_prereq.deadline,
                "description": new_prereq.description, "resolved": False
            }
        )
    # TODO order by deadline
    return data


@click.group()
def cli():
    """Releasewarrior: helping you keep track of releases in flight

    Each sub command takes a product and version

    versioning:\n
    \tBetas: must have a 'b' within string\n
    \tRelease Candidates: must have a 'rc' within string\n
    \tESRs: must have an 'esr' within string\n
    """
    pass


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--date', help="date of planned GTB. format: YYYY-MM-DD")
def track(product, version, date, logger=LOGGER, config=CONFIG):
    """start tracking an upcoming release.
    """
    # set defaults to options
    date = date or arrow.now('US/Pacific').format("YYYY-MM-DD")
    branch = get_branch(version)

    release = Release(product=product, version=version, branch=branch, date=date)

    upcoming_path = os.path.join(config['release_pipeline_repo'],
                                 config['releases']["upcoming"][release.product])
    commit_msg = "Started tracking of {} {} release. Created wiki and data file".format(product,
                                                                                        version)

    # validate we can exec the command call
    validate_track(release, logger, config)

    # determine release data
    data = generate_tracking_data(release, logger, config)

    # track the release
    wiki = generate_wiki(data, release, logger, config)
    data_file = write_data(upcoming_path, data, release, logger, config)
    wiki_file = write_wiki(upcoming_path, wiki, release, logger, config)
    logger.info(data_file)
    logger.info(wiki_file)
    # commit([data_file, wiki_file], commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True)
def prereq(product, version, resolve, logger=LOGGER, config=CONFIG):
    """add or update a pre requisite (pre gtb) human task
    """
    branch = get_branch(version)

    release = Release(product=product, version=version, branch=branch, date=None)

    upcoming_path = os.path.join(config['release_pipeline_repo'],
                                 config['releases']["upcoming"][release.product])
    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "Updated {} {} prerequisites. {}".format(product, version, resolve_msg)

    # validate we can exec the command call
    validate_track(release, logger, config)

    # determine release data
    data = load_release_data(release, logger, config, build_started=False)
    data = update_prereq_tasks(data, resolve)

    # update the release
    wiki = generate_wiki(data, release, logger, config)
    data_file = write_data(upcoming_path, data, release, logger, config)
    wiki_file = write_wiki(upcoming_path, wiki, release, logger, config)
    logger.info(data_file)
    logger.info(wiki_file)
    # commit([data_file, wiki_file], commit_msg, logger, config)
