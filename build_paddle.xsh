#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
$XONSH_SHOW_TRACEBACK = True

import sys; sys.path.insert(0, '')
import config
import os

num_workers = os.environ.get('num_workers', 8)

cd @(config.paddle_path)
mkdir -p build
cd build

# compile_mode env should be set in teamcity
cmake .. -DWITH_TESTING=OFF \
         -DWITH_GOLANG=OFF \
         -DCMAKE_BUILD_TYPE=Release \
         -DWITH_GPU=ON \
         -DWITH_STYLE_CHECK=OFF \
         -DWITH_FLUID_ONLY=ON \
         -DWITH_MKLDNN=off

# clean whl
rm -rf python/dist/*
rm -rf python/build
make -j @(num_workers)
make install

pip install --upgrade python/dist/*.whl
