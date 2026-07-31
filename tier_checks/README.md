# Modular Tier 1 and Tier 2 checks

This directory is self-contained and intended to live at the repository root as `tier_checks/`.
Each sub-requirement has one discoverable `check_*.py` file. The command automatically scans
`tier1/` and `tier2/`, imports each file, and runs its exported `CHECK` object.

## Commands

```bash
# Detect all checks
python tier_checks/check_tiers.py --list

# Fast static and metadata checks for both tiers
python tier_checks/check_tiers.py --tier all --depth fast

# In-depth Tier 1 checks with detailed output
python tier_checks/check_tiers.py --tier 1 --depth in-depth --detail verbose

# In-depth checks for both tiers, plus a JSON report
python tier_checks/check_tiers.py --tier 1 --tier 2 --depth in-depth \
  --detail verbose --json-out tier12-report.json
```

## Depth definitions

- `fast`: paths, recorded inputs and outputs, reference schema, Python version, pinned tool versions, and dependency files. It does not run test, lint, formatting, or reference-regeneration subprocesses.
- `in-depth`: runs behavioral checks such as reference regeneration, targeted pytest, Ruff, Black, and the existing full quality gate. Fast-only checks are reported as skipped, so use both depths when you want two separately archived reports.

## Adding a check

Create `tier_checks/tier1/check_name.py` or `tier_checks/tier2/check_name.py`. Define a `TierCheck` subclass and expose one module-level instance named `CHECK`. No central registry needs editing.

## Safety boundary

The suite never starts the full J100/J50 fit workflows. It validates their recorded scripts, inputs, existing outputs, references, tests, and quality tooling without initiating expensive analysis jobs.
