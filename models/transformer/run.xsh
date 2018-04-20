#!/usr/bin/env xonsh
import sys

model_file = 'train.py'

# CUDA_VISIBLE_DEVICES=4,5 PYTHONPATH=/paddle/dev/my/build2/python ./run.xsh
python @(model_file)
