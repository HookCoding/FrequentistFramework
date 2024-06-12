#!/bin/bash

cwd=$(pwd)

#git submodule init
#git submodule update

#needs to be done before setup, because that changes /usr/bin/python
source scripts/install_pyBumpHunter.sh

source scripts/setup_buildCombineFit.sh

source scripts/install_roofitext.sh $cwd/xmlAnaWSBuilder

cd $cwd/xmlAnaWSBuilder/
mkdir build && cd build
cmake ..
make -j4
make install

cd $cwd/quickFit/
mkdir build && cd build
cmake ..
make -j4
make install

cd $cwd/workspaceCombiner
mkdir build && cd build
cmake ..
make -j4 
make install

cd $cwd
