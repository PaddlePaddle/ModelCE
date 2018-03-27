import os
import logging
import shutil

workspace = os.path.dirname(os.path.realpath(__file__))  # pwd
mode = "production"

############################# OFFICIAL CONFIGS #############################
pjoin = os.path.join

# repo address of PaddlePaddle
repo_url = lambda: 'https://github.com/PaddlePaddle/Paddle.git'

# the place to clone paddle source code
# local_repo_path = lambda: pjoin(workspace, 'paddle_code')
local_repo_path = lambda: pjoin(workspace, '..')

# the compiled paddle whl to test
compiled_whl_path = lambda: '/usr/local/opt/paddle/share/wheels/paddlepaddle_gpu-0.11.1a1-cp27-cp27mu-linux_x86_64.whl'

# TODO change a official repo
# NOTE make sure that the evaluator machine has the access rights.
# the repo to store history baselines, by default, the latest will be pulled as the baseline.
baseline_repo_url = lambda: 'git@github.com:Superjomn/paddle-modelci-baseline.git'

baseline_local_repo_path = lambda: pjoin(workspace, 'models')

############################# CUSTOM CONFIGS #############################
# just do anything here
# success_flag_file = lambda: pjoin(workspace, 'success.flag')  #

############################# DONT CHANGE BELOW #############################
tmp_root = lambda: pjoin(workspace, "tmp")
whl_path = lambda: pjoin(tmp_root(), os.path.basename(compiled_whl_path()))
models_path = lambda: pjoin(workspace, 'models')

log_path = lambda: pjoin(workspace, 'modelci.log')

test_root = pjoin(workspace, "_test_tmp_dir")

# keys for gstate
global_state_root = lambda: pjoin(workspace, "_states")
_state_paddle_code_commit_ = "paddle_code_commit"
_evaluation_result_ = "evaluation_result"
_model_factors_ = "model_factors.json"
_fail_commit_ = 'fail_commit'
_success_commit_ = 'success_commit'

############################# DETAILS BELOW #############################

# set logging
_log_format_ = '[%(asctime)s %(levelname)s] %(message)s'
_log_level_ = logging.DEBUG
# logging.basicConfig(
#     format=_log_format_, level=_log_level_, filename=log_path())


def switch_to_test_mode():
    '''
    - set ci's workspace to test_root
    - clear test_root
    '''
    global workspace, mode
    mode = 'test'
    if '_test_' not in workspace:
        workspace = test_root

    assert "_test_tmp_dir" in test_root
    if os.path.isdir(test_root):
        shutil.rmtree(test_root)

    global baseline_repo_url
    baseline_repo_url = lambda: "https://github.com/Superjomn/paddle-modelci-baseline.git"

    logging.basicConfig(
        format=_log_format_,
        level=_log_level_,
        filename=pjoin(workspace, 'test.log'))

if not os.path.isdir(test_root):
    os.mkdir(test_root)

# os.mkdir(global_state_root())
# os.mkdir(test_root)
# os.mkdir(tmp_root())
