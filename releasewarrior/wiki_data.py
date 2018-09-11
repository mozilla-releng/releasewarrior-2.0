import json

import os
from copy import deepcopy

from git import Repo
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from releasewarrior.click_input import generate_inflight_task_from_input, is_future_threat_input
from releasewarrior.click_input import generate_prereq_task_from_input
from releasewarrior.click_input import generate_inflight_issue_from_input
from releasewarrior.collections import Release
from releasewarrior.git import commit, push
from releasewarrior.helpers import get_branch, load_json, get_remaining_items, validate_graphid


def order_data(data):
    # order prereqs by deadline
    prereqs = data["preflight"]["human_tasks"]
    data["preflight"]["human_tasks"] = sorted(prereqs, key=lambda x: x["deadline"])
    # order buildnums by most recent
    builds = data["inflight"]
    data["inflight"] = sorted(builds, key=lambda x: x["buildnum"], reverse=True)
    return data


def get_current_build_index(release):
    highest_buildnum = 0
    return_index = 0
    for index, build in enumerate(release['inflight']):
        if build["buildnum"] > highest_buildnum:
            highest_buildnum = build["buildnum"]
            return_index = index
    return return_index


def generate_wiki(data, wiki_template, logger, config):
    logger.info("generating wiki from template and config")

    if not wiki_template:
        wiki_template = config['templates']["wiki"]["generic"]

    env = Environment(loader=FileSystemLoader(config['templates_dir']),
                      undefined=StrictUndefined, trim_blocks=True)

    template = env.get_template(wiki_template)
    return template.render(**data)


def write_data(data_path, content, logger, config):
    logger.info("writing to data file: %s", data_path)
    with open(data_path, 'w') as data_file:
        json.dump(content, data_file, indent=4, sort_keys=True)

    return data_path


def write_corsica(corsica_path, content, logger, config):
    logger.info("writing to corsica file: %s", corsica_path)
    with open(corsica_path, 'w') as cp:
        cp.write(content)

    return corsica_path


def write_wiki(wiki_path, content, logger, config):
    logger.info("writing to wiki file: %s", wiki_path)
    with open(wiki_path, 'w') as wp:
        wp.write(content)

    return wiki_path


def get_release_files(release, logging, config):
    upcoming_path = os.path.join(config['releasewarrior_data_repo'],
                                 config['releases']['upcoming'][release.product])
    inflight_path = os.path.join(config['releasewarrior_data_repo'],
                                 config['releases']['inflight'][release.product])
    data_file = "{}-{}-{}.json".format(release.product, release.branch, release.version)
    wiki_file = "{}-{}-{}.md".format(release.product, release.branch, release.version)
    release_path = upcoming_path
    if os.path.exists(os.path.join(inflight_path, data_file)):
        release_path = inflight_path
    return [
        os.path.join(release_path, data_file),
        os.path.join(release_path, wiki_file)
    ]


def complete_filter(tasks, issues, aborted):
    return (all(task["resolved"] for task in tasks) or aborted) and \
            all(issue["resolved"] for issue in issues)


def incomplete_filter(tasks, issues, aborted):
    return (not all(task["resolved"] for task in tasks) and not aborted) or \
            not all(issue["resolved"] for issue in issues)


def no_filter(tasks, issues, aborted):
    return True


def get_releases(config, logger, inflight=True, filter=no_filter):
    for release_path in config['releases']['inflight' if inflight else 'upcoming'].values():
        search_dir = os.path.join(config['releasewarrior_data_repo'], release_path)
        for root, dirs, files in os.walk(search_dir):
            for f in [data_file for data_file in files if data_file.endswith(".json")]:
                abs_f = os.path.join(search_dir, f)
                with open(abs_f) as data_f:
                    data = json.load(data_f)
                    if inflight:
                        tasks = data["inflight"][get_current_build_index(data)]["human_tasks"]
                        issues = data["inflight"][get_current_build_index(data)]["issues"]
                        aborted = data["inflight"][get_current_build_index(data)]["aborted"]
                    else:
                        tasks = data["preflight"]["human_tasks"]
                        issues = []
                        aborted = False
                    if filter(tasks, issues, aborted):
                        yield data


