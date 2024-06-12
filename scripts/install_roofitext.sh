#!/bin/bash

# This script is for installing RooFitExtensions. If the user has installed the package somewhere, please make sure cmake can find it
if [ $# -gt 0 ]; then
    outputDir=${1}
else
    outputDir=`pwd`
fi

# Force remove empty RooFitExtensions directory that was create from recursive submodule update
rm -r ${outputDir}/RooFitExtensions
if [ ! -d ${outputDir}/RooFitExtensions ]; then
    mkdir -vp ${outputDir}
    echo "Cloning RooFitExtensions into target directory ${outputDir}..."
    git clone https://:@gitlab.cern.ch:8443/atlas_higgs_combination/software/RooFitExtensions.git ${outputDir}/RooFitExtensions
fi

if [ -d ${outputDir}/RooFitExtensions ]; then
    pushd ${outputDir}/RooFitExtensions
    git pull
    mkdir -vp build
    cd build
    cmake ../ -DCMAKE_INSTALL_PREFIX=${outputDir}/RooFitExtensions
    make -j 4
    make install
    cd -
    popd
fi

export RooFitExtensions_DIR=${outputDir}/RooFitExtensions

mkdir -vp ${outputDir}/lib/
cp ${outputDir}/RooFitExtensions/lib/* ${outputDir}/lib/
