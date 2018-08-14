import logging
import os
import sys
import json
import re
import yaml
from datetime import datetime
from dateutil.parser import parse
from git import Repo, exc as git_exc

from releasewarrior.git import find_upstream_repo

DEFAULT_CONFIG = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/configs/default_config.yaml"
)

CUSTOM_CONFIG = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/configs/config.yaml"
)

DEFAULT_LOGS_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')), "logs"
)

DEFAULT_TEMPLATES_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/templates"
)

RW_REPO = os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..'))

KNOWN_PRODUCT_PHASES = {
    'devedition': {
        'default': ('promote', 'push', 'ship'),
    },
    'fennec': {
        'release-rc': ('promote', 'ship_rc', 'ship'),
        'default': ('promote', 'ship'),
    },
    'firefox': {
        'release-rc': ('promote_rc', 'ship_rc', 'push', 'ship'),
        'default': ('promote', 'push', 'ship'),
    },
    'thunderbird': {
        'default': ('promote', 'push', 'ship'),
    }
}


def get_logger(verbose=False):
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    os.makedirs(DEFAULT_LOGS_DIR, exist_ok=True)

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M',
                        filename=os.path.join(DEFAULT_LOGS_DIR, 'releasewarrior.log'),
                        filemode='a',
                        level=log_level)
    logger = logging.getLogger("releasewarrior")

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger('').addHandler(console)

    def fatal(*args, **kwargs):
        logger.critical(*args, **kwargs)
        sys.exit(-1)

    logger.fatal = fatal

    return logger


def get_config(path=CUSTOM_CONFIG):
    # first get some default config items
    with open(DEFAULT_CONFIG) as fh:
        config = yaml.load(fh)
    # now append or replace with custom config items
    if os.path.exists(path):
        with open(path) as fh:
            config.update(yaml.load(fh))
    config['templates_dir'] = config.get('templates_dir', DEFAULT_TEMPLATES_DIR)
    config['releasewarrior_data_repo'] = os.path.expanduser(config['releasewarrior_data_repo'])
    return config


def load_json(path):
    data = {}
    with open(path) as f:
        data.update(json.load(f))
    return data


def get_remaining_items(items):
    for index, item in enumerate(items):
        item["id"] = index + 1
        if not item["resolved"]:
            yield item


def get_branch(version, product, logger):
    passed = True
    branch = ""

    if bool(re.match("^\d+\.0rc$", version)):
        branch = "release-rc"
    elif bool(re.match("^(\d+\.\d(\.\d+)?)$", version)):
        if product in ["firefox", "fennec"] and bool(re.match("^(\d+\.\d+)$", version)):
            passed = False
            logger.critical("This release doesn't look like a dot release. Was it meant to be \
a release-candidate?")
            logger.fatal("Include rc at the end of the `%s` for release-candidates", version)
        else:
            branch = "release"
    elif bool(re.match("^\d+\.0b\d+$", version)):
        branch = "beta"
        if product == "devedition":
            branch = "devedition"
    elif bool(re.match("^(\d+\.\d(\.\d+)?esr)$", version)):
        parts = version.split('.')
        branch = "esr{}".format(parts[0])
    else:
        passed = False
        logger.fatal("Couldn't determine branch based on version. See examples in version help")

    if not passed:
        sys.exit(1)
    return branch


def validate(release, logger, config, must_exist=False, must_exist_in=None):

    passed = True

    # branch validation against product
    # not critical so simply prevent basic mistakes
    branch_validations = {
        "devedition": release.branch in ['devedition'],
        "fennec": release.branch in ['beta', 'release', 'release-rc'],
        "firefox": release.branch in ['beta', 'release', 'release-rc', 'esr52', 'esr60'],
        "thunderbird": release.branch in ['beta', 'release']
    }
    if not branch_validations[release.product]:
        logger.fatal(
            "Conflict. Product: %s, can't be used with Branch: %s, determined by Version: %s",
            release.product, release.branch, release.version
        )
        passed = False
    ###

    # ensure release data file exists where expected
    upcoming_path = os.path.join(
        config['releasewarrior_data_repo'],
        config['releases']['upcoming'][release.product],
        "{}-{}-{}.json".format(release.product, release.branch, release.version)
    )
    inflight_path = os.path.join(
        config['releasewarrior_data_repo'],
        config['releases']['inflight'][release.product],
        "{}-{}-{}.json".format(release.product, release.branch, release.version)
    )
    exists_in_upcoming = os.path.exists(upcoming_path)
    exists_in_inflight = os.path.exists(inflight_path)
    # TODO simplify and clean up these conditions
    if must_exist:
        if must_exist_in == "upcoming":
            if not exists_in_upcoming:
                logger.fatal("expected data file to exist in upcoming path: %s", upcoming_path)
                passed = False
            if exists_in_inflight:
                logger.fatal(
                    "data file exists in inflight path and wasn't expected: %s", inflight_path
                )
                passed = False
        elif must_exist_in == "inflight":
            if not exists_in_inflight:
                logger.fatal("expected data file to exist in inflight path: %s", inflight_path)
                passed = False
            if exists_in_upcoming:
                logger.fatal(
                    "data file exists in upcoming path and wasn't expected: %s", upcoming_path
                )
                passed = False
        else:
            if not exists_in_upcoming and not exists_in_inflight:
                logger.fatal(
                    "data file was expected to exist in either upcoming or inflight path: %s, %s",
                    upcoming_path, inflight_path
                )
                passed = False
    else:
        if exists_in_upcoming or exists_in_inflight:
            logger.fatal("data file already exists in one of the following paths: %s, %s",
                         upcoming_path, inflight_path)
            passed = False

    # data repo check
    if not validate_data_repo_updated(logger, config):
        passed = False

    # ensure release directories exist
    for state_dir in config['releases']:
        for product in config['releases'][state_dir]:
            os.makedirs(
                os.path.join(
                    config['releasewarrior_data_repo'], config['releases'][state_dir][product]
                ),
                exist_ok=True
            )
    os.makedirs(
        os.path.join(config['releasewarrior_data_repo'], config['postmortems']), exist_ok=True
    )
    ###
    if not passed:
        sys.exit(1)


