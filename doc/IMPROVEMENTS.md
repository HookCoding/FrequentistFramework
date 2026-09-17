# Improvements

One living document for the whole reproducibility/refactoring effort: what the framework now
does, why it was changed, and how it is meant to be used. Rewritten in place as things evolve —
this describes the *current* state, not history. History is [CHANGELOG.md](../CHANGELOG.md).

## Reproducibility harness (`tests/repro.py`)

**Why.** Before any significant change to the repository, there has to be a way to *prove* a
change did not move a physics number. Plan:
[plans/2026-09-15-reproducibility-lock.md](../plans/2026-09-15-reproducibility-lock.md).

**What exists now.** Four subcommands:

```
python3 tests/repro.py selfcheck
python3 tests/repro.py env
python3 tests/repro.py record {J100,J50} [DIR] [--force --reason "..."]
python3 tests/repro.py check [--quick] [--from DIR [--analysis {J100,J50}]] [--tol-scale SCALE]
```

`selfcheck` runs the comparator against synthetic data — no ROOT, no ATLAS environment, instant.

`env` verifies the software stack against the files that already declare each pin, rather than
inventing a second source of truth: the four sub-framework SHAs in `install.sh` against
`git rev-parse HEAD` in each gitignored clone; the RooFitExtensions SHA in each sub-framework's
own live `scripts/install_roofitext.sh`; agreement of the `lsetup "views …"` line across all
three `setup_lxplus.sh`; the pyBumpHunter venv's `pyvenv.cfg` against that view and Python 3.9.12;
the installed egg's version against the short SHA of the pyBumpHunter pin it parsed from
`install.sh` (so a deliberate pin bump reports "the venv needs rebuilding", not a disagreement with
a constant — [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 25, fixed 2026-09-17); and that none of
the four clones have modified tracked files. It also computes the SHA-256 of the two built binaries and compares them against the
digests in every existing baseline's provenance — a rebuilt `XMLReader` or `quickFit` now fails
`env` (and therefore `check`, which runs `env` first) instead of passing silently. A deliberate
rebuild is expected to change the digest; the fix is to re-cut the baseline (`record --force
--reason "..."`), not to suppress the check.

It compares the live pins against each baseline's recorded `provenance.pins` on the same terms —
the four clone SHAs, the three `RooFitExtensions` SHAs, the LCG view, the venv's Python version and
the installed egg version — and fails on any difference, naming the pin and the way out. Without
that, `env` passing meant only "this tree agrees with `install.sh` as it currently reads", not
"this is the stack the baselines were cut with": a deliberate pin bump, re-clone and venv rebuild
passed every check, because both the clone-SHA check and the egg check derive their expectation
from the declaration that moved ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 35, fixed 2026-09-17).
All three provenance blocks are now read back — `pins` and `binary_sha256` fail, `versions` warns.

It separately *records without asserting* the
resolved ROOT, `cmake` and numpy/scipy/uproot versions the BumpHunter
step actually sees, reading the LCG
view's own `bin/` directly on CVMFS rather than through `lsetup` (see *Versions that cannot be
pinned* below for why).

Those versions matter to the analysis — they drive the 10 000 pseudo-experiments behind
`global_Pval` — even though nothing here can pin them, so the plan's amended §1 requires a
durable record of the versions each baseline was produced with, held in the baseline provenance
block. `env` reads every `tests/baseline_*.json` that exists and compares the live values against
each one's own `provenance.versions` in turn, naming the file in the warning, non-fatally on any
difference and never failing the command. Before any baseline exists it says so and compares
nothing. `env` never writes that record — only `record` does, and only when building a new
baseline from scratch.

