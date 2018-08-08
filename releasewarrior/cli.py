import click
import arrow
import sys

import os

from releasewarrior import git
from releasewarrior.helpers import (
    get_config,
    get_logger,
    get_remaining_items,
    load_json,
    sanitize_date_input,
    validate,
    validate_data_repo_updated,
    validate_phase,
    validate_rw_repo,
)
from releasewarrior.wiki_data import (
    complete_filter,
    get_current_build_index,
    generate_newbuild_data,
    get_releases,
    get_release_info,
    generate_release_postmortem_data,
    get_tracking_release_data,
    incomplete_filter,
    log_release_status,
    no_filter,
    order_data,
    update_inflight_graphid,
    update_inflight_human_tasks,
    update_inflight_issue,
    update_prereq_human_tasks,
    write_and_commit,
)

LOGGER = get_logger(verbose=False)
CONFIG = get_config()


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
@click.option('--gtb-date', help="date of planned GTB. format: YYYY-MM-DD",
              default=arrow.now('US/Pacific').format("YYYY-MM-DD"))
def track(product, version, gtb_date, logger=LOGGER, config=CONFIG):
    """Start tracking an upcoming release.
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=False)
    data = {}

    commit_msg = "{} {} started tracking upcoming release.".format(product, version)
    gtb_date = sanitize_date_input(gtb_date, logger)
    data = get_tracking_release_data(release, gtb_date, logger, config)

    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True, help="prerequisite human task id or alias to resolve.")
def prereq(product, version, resolve, logger=LOGGER, config=CONFIG):
    """Add or resolve a prerequisite (pre gtb).
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    Without any options, you will be prompted to add a prerequisite human task
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="upcoming")
    data = load_json(data_path)

    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "{} {} - updated prerequisites. {}".format(product, version, resolve_msg)
    data = update_prereq_human_tasks(data, resolve)

    data = order_data(data)
    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
def newbuild(product, version, logger=LOGGER, config=CONFIG):
    """Mark a release as submitted to shipit.
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    If this is the first buildnum, move the release from upcoming dir to inflight
    Otherwise, increment the buildnum of the already current inflight release
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True)
    data = load_json(data_path)

    commit_msg = "{} {} - new buildnum started.".format(product, version)
    data, data_path, wiki_path = generate_newbuild_data(data, release, data_path,
                                                        wiki_path, logger, config)

    data = order_data(data)
    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


# TODO include valid aliases
@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True, help="inflight human task id or alias to resolve.")
def task(product, version, resolve, logger=LOGGER, config=CONFIG):
    """Add/resolve a human task for current build.
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    Without any options, you will be prompted to add a task
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    # if we are adding a human_task, the release does not have to be inflight yet
    must_exist_in = "inflight" if resolve else None
    validate(release, logger, config, must_exist=True, must_exist_in=must_exist_in)
    data = load_json(data_path)

    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "{} {} - updated inflight tasks. {}".format(product, version, resolve_msg)
    data = update_inflight_human_tasks(data, resolve, logger)

    data = order_data(data)
    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True, help="inflight issue to resolve")
def issue(product, version, resolve, logger=LOGGER, config=CONFIG):
    """Add/resolve an issue in current buildnum.
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    Without any options, you will be prompted to add an issue
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "{} {} - updated inflight issue. {}".format(product, version, resolve_msg)
    data = update_inflight_issue(data, resolve, logger)

    data = order_data(data)
    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


@cli.command()
@click.argument('graphid')
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--phase', type=click.Choice(['promote', 'promote_rc', 'push', 'ship', 'ship_rc']))
def graphid(graphid, product, version, phase, logger=LOGGER, config=CONFIG):
    """Add a graphid to a release.
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    The phase must match the product.

    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    validate_phase(product, version, phase, logger, config)
    commit_msg = "{} {} - added {} graphid.".format(product, version, phase)
    data = update_inflight_graphid(data, phase, graphid, logger)

    data = order_data(data)
    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