def validate_data_repo_updated(logger, config):
    repo = Repo(config['releasewarrior_data_repo'])
    if repo.is_dirty():
        logger.fatal("release data repo dirty. Aborting...")
        return False
    upstream = find_upstream_repo(repo, logger, config)
    # TODO - we should allow csets to exist locally that are not on remote.
    logger.info("ensuring releasewarrior repo is up to date and in sync with {}".format(upstream))
    logger.debug('pulling new csets from {}/master'.format(upstream))
    try:
        # XXX ff_only=True is overriden by user's gitconfig. Known case: when user set
        # rebase = true
        upstream.pull(ff_only=True)
    except git_exc.GitCommandError as e:
        logger.fatal(
            'Could not pull changes from {}/master: {}'.format(upstream, e)
        )
    commits_behind = list(repo.iter_commits('master..{}/master'.format(upstream)))
    if commits_behind:
        logger.fatal('local master is behind {}/master.'.format(upstream))
        return False

    return True


def validate_phase(product, version, phase, logger, config):
    branch = get_branch(version, product, logger)
    allowed_phases = KNOWN_PRODUCT_PHASES[product].get(
        branch,
        KNOWN_PRODUCT_PHASES[product]['default']
    )
    if phase not in allowed_phases:
        logger.fatal('Illegal phase {} for {} {}!'.format(phase, product, version))
        return False
    return True


def validate_rw_repo(logger, config):
    if os.environ.get("RW_DEV"):
        logger.debug("Skipping rw repo validation because RW_DEV is set")
        return
    # data repo state file
    state_file = os.path.join(config['releasewarrior_data_repo'], 'state.yml')
    min_sha = None
    if os.path.isfile(state_file):
        with open(state_file) as fh:
            state = yaml.load(fh)
        min_sha = state.get('min-rw-sha')
    else:
        logger.warning('no release data state file')
        return

    if not min_sha:
        logger.warning('no release data information on minimum sha for releasewarrior')

    if not re.match('[0-9a-fA-F]', min_sha):
        logger.fatal('min sha ({}) is invalid format'.format(min_sha))
        sys.exit(1)

    repo = Repo(RW_REPO)
    if repo.is_dirty():
        logger.warning("releasewarrior repo dirty")
    upstream = find_upstream_repo(
        repo, logger, config, pattern_key='upstream_rw_repo_url_pattern',
        simplified_pattern_key='simplified_rw_repo_url')

    logger.info("ensuring releasewarrior repo is newer than {} from {}".format(min_sha, upstream))
    try:
        repo.git.merge_base('--is-ancestor', min_sha, repo.head.commit)
    except git_exc.GitCommandError:
        logger.fatal('Local releasewarrior repo does not contain {} please pull'
                     'in newer content'.format(min_sha))
        sys.exit(1)


def sanitize_date_input(date, logger):
    try:
        dt = parse(date)
    except ValueError:
        logger.error('%s does not contain a date', date)
        sys.exit(1)

    # is this date in the past? If so assume we meant next year, same month/day
    # Don't do this if the year was explicitly set.
    if dt < datetime.now() and str(dt.year) not in date:
        logger.info("Adjusting %s, assuming it's meant to be next year.", dt)
        dt = dt.replace(year=dt.year + 1)

    return dt.strftime('%Y-%m-%d')


def validate_graphid(graphid):
    """Validate a graphid's syntax.

    Uses the regular expression for 'taskGroupId' from
    https://docs.taskcluster.net/reference/platform/taskcluster-queue/docs/task-schema#task-definition  # noqa: E501
    """
    import re
    taskgraphid_pattern = r'^[A-Za-z0-9_-]{8}[Q-T][A-Za-z0-9_-][CGKOSWaeimquy26-][A-Za-z0-9_-]{10}[AQgw]$'  # noqa: E501
    if re.fullmatch(taskgraphid_pattern, graphid):
        return True
    return False