The pins `record` writes into a baseline's provenance are each clone's *observed* `git rev-parse
HEAD` (including each sub-framework's `RooFitExtensions` checkout), not the declaration `env`
parses out of `install.sh`/`install_roofitext.sh` — identical on a tree where `env`'s own checks
already assert the two agree, so this changed nothing about the committed baselines, but a
provenance block that recorded the *intended* SHA instead of the one that actually built the
binaries would defeat its own purpose on a drifted tree. `record` also now runs the same checks
`env` does and refuses to write a baseline if any of them fail, unless given the same `--force
--reason "..."` it already requires to overwrite an existing one — a baseline is only useful if
its provenance describes the tree that actually produced it. **Which checks failed is printed
either way**, because overwriting an existing baseline always needs `--force`, so gating the
report on it meant the only route anyone is documented to take was also the one that never showed
what was wrong with the tree it was cutting from ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 32,
fixed 2026-09-17). Two limits of that gate are recorded under the same issue and left alone: it
reads the pin checks only, not the binary digests, and `record` reads its numbers from a run
directory that may predate the binaries whose digests it records — so **re-run the fit before
re-cutting a baseline**, rather than re-cutting from an older run directory.

`env` is not yet a reproducibility check of the fits themselves — that is `check`, below.

`check` is the end-to-end entry point. It runs `env` first and stops (without touching any fit)
if a pin check fails — `env`'s version *warnings* never stop it, but are printed before anything
else so a mismatch further down is read with them already in view. It then verifies every
selected analysis's input spectra SHA-256 against its baseline's `provenance.input_sha256`,
before running any driver, and stops on the first mismatch — so a full `check` never spends
minutes fitting J100 only to discover afterwards that a J50 input moved. *Selected* is the
operative word: `--quick` verifies J100's two inputs and not J50's, which is all a J100-only
comparison depends on ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 37). Only once every selected
analysis's inputs check out does it, for each in turn, wipe any stale scratch output from a
previous run (so a driver that crashes outright cannot be masked by leftover files), run the
driver with `OUT_DIR` pointed at
`run/check_scratch/` — `run/` is already gitignored wholesale, so nothing new needed adding there,
and the recorded `run/run_481_3000_sixPar/`/`run/run_J50_302_2997_sixPar/` are never touched — and
compares the result against the baseline with `compare()`. The comparison is *everything the
baseline holds* except the keys that describe the baseline rather than the fit — `provenance`,
`analysis` and `source_dir`, none of which a candidate has a counterpart for. That is a blocklist
rather than a whitelist deliberately: naming the three keys to compare, as this used to, meant a
section added to `record` later would be recorded, committed and silently never checked
([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 33, fixed 2026-09-17). Today it selects exactly
`unmasked`, `masked` and `directory_listing`, as before. It does not gate on the driver's own exit code — XMLReader/quickFit
warn-and-return-0 on failure (`KNOWN_ISSUES.md`), so the baseline diff is the actual failure
detector.

Two speeds: `check --quick` runs J100 only, skipping J50's BumpHunter masking path; plain `check`
runs both. `check --from DIR` compares an existing output directory instead of running a driver —
the escape hatch for when a refactor has renamed the drivers or run directories and the built-in
`ANALYSES` table has gone stale. It infers which baseline `DIR` belongs to from the directory's
own name, falling back to an explicit `--analysis J100|J50` when that is ambiguous. `--tol-scale`
widens both the `rtol` and `atol` terms of the tight/pvalue tolerance classes for a cross-machine
comparison (plan §4) — both terms, not just `rtol`, because a baseline value near zero needs its
`atol` widened too for the scale to have any effect at all ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md)
issue 19, fixed 2026-09-17: renamed from `--rtol`, which undersold what it actually does).

### Versions that cannot be pinned

The resolved ROOT and `cmake` versions, and the numpy/scipy/uproot versions the BumpHunter step
sees, are read straight from the LCG view's own directory on CVMFS
(`/cvmfs/sft.cern.ch/lcg/views/<view>/bin/{root-config,cmake}`) rather than by asking `lsetup` to
put them on `$PATH` first. In this session's non-interactive shell, `lsetup`'s `PATH` edits do
not survive being probed in isolation — a bare `lsetup "views …"` followed by `cmake --version`
silently resolves the system's `/usr/bin/cmake` instead of the view's. Going to the view's own
`bin/` sidesteps that entirely and is what the framework's own compiled binaries were actually
built against.

