#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
import sys; sys.path.insert(0, '')
import config
$modelci_root=config.workspace

./utils_test.xsh
./core_test.xsh
./repo_test.xsh
./baseline_strategy_test.xsh
./core_test.xsh
