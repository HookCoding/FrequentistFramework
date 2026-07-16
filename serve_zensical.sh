#!/usr/bin/env bash
# Serve the Zensical documentation with live reload for local testing.
#
# Usage: ./serve_zensical.sh [port]   (default port: 8000)
#
# Run this in a clean shell, i.e. one where setup.sh has NOT been sourced:
# the LCG view replaces the Python environment and Zensical needs python3.12.

set -euo pipefail

PORT="${1:-8000}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HOME/.zensical-venv"

if [[ -n "${ATLAS_LOCAL_ROOT_BASE:-}" || -n "${LCG_VERSION:-}" ]]; then
    echo "WARNING: this shell looks like it has the ATLAS/LCG environment set up." >&2
    echo "         If zensical fails below, retry from a fresh shell (without sourcing setup.sh)." >&2
fi

# Create the venv and install zensical on first use
if [[ ! -x "$VENV/bin/zensical" ]]; then
    echo "Installing zensical into $VENV (first run only) ..."
    python3.12 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip zensical
fi

HOST_FQDN="$(hostname -f)"

echo
echo "==============================================================="
echo " Serving docs on port $PORT"
echo
echo " If you ran this on your OWN machine, open:"
echo "     http://localhost:$PORT"
echo
echo " If you ran this on LXPLUS, first open an SSH tunnel from your"
echo " laptop to THIS node (lxplus.cern.ch load-balances, so use the"
echo " full hostname):"
echo "     ssh -N -L $PORT:localhost:$PORT $USER@$HOST_FQDN"
echo " then open:"
echo "     http://localhost:$PORT"
echo "==============================================================="
echo

cd "$REPO_DIR"
exec "$VENV/bin/zensical" serve -a "localhost:$PORT"
