#!/bin/bash
# Adapted from install.sh: dependencies already cloned from GitHub mirrors
# (tofitsch/xmlAnaWSBuilder, tofitsch/quickFit, tofitsch/workspaceCombiner,
# scikit-hep/pyBumpHunter) at the commits pinned in install.sh.
# RooFitExtensions is pre-cloned from the public GitLab URL since the
# kerberos URL in scripts/install_roofitext.sh is not always available.

set -x

FF_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RFE_CACHE=$FF_DIR/.rfe_cache

# pre-clone RooFitExtensions once at the pinned commit
if [ ! -d "$RFE_CACHE" ]; then
  git clone https://gitlab.cern.ch/atlas_higgs_combination/software/RooFitExtensions.git "$RFE_CACHE" || exit 1
  git -C "$RFE_CACHE" checkout ba94bfcbfa4f4a4e3541ade09580399e409e8514 || exit 1
fi

for x in xmlAnaWSBuilder quickFit workspaceCombiner; do
  (
    cd "$FF_DIR/$x" || exit 1

    if [ ! -d RooFitExtensions ]; then
      cp -r "$RFE_CACHE" RooFitExtensions
    fi

    . setup_lxplus.sh

    . scripts/install_roofitext.sh

    cd "$FF_DIR/$x"

    rm -rf build
    mkdir build
    cd build
    cmake .. || exit 1
    make -j4 || exit 1
  ) > "$FF_DIR/install_$x.log" 2>&1
  echo "=== $x done (exit $?) ==="
done

# pyBumpHunter
(
  cd "$FF_DIR/pyBumpHunter" || exit 1

  # need a python3: use the LCG view
  export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
  source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
  lsetup "views LCG_102a x86_64-centos9-gcc11-opt"

  rm -rf pyBH_env
  python3 -m venv pyBH_env
  . pyBH_env/bin/activate

  python3 setup.py install

  deactivate
) > "$FF_DIR/install_pyBumpHunter.log" 2>&1
echo "=== pyBumpHunter done (exit $?) ==="
