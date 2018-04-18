#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
$XONSH_SHOW_TRACEBACK = True

import sys; sys.path.insert(0, '')
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
        default='tasks',
        help='The model dir.')
    parser.add_argument(
        '--times', type=int, default=10, help='The run times')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    kpis_list = run_task(args.task_dir, args.times)
    print(kpis_list)
    ana = AnalysisKpiData(kpis_list)
    ana.analysis_data()
    ana.print_result()


def run_task(task_name, times):
    '''
    Run the model task.
    '''
    task_dir = pjoin(config.baseline_path, task_name)
    log.warn('run  model', task_name)
    kpis_list = []
    for i in range (0, times):
        with PathRecover():
            cd @(task_dir)
            ./run.xsh

        cd @(config.workspace)
        env = {}
        exec('from tasks.%s.continuous_evaluation import tracking_kpis'
             % task_name, env)
        tracking_kpis = env['tracking_kpis']

        kpis = {}
        for kpi in tracking_kpis:
            kpi.root = task_dir
            kpis[kpi.name] = kpi.cur_data
        kpis_list.append(kpis)
    return kpis_list


main()
