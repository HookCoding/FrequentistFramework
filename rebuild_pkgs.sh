#!/bin/bash
# Rebuild the three C++ packages with CMAKE_POLICY_VERSION_MINIMUM=3.5
# (lsetup cmake provides cmake >= 4, which rejects cmake_minimum_required(3.1))

set -x
FF_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

for x in xmlAnaWSBuilder quickFit workspaceCombiner; do
  (
    cd "$FF_DIR/$x" || exit 1
    . setup_lxplus.sh
    rm -rf build
    mkdir build
    cd build
    cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 .. || exit 1
    make -j4 || exit 1
  ) > "$FF_DIR/rebuild_$x.log" 2>&1
  echo "=== $x done (exit $?) ==="
done