def get_release_info(product, version, logger, config):
    branch = get_branch(version, product, logger)
    release = Release(product=product, version=version, branch=branch)
    data_path, wiki_path = get_release_files(release, logger, config)
    logger.debug("release info: %s", release)
    logger.debug("data path: %s", data_path)
    logger.debug("wiki path: %s", wiki_path)
    return release, data_path, wiki_path


def generate_corsica(config, logger):
    all_inflight_releases = get_releases(config, logger)
    corsica_data = {
        "releases": {}
    }
    for release in all_inflight_releases:
        branch = get_branch(release["version"], release["product"], logger)
        branch = branch.replace("-rc", "")
        human_tasks = {}
        current_build_index = get_current_build_index(release)
        for task in release["inflight"][current_build_index]["human_tasks"]:
            if task.get("alias"):
                human_tasks[task["alias"]] = task["resolved"]
        if not corsica_data["releases"].get(release["product"]):
            corsica_data["releases"][release["product"]] = {}

        if not corsica_data["releases"][release["product"]].get(branch):
            corsica_data["releases"][release["product"]][branch] = []
        corsica_data["releases"][release["product"]][branch].append({
            "buildnum": release["inflight"][current_build_index]["buildnum"],
            "version": release["version"].replace("rc", ""),
            "human_tasks": human_tasks
        })

    index_template = config['templates']["corsica"]["index"]

    env = Environment(loader=FileSystemLoader(config['templates_dir']),
                      undefined=StrictUndefined, trim_blocks=True)

    template = env.get_template(index_template)
    return template.render(**corsica_data)


def extract_product_from_json(filepath):
    data = load_json(filepath)
    return "{} {}".format(data.get('product', ''), data.get('version', ''))


def update_markdown_index(logger, config):
    repo_path = config["releasewarrior_data_repo"]
    prefixes = ['inflight', 'upcoming']
    md_files = dict()
    for prefix in prefixes:
        md_files[prefix] = dict()
        for directory, _, files in os.walk(os.path.join(repo_path, prefix)):
            for filename in [os.path.join(directory, f) for f in files if f.endswith('.md')]:
                product = extract_product_from_json(filename.replace('.md', '.json'))
                md_files[prefix][product] = filename.replace(repo_path, '')
    env = Environment(loader=FileSystemLoader(config['templates_dir']),
                      undefined=StrictUndefined, trim_blocks=True)

    template = env.get_template('markdown/readme.md.tmpl')
    return template.render(md_files=md_files)


def write_and_commit(data, data_path, wiki_path, commit_msg, logger, config, wiki_template=None):
    corsica_path = os.path.join(config["releasewarrior_data_repo"], config["corsica"])
    wiki = generate_wiki(data, wiki_template, logger, config)
    new_readme = update_markdown_index(logger, config)
    paths = []

    paths.append(write_data(data_path, data, logger, config))
    paths.append(write_wiki(wiki_path, wiki, logger, config))
    paths.append(write_wiki(os.path.join(
        config['releasewarrior_data_repo'], 'README.md'), new_readme, logger, config))
    if config['corsica_enabled']:
        corsica = generate_corsica(config, logger)
        paths.append(write_corsica(corsica_path, corsica, logger, config))
    for p in paths:
        logger.debug(p)
    if not os.environ.get("RW_DEV"):
        commit(paths, commit_msg, logger, config)
        if config.get("auto_push_data"):
            push(logger, config)


