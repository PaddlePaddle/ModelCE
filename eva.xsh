#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
$XONSH_SHOW_TRACEBACK = True

import sys; sys.path.insert(0, '')
import subprocess
import config
from config import pjoin
from utils import PathRecover, log
import os
import argparse
from analysis_kpis import AnalysisKpiData

$ceroot=config.workspace
os.environ['ceroot'] = config.workspace

def parse_args():
    parser= argparse.ArgumentParser("model benchmark")
    parser.add_argument(
        '--task_dir',
        type=str,
        help='The model dir.')
    parser.add_argument(
        '--times', type=int, default=5, help='The run times')
    args = parser.parse_args()
    return args

def get_changed_tasks(args):
    tasks = []
    print (args.task_dir, args.times)
    if args.task_dir:
        tasks = args.task_dir.split()
        return tasks
    cd @(config.baseline_path)
    out = $(git diff master | grep "diff --git")
    out = out.strip()
    for item in out.split('\n'):
        task = item.split()[3].split('/')[1]
        if task not in tasks:
            tasks.append(task)
    log.warn("changed tasks: %s" % tasks)
    return tasks


def main():
    args = parse_args()
    suc = True
    fail_models = []
    tasks = get_changed_tasks(args)
    times = args.times
    for task in tasks:
        try:
            kpis_status, kpis_list = run_task(task, times)
            print(kpis_list)
            ana = AnalysisKpiData(kpis_status, kpis_list)
            ana.analysis_data()
            ana.print_result()
        except Exception as e:
            print (e)
            suc = False
            fail_models.append(task)
    if suc:
        print("all changed models success!")
    else:
        log.warn("failed models:", fail_models)
        sys.exit(1)
        

def run_task(task_name, times):
    '''
    Run the model task.
    '''
    task_dir = pjoin(config.baseline_path, task_name)
    log.warn('run  model', task_name)
    cd @(config.workspace)
    env = {}
    exec('from tasks.%s.continuous_evaluation import tracking_kpis'
             % task_name, env)
    tracking_kpis = env['tracking_kpis']

    kpis_status = get_kpis_status(tracking_kpis)

    need_mul_times = False
    for actived in kpis_status.values():
        if actived:
            need_mul_times = True
            break
    if not need_mul_times:
        times = 1        

    kpis_list = []
    for i in range(times):
        with PathRecover():
            cd @(task_dir)
            ./run.xsh

        cd @(config.workspace)

        kpis = {}
        for kpi in tracking_kpis:
            kpi.root = task_dir
            kpis[kpi.name] = kpi.cur_data
        kpis_list.append(kpis)
    return kpis_status, kpis_list


def get_kpis_status(tracking_kpis):
    kpis_status = {}
    for kpi in tracking_kpis:
        kpis_status[kpi.name] = kpi.actived
    print (kpis_status)
    return kpis_status


main()
