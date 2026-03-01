#cd quickFit/RooFitExtensions

#quickfit
rm -rf quickFit
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/quickFit.git --branch tofitsch_baseline_fit
cd quickFit
git checkout 0408030b6c8d74a2e2c27a864a02756132d08f5a
cd ..

#xmlAnaWSBuilder
rm -rf xmlAnaWSBuilder
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/xmlAnaWSBuilder.git --branch tofitsch_baseline_fit
cd xmlAnaWSBuilder
git checkout 6b84050f3c0206a6f30eb40b103cc101e68505cc
cd ..

for x in xmlAnaWSBuilder quickFit; do

  cd $x

  . setup_lxplus.sh

  . scripts/install_roofitext.sh

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