def generate_newbuild_data(data, release, data_path, wiki_path, logger, config):
    is_first_gtb = "upcoming" in data_path
    current_build_index = get_current_build_index(data)
    if is_first_gtb:
        # resolve shipit task
        for index, task in enumerate(data["inflight"][current_build_index]["human_tasks"]):
            if task["alias"] == "shipit":
                data["inflight"][current_build_index]["human_tasks"][index]["resolved"] = True

        #   delete json and md files from upcoming dir, and set new dest paths to be inflight
        repo = Repo(config['releasewarrior_data_repo'])
        inflight_dir = os.path.join(config['releasewarrior_data_repo'],
                                    config['releases']['inflight'][release.product])
        moved_files = repo.index.move([data_path, wiki_path, inflight_dir])
        # set data and wiki paths to new dest (inflight) dir
        # moved_files is a list of tuples representing [files_moved][destination_location]
        # TODO
        data_path = os.path.join(config['releasewarrior_data_repo'], moved_files[0][1])
        wiki_path = os.path.join(config['releasewarrior_data_repo'], moved_files[1][1])
    else:
        #  kill latest buildnum add new buildnum based most recent buildnum
        logger.info("most recent buildnum has been aborted, starting a new buildnum")
        newbuild = deepcopy(data["inflight"][current_build_index])
        # abort the now previous buildnum
        data["inflight"][current_build_index]["aborted"] = True
        newbuild["aborted"] = False
        for task in newbuild["human_tasks"]:
            if task["alias"] == "shipit":
                continue  # leave submitted to shipit as resolved
            # reset all tasks to unresolved
            task["resolved"] = False
        # carry forward only unresolved issues
        newbuild["issues"] = [issue for issue in get_remaining_items(newbuild["issues"])]
        # increment buildnum
        newbuild["buildnum"] = newbuild["buildnum"] + 1
        # ignore old graphids
        newbuild["graphids"] = []
        # add new buildnum based on previous to current release
        data["inflight"].append(newbuild)
    current_build_index = get_current_build_index(data)

    return data, data_path, wiki_path


def get_tracking_release_data(release, gtb_date, logger, config):
    logger.info("generating data from template and config")
    data_template = os.path.join(
        config['templates_dir'],
        config['templates']["data"][release.product][release.branch]
    )
    data = load_json(data_template)
    data["version"] = release.version
    data["date"] = gtb_date
    return data


def normalize_human_task_id(human_tasks, task_id):
    '''Turn a human task id argument into a usable list index.

    Arguments:
    human_tasks: a list of dicts of the human tasks. Expects the dicts to have
        an 'alias' key
    task_id: a string of the human task id argument.

    Returns:
    An int of the task index.
    Raises:
    ValueError if it cannot be translated to a valid index.
    '''
    try:
        human_task_id = int(task_id) - 1
        # Bounds checking - is our index in the list?
        if not 0 < human_task_id < len(human_tasks):
            human_task_id = None
    except ValueError:
        # Bounds checking handled by enumerate.
        human_task_id = next((index for index, task in enumerate(
            human_tasks) if task['alias'] == task_id), None)

    if human_task_id is None:
        raise ValueError('Invalid task id')
    return human_task_id


def update_inflight_human_tasks(data, resolve, logger):
    data = deepcopy(data)
    current_build_index = get_current_build_index(data)
    if resolve:
        for raw_task_id in resolve:
            try:
                human_task_id = normalize_human_task_id(
                    data["inflight"][current_build_index]["human_tasks"], raw_task_id)
            except ValueError:
                logger.error("Unknown task id: %s", raw_task_id)
                continue
            data["inflight"][current_build_index]["human_tasks"][human_task_id]["resolved"] = True
    else:
        logger.info("Current existing inflight tasks:")
        for index, task in enumerate(data["inflight"][current_build_index]["human_tasks"]):
            logger.info("ID: %s - %s", index + 1, task["description"])
        # create a new inflight human task through interactive inputs
        new_human_task = generate_inflight_task_from_input()
        data["inflight"][current_build_index]["human_tasks"].insert(
            new_human_task.position,
            {
                "alias": "", "description": new_human_task.description,
                "docs": new_human_task.docs, "resolved": False
            }
        )

    return data


