#!/bin/bash

dirname=${PWD##*/}

if [[ ! -d xmlAnaWSBuilder ]] || [[ ! -d quickFit ]]; then
    echo "Execute from FrequentistFramework directory!"
    return 1
fi

if [[ -n ${ANAFIT_LCG_PLATFORM:-} ]]; then
    export ATLAS_LOCAL_ROOT_BASE="${ATLAS_LOCAL_ROOT_BASE:-/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase}"
    source "${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh" || return 1
    lsetup "views LCG_102a ${ANAFIT_LCG_PLATFORM}" || return 1
    lsetup cmake || return 1

    if [[ -z ${_DIRXMLWSBUILDER:-} ]]; then
        export _DIRXMLWSBUILDER="${PWD}/xmlAnaWSBuilder"
        # install.sh builds XMLReader/libxmlAnaWSBuilder.so into build/;
        # only the copied RooFitExtensions library lives at the top-level
        # lib/ (there is no top-level bin/ at all).
        export _BIN_PATH="${_DIRXMLWSBUILDER}/build/bin"
        export _LIB_PATH="${_DIRXMLWSBUILDER}/build/lib:${_DIRXMLWSBUILDER}/lib"
        export LD_LIBRARY_PATH="${_LIB_PATH}:${LD_LIBRARY_PATH:-}"
        export PATH="${_BIN_PATH}:${PATH}"
    fi

    if [[ -z ${_DIRFIT:-} ]]; then
        export _DIRFIT="${PWD}/quickFit"
        # quickFit's build output (quickFit, quickLimit, libquick.so) sits
        # flat in build/, not build/bin or build/lib; the copied
        # RooFitExtensions library is the separate top-level lib/.
        export _BIN_PATH="${_DIRFIT}/build"
        export _LIB_PATH="${_DIRFIT}/build:${_DIRFIT}/lib"
        export LD_LIBRARY_PATH="${_LIB_PATH}:${LD_LIBRARY_PATH:-}"
        export PATH="${_BIN_PATH}:${PATH}"
    fi
else
    if [[ -z ${_DIRXMLWSBUILDER:-} ]]; then
        cd xmlAnaWSBuilder/ || return 1
        source setup_lxplus.sh
        _setup_lxplus_status=$?
        cd .. || return 1
        if (( _setup_lxplus_status != 0 )); then
            return 1
        fi
    fi

    if [[ -z ${_DIRFIT:-} ]]; then
        cd quickFit/ || return 1
        source setup_lxplus.sh
        _setup_lxplus_status=$?
        cd .. || return 1
        if (( _setup_lxplus_status != 0 )); then
            return 1
        fi
    fi
fi

mkdir -p run
