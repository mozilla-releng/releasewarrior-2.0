#!/usr/bin/env python

import aiohttp
import argparse
import asyncio
import async_timeout
import posixpath
from taskcluster.aio import Index, Queue


HG_URL = 'https://hg.mozilla.org/'

REPOS = ('releases/mozilla-beta', 'releases/mozilla-release',
         'releases/mozilla-esr52', 'releases/mozilla-esr60', 'mozilla-central')

""" http://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/pushlog.html?highlight=json-pushes#json-pushes-command """  # noqa
JSON_PUSHES = 'json-pushes?changeset={rev}&version=2&tipsonly=1&full=1'

ACTION_INDEX = 'gecko.v2.{repo}.pushlog-id.{pushid}.actions'


async def get_changeset_data(revision, session):
    for repo in REPOS:
        url = posixpath.join(HG_URL, repo, JSON_PUSHES.format(rev=revision))
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                if response.status == 404:
                    continue
                response.raise_for_status()

                index_repo = repo[repo.rfind('/') + 1:]
                data = await response.json()
                pushlog_id = list(data['pushes'].keys())[0]
                changeset = data['pushes'][pushlog_id]['changesets'][-1]
                return (changeset, index_repo, pushlog_id)


async def get_action_tasks(session, pushlog_id, index_repo):
    async with async_timeout.timeout(100):
        index_string = ACTION_INDEX.format(pushid=pushlog_id, repo=index_repo)
        index = Index(session=session)
        data = await index.listTasks(index_string)
        tasks = [t['taskId'] for t in data['tasks']]
        return tasks


async def get_action_task_details(session, taskid):
    async with async_timeout.timeout(100):
        queue = Queue(session=session)
        task = await queue.task(taskid)
        return dict(taskid=taskid,
                    name=task['extra']['action']['name'],
                    buildnum=task['extra']['action']['context']['input']['build_number'],
                    flavor=task['extra']['action']['context']['input']['release_promotion_flavor'],
                    ci=task['taskGroupId'])


def output_graphs(tasks, format='human'):
    if format == 'human':
        return output_graphs_human(tasks)
    if format == 'export':
        return output_graphs_export(tasks)
    raise NotImplementedError("format {} is not yet implemented".format(format))


def output_graphs_human(tasks):
    for product in ['devedition', 'firefox', 'fennec']:
        product_tasks = [t for t in tasks if product in t['flavor']]
        if not product_tasks:
            continue
        buildnumbers = set([t['buildnum'] for t in product_tasks])
        print("|{:-^111}|".format(product.title()))
        print("|  {:<8} | {:^22} | {:^22} | {:^22} | {:^22} |".format(
            'buildN', 'CI', 'promote', 'push', 'ship'))
        print("|{:-^111}|".format(''))
        for bn in sorted(buildnumbers, reverse=True):
            for ci in set([t['ci'] for t in product_tasks if t['buildnum'] == bn]):
                promote = [t['taskid'] for t in product_tasks
                           if t['buildnum'] == bn and t['ci'] == ci and
                           'promote_' in t['flavor']]
                push = [t['taskid'] for t in product_tasks
                        if t['buildnum'] == bn and t['ci'] == ci and
                        'push_' in t['flavor']]
                ship = [t['taskid'] for t in product_tasks
                        if t['buildnum'] == bn and t['ci'] == ci and
                        'ship_' in t['flavor']]
                if len(promote) > 1 or len(push) > 1 or len(ship) > 1:
                    raise Exception("Found too many relevant graphs")
                if not promote:
                    promote = ['']
                if not push:
                    push = ['']
                if not ship:
                    ship = ['']
                print("|  build{:<3} | {:^22} | {:^22} | {:^22} | {:^22} |".format(
                    bn, ci, promote[0], push[0], ship[0]))
                print("|{:-^111}|".format(''))
        print()


def output_graphs_export(tasks):
    for product in ['devedition', 'firefox', 'fennec']:
        product_tasks = [t for t in tasks if product in t['flavor']]
        if not product_tasks:
            continue
        buildnumbers = set([t['buildnum'] for t in product_tasks])
        print("|{:-^80}|".format(product.title()))
        for bn in sorted(buildnumbers, reverse=True):
            for ci in set([t['ci'] for t in product_tasks if t['buildnum'] == bn]):
                print("|{:.^80}|".format('build{}'.format(bn)))
                promote = [t['taskid'] for t in product_tasks
                           if t['buildnum'] == bn and t['ci'] == ci and
                           'promote_' in t['flavor']]
                push = [t['taskid'] for t in product_tasks
                        if t['buildnum'] == bn and t['ci'] == ci and
                        'push_' in t['flavor']]
                ship = [t['taskid'] for t in product_tasks
                        if t['buildnum'] == bn and t['ci'] == ci and
                        'ship_' in t['flavor']]
                if len(promote) > 1 or len(push) > 1 or len(ship) > 1:
                    raise Exception("Found too many relevant graphs")
                print('export DECISION_TASK_ID={}'.format(ci))
                if promote:
                    print('export PROMOTE_TASK_ID={}'.format(promote[0]))
                if push:
                    print('export PUSH_TASK_ID={}'.format(push[0]))
                if ship:
                    print('export SHIP_TASK_ID={}'.format(ship[0]))
                print("|{:-^80}|".format(''))
        print()


def get_my_options():
    parser = argparse.ArgumentParser(description='Gather taskids for release promotion')
    parser.add_argument('-r', '--revision', action='store')
    parser.add_argument('--output', default='human', action='store',
                        choices=['human', 'export'])
    options = parser.parse_args()
    return options


async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        options = get_my_options()
        cset_data = await get_changeset_data(options.revision, session)
        changeset, index_repo, pushlog_id = cset_data
        possible_tasks = await get_action_tasks(session, pushlog_id, index_repo)
        all_relevant_tasks = []
        for taskid in possible_tasks:
            task_data = await get_action_task_details(session, taskid)
            if task_data['name'] != 'release-promotion':
                continue
            all_relevant_tasks.append(task_data)
        output_graphs(all_relevant_tasks, format=options.output)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