The numpy/scipy/uproot probe is different: there is no file to read the answer from, because the
question is whether `python/FindBHWindow.py`'s actual activation line
(`source pyBH_env/bin/activate; python3 ...`) can import them at all. That probe replicates the
real invocation context — `scripts/setup_buildAndFit.sh`, exactly as every driver sources it,
not a simplified one-line stand-in — before activating the venv. See `CHANGELOG.md`'s 2026-09-16
`record` entry for why the simplified version of this probe gave a false negative.

**The comparator.** `compare(baseline, candidate, tol_scale=1.0)` flattens two nested
dict/list structures to dotted key paths and compares every leaf:

- **tight** (`rtol=1e-6, atol=1e-8`): fitted parameters and errors, `minNll`, `chi2`,
  `chi2/ndof`, postfit bin contents, the data integral.
- **pvalue** (`rtol=1e-5, atol=1e-8`): the rebinned chi2 p-value, BumpHunter `global_Pval` and
  `significance`.
- **exact**: `status`, `covQual`, `nbins`, `npars`, `ndof`, `MaskMin`, `MaskMax`, `BlindRange`,
  `seed`, `npe`, the directory listing, and **anything not otherwise classified** — an
  unclassified leaf fails on the last ULP rather than passing on a real move, which is the safe
  direction, but a float compared that way fails for a reason that has nothing to do with the
  physics. So an unclassified *numeric* leaf now says so in the failure text (`compared exactly:
  leaf 'x' has no tolerance class …`) instead of reporting a bare `exact match required`, which
  reads like a finding. A rewrite of `ExtractPostfitFromWS.py` that adds a labelled chi2 bin is
  the expected way to reach this ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 34, fixed
  2026-09-17): add the new leaf to `TOLERANCE_BY_LEAF`.

Environment-observation keys (ROOT version, active view) never reach `compare()` at all — `check`
deliberately excludes `provenance`, the baseline's own metadata, from the comparison, since a
candidate has no provenance of its own to compare it against. `env` is what reports environment
drift (see above); the comparator no longer carries a separate, weaker "note" class for the same
job, which used to exist but could never fire in practice ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md)
issue 16, fixed 2026-09-17).

A missing or extra key between baseline and candidate is always a failure. Every mismatch is
reported, not just the first. `tol_scale` widens both float classes' `rtol` and `atol` terms at
once, for the cross-machine case.

