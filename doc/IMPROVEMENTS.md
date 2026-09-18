# Improvements

One living document for the whole reproducibility/refactoring effort: what the framework now
does, why it was changed, and how it is meant to be used. Rewritten in place as things evolve —
this describes the *current* state, not history. History is [CHANGELOG.md](../CHANGELOG.md).

## The fit path's own verdict (`run_anaFit.py` and the Run 2 drivers)

The framework computes one verdict on whether a fit is usable at all. If p(chi2) falls below
`--maskthreshold` (default 0.01), `python/FindBHWindow.py` locates the most significant window, the
fit is repeated with that window blinded, and if p(chi2) *still* fails, `run_anaFit()` prints
`Exiting with failed fit status.` and returns `-1`.

**That verdict is now reported.** It used to be discarded twice over — `main()` called
`run_anaFit(…)` as a bare statement, so `sys.exit(None)` exited 0, and neither driver checked the
exit code anyway — which meant a twice-rejected fit produced the same files, the same plots and the
same successful exit as an accepted one ([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 38, fixed
2026-09-17). Now:

- `main()` returns `run_anaFit(…)`, so the status reaches `sys.exit`.
- `scripts/run_anaFit_run2.sh` and `scripts/run_anaFit_run2_J50.sh` capture it, print an explicit
  `ERROR: … this result must not be used` banner, and report it as their own exit status.
- **The plots are still produced on a failure**, deliberately: they are the diagnostics you want in
  order to see why the fit failed. What is no longer possible is the run reporting success.
- The status is carried by a `( exit … )` subshell rather than `exit`, because both drivers are
  `{ … }` brace groups their own headers tell you to *source* — a bare `exit` would kill an
  interactive shell — while `tests/repro.py` runs them with `bash`.

Anything that checks these drivers' exit status will therefore start seeing real failures it
previously missed. That is the point of the change, but it is worth knowing before pointing the
HTCondor path at it.

**The parameter count is now cross-checked against the card.** `nPars` is derived by testing the
background file's path for the words `three`…`ten`, falling back to 5 when none matches. The card
itself is the authority — it declares `p1…pN` with `[PARn, …]` placeholders — so `run_anaFit.py`
now compares the highest `PAR` index the card declares against `nPars` before the prefit runs, and
stops with both numbers if they disagree; a card with no placeholders at all warns instead. All
twelve tracked background cards pass; a `sixPar` card renamed `…_6Par` or `…_tenPar` is refused
([KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 42, fixed 2026-09-17).

**Fit quality is now reported on every fit.** `report_fit_quality()` reads `status()` and
`covQual()` from the `fitResult` immediately after `quickFit` and **before anything is extracted**,
and prints one line:

```
FIT QUALITY: status=1 covQual=2 (full, but forced positive-definite) [.../FitResult_anaFit_sixPar_bkgOnly.root]
```

Every fit this repository has recorded is `status=1, covQual=2` — MINUIT had to force the
covariance matrix positive-definite, adding ~0.005 to the diagonal, while the log's closing line
read `Fit Summary of POIs (STATUS OK)`. The central values are sound: the minimum is `Valid` and
the retries land on the same FCN. The **errors** come from that forced matrix, and the errors are
what the spurious-signal, injection-linearity and limit studies consume — which is why this is
worth seeing on every run rather than never (issue 40).

`--mincovqual` (default **2**) refuses anything worse. The default accepts exactly what is on
record and refuses a degradation, so it cannot invalidate the two locked analyses while still
catching the case the issue was filed about. **Whether `covQual=2` is itself good enough for these
fits is a physics judgement and is deliberately not made here** — the framework can now state the
property and be told what to do about it, which is the whole of the change.

**The goodness-of-fit gate is defined on `<channel>_bkgonly_rebinned`**, in both the masked and
unmasked cases. It used to differ by branch — the unmasked gate read `<channel>_rebinned` — and the
two differ by 1–2% relative, so a fit landing between them was accepted or rejected according to
which branch it took. The gate asks whether the *background model* describes the data, so the
background-only distribution is the one it is read from; for a masked b-only fit that is also the
correctly normalised distribution, which is why the masked branch already used it. Settled by the
repository owner on 2026-09-18 (issue 39). `plot_postfit.cpp` reads the same distribution, so the
gate and the plot judge the same thing.

**One thing is recorded and deliberately not fixed**, because it needs a judgement rather than an
edit: a latent exclusion of empty bins from the chi2 (issue 41 — verified not triggered by anything
recorded, but a reach extension into the sparse high-mass tail is what would trigger it).

**A failed workspace build or fit now stops the run.** `XMLReader`, `quickFit` and `quickLimit`
used to have a non-zero exit met with `WARNING: Non-zero return code … Check if tolerable`, after
which extraction proceeded anyway. They all go through `execute_checked()` now, which raises and
names the command, the exit code, the signal where the code is above 128, and the log file. These
binaries do signal hard failures — a nonexistent card makes `XMLReader` exit 139 (SIGSEGV) — so
what was happening was that a real signal was being discarded.

This and the `covQual` reporting above cover different halves of the same question and neither
replaces the other: `execute_checked` catches a binary that **died**, `report_fit_quality` catches
a fit that **ran badly and exited 0**. Note that the `--dolimit` path is not exercised by either
locked analysis, so `quickLimit`'s gate is reasoned-about rather than regression-tested.

**Two input mistakes that used to pass silently are now refused.**

- **A half-given `--rebinfile`/`--rebinhist` pair.** These are a pair, but `if rebinfile and
  rebinhist` treated "one given" as identical to "neither given" and fell through to a fallback
  binning that `createBinning.py` generates only up to 1000 GeV — while both Run 2 drivers fit to
  3000 and 2997. That silently moved the rebinned chi2, the p-value `--maskthreshold` gates on, and
  the BumpHunter window. Refused now at the top of `run_anaFit()`, before any fitting, and in
  `PostfitExtractor.__init__`, which also covers `ExtractPostfitFromWS.py`'s standalone CLI
  (issue 46). Only one direction was ever silent: the drivers must quote `--rebinhist "$rebinhist"`
  because the J100 histogram name contains spaces, so an emptied variable arrived as `''` and was
  falsy, where an emptied `--rebinfile $rebinfile` made the word vanish and argparse already
  refused.
- **Running a driver from the wrong directory.** `scripts/setup_buildAndFit.sh` refuses outside the
  repository root with `return 1`, but `return` in a sourced script returns only from that script —
  every driver carried on regardless, created `run/` in the wrong place and entered the fit chain
  with no CVMFS environment. All six drivers that source it now test the status and stop
  (issue 43).

## The postfit plots

Every run produces two plots of the same fit, from two different programs, and they are not
equivalent.

- `post_fit.pdf` — `plot_postfit.cpp`, run through ROOT. Loads both the unmasked and masked fits,
  labels each, and prints `χ2/Ndof` and `p-val` for the native and rebinned versions of both.
- `postFit.pdf` — `python/plotPostFit.py`. One fit, one number.

The C++ macro has repeatedly turned out to be the more careful of the two, which is worth knowing
before trusting the Python one in a new situation.

**Neither plot is checked by `tests/repro.py`.** The baselines record plot **filenames** in
`directory_listing` and nothing else about them — `grep` for `pdf` in `tests/repro.py` returns
nothing. Issues 44, 45 and 48 would all have passed a green `check`, and all three were found by
reading code. The lock protects numbers, not plots; read a plot on its own merits.

**Fixed:** `plotPostFit.py` labelled its number `#chi^{2}/ndof` while reading **bin 6** of the chi2
histogram, which holds the p-value (bin 2 is `chi2/ndof`). Every plot it drew showed the p-value
under the wrong name — 0.496 for J100 where the true reduced chi2 is 1.000, and 0.078 for J50
against a true 1.039. Both are *plausible* reduced-chi2 values, so it read as a badly over-fitted
background rather than as a bug. Now reads bin 2 (issue 45).

**Fixed:** `postFit.pdf` used to plot the **unmasked** file unconditionally, so on a run accepted
only after masking it showed the fit that was *rejected* — live in the recorded J50 result, where
the unmasked rebinned p is 0.00248 and the masked one 0.01906 against a 0.01 threshold. Both
drivers now plot whichever fit was accepted, and `plotPostFit.py`'s `-l/--label` draws which it is
on the plot, so the file is self-describing rather than silently meaning different things in
different runs (issue 48). Deliberately still **one** file: `post_fit.pdf` already carries both fits
side by side, and a second filename would force a baseline re-cut for a change that moves no number.

**Open, and worth knowing before using either plot:**

- `plot_postfit.cpp` stamps every plot with a hardcoded `#sqrt{s} = 13 TeV, 25 fb^{-1}`. That is
  wrong for all three live callers: the wrong exposure for full Run 2 J100 and for prescaled J50,
  and the wrong *centre-of-mass energy* for `scripts/run_anaFit.sh`, which fits 2023 data at
  13.6 TeV. The correct values are nowhere in this repository — nothing records what dataset any
  input corresponds to — so they have to come from whoever owns the datasets (issue 44).
- The Run 2 drivers' failure banner attributes any non-zero exit to a twice-rejected p(chi2), which
  is now one cause among several — a missing input, a bad card or the rebin-pair refusal above all
  reach it too. The verdict it gives ("this result must not be used") stays correct; only the
  diagnosis is wrong (issue 47).

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
