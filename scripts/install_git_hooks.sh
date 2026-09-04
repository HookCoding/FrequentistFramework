#!/usr/bin/env bash
# One-time setup: point this checkout's git hooks at the repo-tracked
# .githooks/ directory, so the mandatory pre-commit gate
# (.githooks/pre-commit) actually runs. See README.md's "Mandatory
# pre-commit gate" section and doc/TIER2_SYSTEM.md's "Optional
# pre-commit configuration" section for what this does and does not
# require (no third-party `pre-commit` package, no new dependency).

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

echo "Installed: git hooks now point at .githooks/ (core.hooksPath=.githooks)."
echo "The mandatory pre-commit gate (.githooks/pre-commit) will run on your next 'git commit'."