Two cases are handled before the tolerance test, because a float comparison quietly gives the
wrong answer for both. **NaN**: every comparison against NaN is false, so an unguarded tolerance
test passes a NaN candidate against any baseline value — exactly the silent agreement this harness
exists to prevent, since a fit that fails into NaN is one of the things XMLReader/quickFit's
warn-and-return-0 behaviour can produce. One side NaN is now a mismatch, both sides NaN a match
([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 22, fixed 2026-09-17). **A leaf whose type changes**
(a float against a string, say) is reported as `type changed: float -> str` rather than raising
`TypeError` out of the arithmetic (issue 26, same day).

All four subcommands are built. `run_env_checks()` is shared by `env` and `check` rather than
reimplemented in the latter; `compare()` is used by `record`'s own `selfcheck` test and by
`check`, which is the only subcommand that builds a candidate to feed it — `env` deliberately does
not use it (see the design note in `tests/repro.py` above the `env` code: most of its checks are
mutual-agreement or dirty-file assertions, not a baseline-vs-candidate comparison).

§6 is done: the dead `scripts/install_roofitext.sh` and the inert `.gitmodules` are deleted,
`install.sh` clones the three sub-frameworks from their public GitHub mirrors instead of the
unreachable CERN GitLab URLs (SHA pins unchanged), and the stale `README.md`/`CLAUDE.md`
documentation (the `LCG_105` venv row, the missing RooFitExtensions/`cmake` pins, the
"submodules" and "no test suite"/`requirements.txt` notes) is corrected. The README's
"Reproducibility" section was added alongside `check` in the previous step.

Verification closed the plan out: `config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template`'s
`p6` range was tightened from `[-0.1, 0.1]` to `[-0.1, 0.04]` — below its baseline best-fit value
of `0.0478` — and `check --quick` re-ran the J100 driver for real and failed with dozens of
readable postfit-bin mismatches, not a hand-edited baseline. Reverting the card and re-running
produced a clean PASS again. `run/run_481_3000_sixPar/`'s file mtimes were confirmed to all
predate this work, and the final `git status` carries no unexpected changes.

**What is next.** The harness (`tests/repro.py`'s `selfcheck`/`env`/`record`/`check`) is built,
documented and verified end to end, and the gaps the original survey found are closed. An audit of
this implementation against the plan, on 2026-09-16, found ten things outstanding, filed as issues
12–21 in [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) with the fix each one needed; all ten are now fixed,
the last (issue 21, re-adding the parser unit tests) on 2026-09-17. Nothing from that audit remains
open, and every requirement of the plan is implemented.

A second review on 2026-09-17, after those ten were closed, found six further things — issues
22–27, none of which affected a recorded number. Five of them were introduced by this work and are
now fixed: the comparator's NaN hole (22) and its type-change/malformed-baseline crashes (26), the
egg check's hardcoded constant (25), a stale sentence in `KNOWN_ISSUES.md` itself (24), and the
"CERN GitLab" description the §6 repoint made untrue (27).

**One is left open deliberately: issue 23.** J50's BumpHunter step writes `bump.png` and
`BH_statistics.png` into the repository root rather than the run folder, so a `check` rewrites them
there — outside the scratch directory, though still never touching `run/`. That write has been in
`FindBHWindow.py` since 2021, so it is a fit-path bug this work inherited rather than caused; it is
recorded and left for whenever the fit path is next opened. The isolation described above is
accurate for everything else.

A fourth review on 2026-09-17 sorted the harness by a sharper question than the earlier ones asked:
**can this make `check` reach the wrong verdict?** It found six more things, filed as issues 32–37,
and **all six are fixed** — every one lived in `tests/repro.py` or its documentation rather than on
the fit path. Two of them had a false-pass route, which is the class
[CLAUDE.md](../CLAUDE.md)'s triage rule puts first: `record --force` silenced the env gate on the
only re-cut route anyone is documented to take (32), and `_check_one`'s top-level whitelist would
have ignored a section added to `record` later (33). One had a false-fail route the refactor reaches
by itself (34, the bit-exact default). The other three change no verdict: 35 closes the last
provenance block that was recorded and never read back, 36 hardens a parser against an arrangement
`install.sh` does not currently contain, and 37 corrects a stale claim about `--quick`. The question
also **reordered** the earlier labels — 35 is issue 12's twin and was first reported as Medium, but
it cannot move a verdict, only the diagnosis, so it ranks below 33. The committed baselines were not
re-cut; `check --from` passes unchanged against both recorded run directories after the fixes.

A third review on 2026-09-17 re-ran the harness — `selfcheck`, `env` 24/24 and `check --from`, the
last of these a path nothing had exercised before — and confirmed again that every requirement of
the plan is implemented. It found four more problems, filed as issues 28–31, all of them one defect
in four places: a condition the harness should *report* instead makes it raise. **All four are
recorded and none is fixed**, under the triage rule now written into [CLAUDE.md](../CLAUDE.md):
they all fail closed, so none can let an analysis complete with a silently wrong number, and two of
the four are unreachable for anyone following the documentation. Issue 29 — the extractors crashing
when a PostFit file's *contents*, rather than its name, have changed — is the one to revisit first
if `ExtractPostfitFromWS.py` is opened, since a rewrite of it trips that path by itself.
