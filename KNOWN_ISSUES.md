# Known issues

Known bugs, limitations and deliberately unguarded edge cases, stated openly. Recording an
issue here is the obligation; fixing it is a choice — not every problem needs to be fixed, and
not every edge case needs to be explicitly guarded, or a framework this size would drown in
defensive code written for situations that never arise. What is not acceptable is a known
problem that is *undisclosed*: the next person then rediscovers it as a wrong physics number
rather than as a documented limitation.

Each entry: what it is, where it lives, what it affects, and whether it is deliberately left
alone. Updated whenever an issue is found, fixed, or consciously accepted.

| Issue | Where | Affects / status |
|---|---|---|
| `SetSeed(0)` makes pseudo-data generation genuinely non-deterministic; the deterministic variant sits commented out on the line above | `python/generatePseudoData.py:66-67` | Pseudodata generation only, off the J50/J100 fit path. Left alone. |
| `setup_buildCombineFit.sh` does not exist, but is sourced by **eight** live call sites | `scripts/run_nloFit.sh:6` and 7 others | The NLO-fit driver and its dependents; already broken before any of this work. Left alone. |
| `install_quickFit_and_xmlAnaWSBuilder.sh` does not exist, but is sourced | `scripts/install_FrequentistFramework.sh:14` | That install script only; not on the `install.sh` path this repo actually uses. Left alone. |
| `re.sub("PAR1", …)` runs before `PAR10`, corrupting any ten-parameter card | `python/run_anaFit.py:276-279` | Only `tenPar`-style cards; harmless at the five/six parameters J50 and J100 use. Left alone. |
| XMLReader and quickFit only *warn* on failure and still return 0; nothing gates on their exit codes, so a failed fit can look like a successful one | `python/run_anaFit.py:44,71` | Every fit. This is exactly why `tests/repro.py check` (once built) will diff baseline outputs rather than trust exit codes. Left alone at the source; worked around in the harness. |
| `gRand.SetSeed()` is a no-op — `TH1::FillRandom` samples from the global `gRandom`, so these are only accidentally reproducible | `python/InjectGaussian.py:67-68`, `python/InjectZprime.py:118-119` | Signal-injection studies, off the J50/J100 fit path. Left alone. |
| Hardcoded personal checkout path, so the HTCondor path runs someone else's framework at an unknown version | `submission/condor_script.sh:19,24` | HTCondor toy studies only, out of this plan's scope. Left alone. |
| Absolute AFS/EOS paths in other people's accounts, live in tracked config | `config/dijetisrTLA/*`, `python/inject_zprime_dscblimits.sh` | The (already inert) Run 3 ISR TLA flavour and Z' injection limits. Left alone. |
| Hardcoded input path returning *Permission denied*, and `--end` defaults to 1000 GeV | `python/createBinning.py` | The auto-rebinning fallback; both Run 2 drivers bypass it via `--rebinfile`/`--rebinhist`. Left alone. |

All nine were found during the survey behind
[plans/2026-09-15-reproducibility-lock.md](plans/2026-09-15-reproducibility-lock.md), verified,
and confirmed off the J50/J100 path — which is why they are disclosed here rather than fixed.
