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

$ceroot=config.workspace
os.environ['ceroot'] = config.workspace
mode = os.environ.get('mode', 'evaluation')


def main():
    #try_start_mongod()
    refresh_baseline_workspace()
    suc = evaluate_tasks()
    if suc:
        display_success_info()
        if mode != "baseline_test":
            update_baseline()
        exit 0
    else:
        display_fail_info()
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
                with PathRecover():
                    cd @(config.workspace)
                    env = {}
                    exec('from tasks.%s.continuous_evaluation import tracking_kpis'
                        % task_name, env)
                    tracking_kpis = env['tracking_kpis']

                for kpi in tracking_kpis:
                    kpi.root = task_dir
                    if kpi.compare_with(kpi.cur_data, kpi.baseline_data) > config.kpi_update_threshold:
                        log.warn('updating kpi: ', kpi.cur_data)
                        cp @(kpi.out_file) @(kpi.his_file)

        git commit -a -m @(message)
        git push


def refresh_baseline_workspace():
    ''' download baseline. '''
    if mode != "baseline_test":
        # production mode, clean baseline and rerun
        rm -rf @(config.baseline_path)
        git clone @(config.baseline_repo_url) @(config.baseline_path)


def evaluate_tasks():
    '''
    Evaluate all the tasks. It will continue to run all the tasks even
    if any task is failed to get a summary.
    '''
    cd @(config.workspace)
    paddle_commit = repo.get_commit(config.paddle_path)
    commit_time = repo.get_commit_date(config.paddle_path)
    log.warn('commit', paddle_commit)
    all_passed = True
    tasks = [v for v in get_tasks()]
    for task in get_tasks():
        passed, eval_infos, kpis, kpi_types = evaluate(task)

        if mode != "baseline_test":
            log.warn('add evaluation %s result to mongodb' % task)
            pst.add_evaluation_record(paddle_commit,
                                      commit_time,
                                      task,
                                      passed,
                                      eval_infos, kpis, kpi_types)
        if not passed:
            all_passed = False
    return all_passed


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

        # load kpis
        cd @(config.workspace)
        env = {}
        exec('from tasks.%s.continuous_evaluation import tracking_kpis'
             % task_name, env)
        tracking_kpis = env['tracking_kpis']

        # evaluate all the kpis
        eval_infos = []
        kpis = {}
        kpi_types = {}
        passed = True
        for kpi in tracking_kpis:
            suc = kpi.evaluate(task_dir)
            if not suc:
                passed = False
            kpis[kpi.name] = kpi.cur_data
            kpi_types[kpi.name] = kpi.__class__.__name__
            # if failed, continue to evaluate all the kpis to get full statistics.
            eval_infos.append(kpi.fail_info if not suc else kpi.success_info)
        return passed, eval_infos, kpis, kpi_types


def get_tasks():
    with PathRecover():
        cd @(config.workspace)
        subdirs = $(ls @(config.baseline_path)).split()
        return filter(lambda x : not (x.startswith('__') or x.endswith('.md')), subdirs)


def display_fail_info():
    paddle_commit = repo.get_commit(config.paddle_path)
    infos = pst.db.finds(config.table_name, {'commitid': paddle_commit, 'type': 'kpi' })
    log.error('Evaluate [%s] failed!' % paddle_commit)
    log.warn('The details:')
    for info in infos:
        log.info('task:', info['task'])
        log.info('passed: ', info['passed'])
        log.info('infos', '\n'.join(info['infos']))
        log.info('kpis keys', info['kpis-keys'])
        log.info('kpis values', info['kpis-values'])


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

main()
