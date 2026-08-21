# Tier-1 environment provenance and pinning

This document records the verified split between the development quality environment and the scientific analysis environment.

## Development quality environment

- Python executable: `.venv/bin/python`
- Python: 3.12.13
- Project requirement: Python 3.11 or newer
- pytest: 9.1.1
- Ruff: 0.16.0
- Black: 26.5.1

Dependency records:

- `requirements-dev.txt`
- `requirements-dev-lock.txt`

Latest full lightweight gate:

- 105 collected;
- 101 passed;
- 2 dependency tests deselected;
- 2 strict expected failures;
- Ruff and Black passed;
- exit code 0.

A clean Python 3.12 environment reproduced the locked tool versions and passed the full lightweight gate at its recorded checkpoint. Bootstrap pip is not pinned.

## Scientific analysis environment

`scripts/setup_buildAndFit.sh` sources the XMLReader and quickFit setup scripts, both selecting:

- LCG `LCG_102a`
- platform `x86_64-centos9-gcc11-opt`
- Python 3.9.12
- ROOT/PyROOT 6.26/08

Python executable:

```text
/cvmfs/sft.cern.ch/lcg/views/LCG_102a/x86_64-centos9-gcc11-opt/bin/python
```

ROOT 6.40.02 describes the shell before authoritative setup, not the runtime used by the successful J100/J50 fits.

## External revisions

- `xmlAnaWSBuilder`: `6b84050f3c0206a6f30eb40b103cc101e68505cc`
- `quickFit`: `0408030b6c8d74a2e2c27a864a02756132d08f5a`
- `workspaceCombiner`: `7d484ad3f89c4075d2c567aa4503fc56e1bb9468`
- `pyBumpHunter`: `91f49a622bd77622edb02a1a2788fc12835e5b72`

No tracked source modifications were present in these prepared checkouts.

Setup-script hashes:

- XMLReader setup: `34ca7d4db40cdd60ca998fc3ca62cd8ab625f87ed6c7dde66b2140bd6b1a5e27`
- quickFit setup: `217a2a72104ab257e302fa588d44afc2beaaa6a333991acf7de8af8233b3d917`

## Canonical input hashes

- J100 data: `f6336bc2d0a966559072241be2d547ecd6b4b5bcae11e3c33751e25ce2a5d0e6`
- J50 data: `4d2e0184ac95ee23bf1e74fef0a15cc86bf4a1f8342d90f703441fe90fbab3ee`
- Top template: `4d6d73b0445ad0e9777fabb6c734ec49fed9317801ffc19aa86692a3cb911807`
- Category template: `69b23311719bbe8f5e6e49f951fc479235e6b2cd889d8ba201e059b2674862d0`
- Six-parameter background template: `7d3d322bbf79734b0c65f9d407ec7316cd84ee9cd471e97c1d73b773807dda10`
- Signal template: `d7ae0ebc4aa3a234cae5c99d21dc5092278d10b22463c67f3048447ee41be314`

## Schema-version-2 manifests

Canonical manifests:

- `run/fits/J100/run_481_3000_sixPar/analysis_results.json`
- `run/fits/J50/run_344_2079_sixPar/analysis_results.json`

They record runtime, dependency revisions, input and configuration hashes, invocation details, success state, masking state, and accepted chi-square p-value.

Canonical results:

- J100 `p_chi2`: `0.018448750724012808`
- J50 `p_chi2`: `0.07853114301666252`
- both unmasked

## Verification commands

Development gate:

```bash
source .venv/bin/activate
python scripts/quality_check.py --mode full
```

Prepared dependency gate:

```bash
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v
```

Runtime readiness:

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -k authoritative_setup_provides_scientific_runtime -v
```

Scientific characterization:

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

Latest scientific result: 1 passed, 2 deselected, 116.02 seconds, exit code 0.

## Known limitations

- Missing Git submodule gitlinks
- Destructive `install.sh`
- Clean-clone scientific acquisition incomplete
- Hosted CI pending push
- CLs intentionally deferred
- Numerical tolerances provisional
- Bootstrap pip unpinned
