#!/bin/bash

cd pyBumpHunter

pip3 install virtualenv -t virtualenv
python3 -m venv pyBH_env
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
