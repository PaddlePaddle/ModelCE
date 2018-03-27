#!/usr/bin/env xonsh
import os
import config

$RAISE_SUBPROC_ERROR = True

os.environ['modelci_root'] = config.workspace

./utils_test.xsh
./core_test.xsh
./repo_test.xsh
./baseline_strategy_test.xsh
./core_test.xsh
