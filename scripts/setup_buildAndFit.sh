#!/bin/bash

dirname=${PWD##*/}

if [[ ! -d xmlAnaWSBuilder ]] || [[ ! -d quickFit ]]; then
    echo "Execute from FrequentistFramework directory!"
    return 1
fi

if [[ -z $_DIRXMLWSBUILDER ]]; then
    cd xmlAnaWSBuilder/
    source setup_lxplus.sh
    cd ..
fi

if [[ -z $_DIRFIT ]]; then
    cd quickFit/
    source setup_lxplus.sh
    cd ..
fi

mkdir -p run
