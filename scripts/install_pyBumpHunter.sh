#!/bin/bash

cwd=$(pwd)


pip3 install virtualenv -t ${cwd}/pyBumpHunter/virtualenv
python3 -m venv ${cwd}/pyBumpHunter/pyBH_env
source ${cwd}/pyBumpHunter/pyBH_env/bin/activate # activate it 

packagepath=$(python3 -c "import site;print(site.getsitepackages()[0])")

# installing everything
python3 -m pip install --upgrade pip -t ${packagepath}
python3 -m pip install numpy -t ${packagepath}
python3 -m pip install matplotlib -t ${packagepath}
python3 -m pip install scipy -t ${packagepath}
python3 -m pip install uproot -t ${packagepath}
python3 -m pip install --upgrade setuptools -t ${packagepath}
python3 -m pip install setuptools_scm -t ${packagepath}

cd ${cwd}/pyBumpHunter

#only works if cd'ed into pyBumpHunter directory before, --prefix does not help:
python3 setup.py install

cd ${cwd}

deactivate
