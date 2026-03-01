#!/bin/bash

cwd=$(pwd)

#git submodule sync --recursive
#git submodule update --init
# just clone submodules by hand

#needs to be done before setup, because that changes /usr/bin/python
#source scripts/install_pyBumpHunter.sh # ignore bumphunter for now

source scripts/setup_buildCombineFit.sh

source scripts/install_quickFit_and_xmlAnaWSBuilder.sh

# TODO: integrate in above script?
cd $cwd/workspaceCombiner
mkdir build && cd build
cmake ..
make -j4 
make install

cd $cwd
