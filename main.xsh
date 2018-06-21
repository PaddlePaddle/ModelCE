#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
$XONSH_SHOW_TRACEBACK = True

import sys; sys.path.insert(0, '')
import config
from config import pjoin
from utils import PathRecover, log
import persistence as pst
import os
import repo
import argparse
import traceback

$ceroot=config.workspace
os.environ['ceroot'] = config.workspace
mode = os.environ.get('mode', 'evaluation')

def parse_args():
    parser= argparse.ArgumentParser("Tool for running CE models")
    parser.add_argument(
        '--modified',
        action='store_true',
        help='if set, we will just run modified models.')
    args = parser.parse_args()
    return args

def main():
    #try_start_mongod()
    args = parse_args()
    if not args.modified:
        refresh_baseline_workspace()
    suc, exception_task = evaluate_tasks(args)
    if suc:
        display_success_info()
        if mode != "baseline_test" and not args.modified:
            update_baseline()
        exit 0
    else:
        if not args.modified:
            display_fail_info(exception_task)
        sys.exit(-1)
        exit -1


def update_baseline():
    ''' update the baseline in a git repo using current base. '''
    log.warn('updating baseline')
    commit = repo.get_commit(config.paddle_path)
    with PathRecover():
        message = "evalute [%s]" % commit
        for task_name in get_tasks():
            task_dir = pjoin(config.baseline_path, task_name)
            cd @(task_dir)
            print('task_dir', task_dir)
            if os.path.isdir('latest_kpis'):
                # update baseline if the latest kpi is better than history
                tracking_kpis = get_kpi_tasks(task_name)

                for kpi in tracking_kpis:
                    # if the kpi is not actived, do not update baseline.
                    if not kpi.actived: continue
                    kpi.root = task_dir
                    better_ratio = kpi.compare_with(kpi.cur_data, kpi.baseline_data)
                    if  better_ratio > config.kpi_update_threshold:
                        log.warn('current kpi %s better than history by %f, update baseline' % (kpi.out_file, better_ratio))
                        cp @(kpi.out_file) @(kpi.his_file)

        if $(git diff):
            log.warn('update github baseline')
            '''
            due to the selected update controled by `config.kpi_update_threshold`, if one task passed, there might be no baselines to update.
            '''
            git pull origin master
            git commit -a -m @(message)
            git push
        else:
            log.warn('no baseline need to update')


def refresh_baseline_workspace():
    ''' download baseline. '''
    if mode != "baseline_test":
        # production mode, clean baseline and rerun
        rm -rf @(config.baseline_path)
        git clone @(config.baseline_repo_url) @(config.baseline_path)


def evaluate_tasks(args):
    '''
    Evaluate all the tasks. It will continue to run all the tasks even
    if any task is failed to get a summary.
    '''
    cd @(config.workspace)
    paddle_commit = repo.get_commit(config.paddle_path)
    commit_time = repo.get_commit_date(config.paddle_path)
    log.warn('commit', paddle_commit)
    all_passed = True
    exception_task = {}
    if args.modified:
        tasks = [v for v in get_changed_tasks()]
    else:
        tasks = [v for v in get_tasks()]
    for task in tasks:
        try:
            passed, eval_infos, kpis, kpi_types = evaluate(task)
            if mode != "baseline_test":
                log.warn('add evaluation %s result to mongodb' % task)
                kpi_objs = get_kpi_tasks(task)
                if not args.modified:
                    pst.add_evaluation_record(commitid = paddle_commit,
                                              date = commit_time,
                                              task = task,
                                              passed = passed,
                                              infos = eval_infos,
                                              kpis = kpis,
                                              kpi_types = kpi_types,
                                              kpi_objs = kpi_objs)
            if not passed:
                all_passed = False
        except Exception as e:
            exception_task[task] = traceback.format_exc()
            all_passed = False

    return all_passed, exception_task


def evaluate(task_name):
    '''
    task_name: str
        name of a task directory.
    returns:
        passed: bool
            whether this task passes the evaluation.
        eval_infos: list of str
            human-readable evaluations result for all the kpis of this task.
        kpis: dict of (kpi_name, list_of_float)
    '''
    task_dir = pjoin(config.baseline_path, task_name)
    log.warn('evaluating model', task_name)

    with PathRecover():
        cd @(task_dir)
        ./run.xsh

        tracking_kpis = get_kpi_tasks(task_name)

        # evaluate all the kpis
        eval_infos = []
        kpis = {}
        kpi_types = {}
        passed = True
        for kpi in tracking_kpis:
            suc = kpi.evaluate(task_dir)
            if (not suc) and kpi.actived:
                ''' Only if the kpi is actived, its evaluation result would affect the overall tasks's result. '''
                passed = False
                log.error("Task [%s] failed!" % task_name)
                log.error("details:", kpi.fail_info)

            kpis[kpi.name] = kpi.cur_data
            kpi_types[kpi.name] = kpi.__class__.__name__
            # if failed, still continue to evaluate the other kpis to get full statistics.
            eval_infos.append(kpi.fail_info if not suc else kpi.success_info)
        return passed, eval_infos, kpis, kpi_types


def get_tasks():
    with PathRecover():
        cd @(config.workspace)
        subdirs = $(ls @(config.baseline_path)).split()
        return filter(lambda x : not (x.startswith('__') or x.endswith('.md')), subdirs)


def display_fail_info(exception_task):
    paddle_commit = repo.get_commit(config.paddle_path)
    infos = pst.db.finds(config.table_name, {'commitid': paddle_commit, 'type': 'kpi' })
    log.error('Evaluate [%s] failed!' % paddle_commit)
    log.warn('The details:')
    for info in infos:
        if not info['passed']:
            log.warn('task:', info['task'])
            log.warn('passed: ', info['passed'])
            log.warn('infos', '\n'.join(info['infos']))
            log.warn('kpis keys', info['kpis-keys'])
            log.warn('kpis values', info['kpis-values'])
    if exception_task:
        for task, info in exception_task.items():
            log.error("%s %s" %(task, info))


def display_success_info():
    paddle_commit = repo.get_commit(config.paddle_path)
    log.warn('Evaluate [%s] successed!' % paddle_commit)


def try_start_mongod():
    out = $(ps ax | grep mongod).strip().split('\n')
    print('out', out)
    if len(out) < 1: # there are no mongod service
        log.warn('starting mongodb')
        mkdir -p /chunwei/ce_mongo.db
        mongod --dbpath /chunwei/ce_mongo.db &


def get_kpi_tasks(task_name):
    with PathRecover():
        cd @(config.workspace)
        env = {}
        exec('from tasks.%s.continuous_evaluation import tracking_kpis'
             % task_name, env)
        tracking_kpis = env['tracking_kpis']
        return tracking_kpis


def get_changed_tasks():
    tasks = []
    cd @(config.baseline_path)
    out = $(git diff master | grep "diff --git")
    out = out.strip()
    for item in out.split('\n'):
        task = item.split()[3].split('/')[1]
        if task not in tasks:
            tasks.append(task)
    log.warn("changed tasks: %s" % tasks)
    return tasks

main()