# TODO assign default date to the "next wed"
# TODO accept various date inputs
@cli.command()
@click.argument('date')
def postmortem(date, logger=LOGGER, config=CONFIG):
    """Create a postmortem for completed releases.
    creates a postmortem file based on completed releases and their unresolved issues.
    archives release files that are completed
    using the same date will only append and archive releases as they are updated

    argument: date of planned postmortem. format: YYYY-MM-DD
    """

    if not date:
        logger.critical("For now, you must be explicit and specify --date")
        sys.exit(1)

    date = sanitize_date_input(date, logger)

    completed_releases = [
        release for release in get_releases(config, logger, filter=complete_filter)
    ]
    postmortem_data_path = os.path.join(config["releasewarrior_data_repo"], config["postmortems"],
                                        "{}.json".format(date))
    postmortem_wiki_path = os.path.join(config["releasewarrior_data_repo"], config["postmortems"],
                                        "{}.md".format(date))
    wiki_template = config['templates']["wiki"]["postmortem"]

    # validate
    validate_rw_repo(logger, config)
    if not completed_releases:
        logger.warning("No recently completed releases. Nothing to do!")
        sys.exit(1)
    # make sure archive and postmortem dirs exist
    for product in config['releases']['archive']:
        os.makedirs(
            os.path.join(
                config['releasewarrior_data_repo'], config['releases']['archive'][product]
            ),
            exist_ok=True
        )
    os.makedirs(
        os.path.join(config['releasewarrior_data_repo'], config['postmortems']),
        exist_ok=True
    )

    # get existing postmortem data
    postmortem_data = {
        "date": date,
        "complete_releases": []
    }
    if os.path.exists(postmortem_data_path):
        postmortem_data = load_json(postmortem_data_path)

    # archive completed releases
    for release in completed_releases:
        _, data_path, wiki_path = get_release_info(release["product"], release["version"],
                                                   logger, config)
        # add release to postmortem data
        postmortem_data["complete_releases"].append(generate_release_postmortem_data(release))
        # archive release
        archive_dir = os.path.join(config["releasewarrior_data_repo"],
                                   config["releases"]["archive"][release["product"]])
        git.move(data_path, os.path.join(archive_dir, os.path.basename(data_path)), logger, config)
        git.move(wiki_path, os.path.join(archive_dir, os.path.basename(wiki_path)), logger, config)

    commit_msg = "updates {} postmortem".format(date)
    postmortem_data["complete_releases"] = sorted(postmortem_data["complete_releases"],
                                                  key=lambda x: x["date"])
    write_and_commit(postmortem_data, postmortem_data_path, postmortem_wiki_path,
                     commit_msg, logger, config, wiki_template=wiki_template)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
def cancel(product, version, logger=LOGGER, config=CONFIG):
    """Abort the current buildnum.
    Similar to newbuild where it aborts current buildnum of given release but does not create
    a new build.
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    logger.info("Most recent buildnum has been aborted. Release cancelled.")
    commit_msg = "{} {} - cancelling release".format(product, version)
    current_build_index = get_current_build_index(data)
    data["inflight"][current_build_index]["aborted"] = True

    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
def sync(product, version, logger=LOGGER, config=CONFIG):
    """Sync manual changes to json.
    Takes currently saved json data of given release from data repo, generates the wiki and
    commits.
    Product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    """
    validate_rw_repo(logger, config)
    release, data_path, wiki_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    commit_msg = "{} {} - syncing wiki with current data".format(product, version)

    write_and_commit(data, data_path, wiki_path, commit_msg, logger, config)


@cli.command()
@click.option(
    '--verbose', is_flag=True, help="shows all tracked releases as well as completed releases"
)
def status(verbose, logger=LOGGER, config=CONFIG):
    """Shows prerequisites and inflight human tasks.
    """
    ###
    if not validate_data_repo_updated(logger, config):
        sys.exit(1)

    # upcoming prerequisites
    upcoming_releases = get_releases(config, logger, inflight=False, filter=incomplete_filter)
    if verbose:
        upcoming_releases = get_releases(config, logger, inflight=False, filter=no_filter)
    upcoming_releases = sorted(upcoming_releases, key=lambda x: x["date"], reverse=True)
    logger.info("UPCOMING RELEASES...")
    if not upcoming_releases:
        logger.info("=" * 79)
        logger.info("[no upcoming releases with prerequisite tasks to do]")
    for release in upcoming_releases:
        remaining_prereqs = get_remaining_items(release["preflight"]["human_tasks"])

        logger.info("=" * 79)
        logger.info("Upcoming Release: %s %s", release["product"], release["version"])
        logger.info("Expected GTB: %s", release["date"])
        logger.info("\tIncomplete prerequisites:")
        for prereq in remaining_prereqs:
            logger.info(
                "\t\t* ID: %s, deadline: %s, bug %s - %s", prereq['id'], prereq['deadline'],
                prereq["bug"], prereq["description"]
            )
        if not remaining_prereqs:
            logger.info("\t\t* none")

    ###

    ###
    # releases in flight
    incomplete_releases = [
        release for release in get_releases(config, logger, filter=incomplete_filter)
    ]
    logger.info("")
    logger.info("INFLIGHT RELEASES...")
    if not incomplete_releases:
        logger.info("=" * 79)
        logger.info("[no inflight releases with human tasks to do]")
    for release in incomplete_releases:
        log_release_status(release, logger)
    ###

    ###
    # completed releases (unresolved issues)
    if verbose:
        complete_releases = [
            release for release in get_releases(config, logger, filter=complete_filter)
        ]
        logger.info("")
        logger.info("COMPLETED RELEASES...")
        if not complete_releases:
            logger.info("=" * 79)
            logger.info("[all completed releases have been archived]")
        for release in complete_releases:
            log_release_status(release, logger)
    ###


@cli.command()
@click.option('--push', is_flag=True, help="Pushes the data repo to upstream")
@click.option('--pull', is_flag=True, help="Pulls the data repo from upstream")
def data(push, pull, logger=LOGGER, config=CONFIG):
    """Interacts with the data repo."""
    if push and pull:
        logger.error("Can't push and pull at the same time.")
        sys.exit(1)
    if push:
        git.push(logger, config)
    if pull:
        git.pull(logger, config)
