#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
$XONSH_SHOW_TRACEBACK = True

import os
import sys; sys.path.insert(0, '')
import time

import prepare
import config
import repo
import baseline
from utils import *
from core import TestError

# set environ for tests to load core.py
# TODO no need two ways to set environment
$modelci_root = config.workspace
os.environ['modelci_root'] = config.workspace

def test_released_whl():
    prepare.get_whl()
    prepare.install_whl()
    test_models()

def test_models():
    cd @(config.workspace)
    evaluate_status = []
    log.info('begin to evaluate model')
    gstate.clear(config._evaluation_result_)
    for model in models():
        log.info('get model', model)
        status = 'fail'
        model_path = pjoin(config.workspace, model)
        try:
            passed, errors = test_model(model)
            status = "pass" if passed else '; '.join(errors)
            log.info('evaluation status', status)
        except Exception as e:
            log.error('model %s execute error' % model)
            status = 'exec error: %s' % str(e)
        evaluate_status.append((model, status))
        update_evaluation_status(evaluate_status)

    log.warn('evaluation result:\n%s' % gstate.get_evaluation_result())
    # commitid = repo.get_paddle_commit()
    date = time.strftime("%m-%d %H:%M:%S")
    # if evaluation_succeed():
    #     update_success_commit_to_gstate()
    #     gstate.add_evaluation_record(commitid, True, date)
    # else:
    #     update_fail_commit_to_gstate()
        # gstate.add_evaluation_record(commitid, False, date)

def test_model(model_name):
    model_dir = pjoin(config.models_path(), model_name)
    log.info('model dir', model_dir)
    def run_model():
        log.warn('running model ', model_name)
        ./train.xsh
        log.warn('finish running model')
    def evaluate_model():
        log.warn('evaluating model ', model_name)
        log.info('models_path', config.models_path())
        model_root = pjoin(config.models_path(), model_name)
        log.info('model_root', model_root)
        cd @(config.workspace)
        env = {}
        exec('from models.%s.continuous_evaluation import tracking_factors' % model_name, env)
        tracking_factors = env['tracking_factors']
        passed = True
        status = []
        for factor in tracking_factors:
            suc = factor.evaluate(model_root)
            if not suc:
                status.append(factor.error_info)
            else:
                status.append(factor.success_info)
        return passed, status

    with PathRecover():
        cd @(model_dir)
        run_model()
        return evaluate_model()

def update_evaluation_status(status):
    ''' persist the evaluation status to path '''
    lines = ['%s\t%s' % kv for kv in status]
    gstate.set_evaluation_result('\n'.join(lines))

def source_code_updated():
    '''
    whether paddle source is updated
    '''
    cur_commit = repo.get_paddle_commit()
    last_commit = gstate.get(config._state_paddle_code_commit_)
    updated = last_commit is None or cur_commit != last_commit
    gstate.set_source_code_updated(updated)
    if not updated:
        log.info("paddle source code is not changed, skip test, commitid %s" % cur_commit)
    else:
        gstate.set(config._state_paddle_code_commit_, cur_commit)
    return updated


baseline.strategy.refresh_workspace()
test_models()
baseline.strategy()

if not evaluation_succeed():
    log.error("evaluation failed!")
    log.warn("evaluation details:")
    log.warn(gstate.get_evaluation_result())
    sys.exit(-1)
log.warn("all evaluation passed!")
