#!/bin/bash

cd pyBumpHunter
#virtualenv --python=/cvmfs/sft.cern.ch/lcg/releases/LCG_105/Python/3.9.12/x86_64-el9-gcc11-opt/lib/python3.9/site.py pyBH_env  # create a venv w/ python3 (if we don’t use --python=... then it defaults to python 2.7)
virtualenv --python=/cvmfs/sft.cern.ch/lcg/releases/LCG_105/Python/3.9.12/x86_64-el9-gcc11-opt/bin/python3 pyBH_env # this worked

source pyBH_env/bin/activate # activate it 
# installing everything
pip install --upgrade pip
python3 -m pip install numpy 
python3 -m pip install matplotlib
python3 -m pip install scipy
python3 -m pip install uproot
python3 -m pip install --upgrade setuptools
python3 -m pip install setuptools_scm

python3 setup.py install

deactivate
cd ..
