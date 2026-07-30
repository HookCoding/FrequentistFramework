#xmlAnaWSBuilder
rm -rf xmlAnaWSBuilder
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/xmlAnaWSBuilder.git --branch tofitsch_baseline_fit
cd xmlAnaWSBuilder
git checkout 6b84050f3c0206a6f30eb40b103cc101e68505cc
cd ..

#quickfit
rm -rf quickFit
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/quickFit.git --branch tofitsch_baseline_fit
cd quickFit
git checkout 0408030b6c8d74a2e2c27a864a02756132d08f5a
cd ..

#workspaceCombiner
rm -rf workspaceCombiner
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/workspaceCombiner.git --branch tofitsch_baseline_fit
cd workspaceCombiner
git checkout 7d484ad3f89c4075d2c567aa4503fc56e1bb9468
cd ..

for x in xmlAnaWSBuilder quickFit workspaceCombiner; do

  cd $x

  . setup_lxplus.sh

  . scripts/install_roofitext.sh

  . setup_lxplus.sh

  cd RooFitExtensions

  rm -rf build
  mkdir build
  cd build
  cmake ..
  make
  cd ../..

  rm -rf build
  mkdir build
  cd build
  cmake ..
  make

  cd ../..

done

# pyBumpHunter
rm -rf pyBumpHunter
git clone https://github.com/scikit-hep/pyBumpHunter.git
cd pyBumpHunter

git checkout 91f49a622bd77622edb02a1a2788fc12835e5b72

python3 -m venv pyBH_env
. pyBH_env/bin/activate

python3 setup.py install

deactivate
cd ..