def update_prereq_human_tasks(data, resolve):
    data = deepcopy(data)
    if resolve:
        for human_task_id in resolve:
            # 0 based index so -1
            human_task_id = int(human_task_id) - 1
            data["preflight"]["human_tasks"][human_task_id]["resolved"] = True
    else:
        # create a new prerequisite task through interactive inputs
        new_prereq = generate_prereq_task_from_input(gtb_date=data.get('date'))
        data["preflight"]["human_tasks"].append(
            {
                "bug": new_prereq.bug, "deadline": new_prereq.deadline,
                "description": new_prereq.description, "resolved": False
            }
        )
    return data


def update_inflight_issue(data, resolve, logger):
    data = deepcopy(data)
    current_build_index = get_current_build_index(data)
    if resolve:
        for issue_id in resolve:
            # 0 based index so -1
            issue_index = int(issue_id) - 1
            logger.info(
                "resolving issue %s - %s",
                issue_id,
                data["inflight"][current_build_index]["issues"][issue_index]["description"]
            )
            data["inflight"][current_build_index]["issues"][issue_index]["resolved"] = True
            data["inflight"][current_build_index]["issues"][issue_index]["future_threat"] = \
                is_future_threat_input()

    else:
        # create a new issueuisite task through interactive inputs
        new_issue = generate_inflight_issue_from_input()
        data["inflight"][current_build_index]["issues"].append(
            {
                "who": new_issue.who, "bug": new_issue.bug, "description": new_issue.description,
                "resolved": False, "future_threat": True
            }
        )
    return data


def update_inflight_graphid(data, phase, graphid, logger):
    data = deepcopy(data)
    current_build_index = get_current_build_index(data)
    # If we've been given a url, copy/pasted from the 'new build' email, fix that.
    graphid = graphid.split('/')[-1]
    # Double-click to select text on Mac includes the starting u' but not the
    # final '
    if graphid.startswith("u'"):
        graphid = graphid[2:]

    if not validate_graphid(graphid):
        logger.fatal("GraphID %s is invalid.", graphid)
    graphids = data["inflight"][current_build_index]["graphids"]
    existing_phases = [p for p, _ in graphids]
    if phase in existing_phases:
        i = existing_phases.index(phase)
        graphids[i] = [phase, graphid]
    else:
        graphids.append([phase, graphid])
    return data


def generate_release_postmortem_data(release):
    postmortem_release = {
        "version": release['version'],
        "product": release['product'],
        "date": release['date'],
    }
    future_threat_issues = []
    resolved_issues = []
    for build in release["inflight"]:
        for issue in build["issues"]:
            issue["buildnum"] = build["buildnum"]
            if issue["future_threat"]:
                future_threat_issues.append(issue)
            else:
                resolved_issues.append(issue)

    postmortem_release["future_threats"] = future_threat_issues
    postmortem_release["resolved"] = resolved_issues

    return postmortem_release


def log_release_status(release, logger):
    current_build_index = get_current_build_index(release)
    remaining_tasks = get_remaining_items(release["inflight"][current_build_index]["human_tasks"])
    remaining_issues = get_remaining_items(release["inflight"][current_build_index]["issues"])

    logger.info("=" * 79)
    logger.info("RELEASE: %s %s build%s %s",
                release["product"], release["version"],
                release["inflight"][current_build_index]["buildnum"], release["date"])
    for graph_info in release["inflight"][current_build_index]["graphids"]:
        logger.info("%s graph: https://tools.taskcluster.net/task-group-inspector/#/%s",
                    graph_info[0], graph_info[1])
    logger.info("")
    logger.info("\treleaserunner variables:")
    for graph_info in release["inflight"][current_build_index]["graphids"]:
        print("\t\texport {}_TASK_ID={}".format(graph_info[0].upper(), graph_info[1]))
    logger.info("")
    logger.info("\tIncomplete human tasks:")
    for task in remaining_tasks:
        alias = ""
        if task.get("alias"):
            alias = "(alias: {})".format(task["alias"])
        logger.info("\t\t* ID %s %s - %s", task["id"], alias, task["description"])
    logger.info("\tUnresolved issues:")
    for issue in remaining_issues:
        logger.info("\t\t* ID: %s bug: %s - %s", issue["id"], issue["bug"], issue["description"])
