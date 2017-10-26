import os
import collections
import json

import click
import arrow
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from git import Repo

from releasewarrior.helpers import get_config
from releasewarrior.helpers import get_logger


LOGGER = get_logger()
CONFIG = get_config()

Release = collections.namedtuple('Release', 'product, version, branch, date')


def get_branch(version):
    # TODO
    return "beta"


def validate(release, logger, config):
    # TODO validate version
    # TODO check if local release-pipeline repo is dirty
    # TODO sanity check if local release-pipeline repo is behind upstream
    pass

def validate_create(release, logger, config):
    validate(release, logger, config)
    # TODO ensure release doesn't already exist
    pass


def generate_data(release, logger, config):
    logger.info("generating data from template and config")

    # TODO add support for more powerful issue tracking: owner, status, bug,
    # TODO add support pre gtb human tasks with deadlines
    # TODO add support for ad-hoc human tasks within regular human tasks

    data_template = os.path.join(
        config['templates_dir'],
        config['templates']["data"][release.product][release.branch]
    )

    data = {}

    with open(data_template) as data_template_f:
        data.update(json.load(data_template_f))

    data["version"] = release.version
    data["date"] = release.date

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
def create(product, version, date, logger=LOGGER, config=CONFIG):
    """start tracking an upcoming release.
    """
    # set defaults to options
    if not date:
        now = arrow.now('US/Pacific')
        date = now.format("YYYY-MM-DD")
    branch = get_branch(version)

    release = Release(product=product, version=version, branch=branch, date=date)

    upcoming_path = os.path.join(config['release_pipeline_repo'],
                                 config['releases']["upcoming"][release.product])
    commit_msg = "started tracking of {} {} release. Created wiki and data file".format(product,
                                                                                        version)

    # validate we can exec the command call
    validate_create(release, logger, config)

    # create the release
    data = generate_data(release, logger, config)
    wiki = generate_wiki(data, release, logger, config)
    data_file = write_data(upcoming_path, data, release, logger, config)
    wiki_file = write_wiki(upcoming_path, wiki, release, logger, config)
    logger.info(data_file)
    logger.info(wiki_file)
    # commit([data_file, wiki_file], commit_msg, logger, config)