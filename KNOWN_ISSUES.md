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
| ~~XMLReader and quickFit only *warn* on failure and still return 0; nothing gates on their exit codes, so a failed fit can look like a successful one~~ — **Fixed 2026-09-18.** `execute_checked()` now stops the run on a non-zero exit from XMLReader, quickFit or quickLimit. **The original wording was also wrong and is corrected here rather than edited away:** the binaries do *not* return 0 on hard failures — tested directly, a nonexistent card makes XMLReader exit **139** (SIGSEGV) and a nonexistent workspace does the same to quickFit. `quickFit` with no arguments at all exits 0, but that is a usage no-op, not a failed fit. Hard failures were being signalled and discarded, which is why this turned out to be fixable where the entry as written implied it was not. Soft failures — a fit that runs, does not converge and exits 0 — are not covered here; issue 40's `covQual`/`status` reporting is what catches those. | `python/run_anaFit.py` (XMLReader, quickFit, quickLimit) | Every fit. `tests/repro.py check` still diffs baseline outputs rather than trusting exit codes, which remains the stronger guarantee. |
| `gRand.SetSeed()` is a no-op — `TH1::FillRandom` samples from the global `gRandom`, so these are only accidentally reproducible | `python/InjectGaussian.py:67-68`, `python/InjectZprime.py:118-119` | Signal-injection studies, off the J50/J100 fit path. Left alone. |
| Hardcoded personal checkout path, so the HTCondor path runs someone else's framework at an unknown version | `submission/condor_script.sh:19,24` | HTCondor toy studies only, out of this plan's scope. Left alone. |
| Absolute AFS/EOS paths in other people's accounts, live in tracked config | `config/dijetisrTLA/*`, `python/inject_zprime_dscblimits.sh` | The (already inert) Run 3 ISR TLA flavour and Z' injection limits. Left alone. |
| Hardcoded input path returning *Permission denied*, and `--end` defaults to 1000 GeV | `python/createBinning.py` | The auto-rebinning fallback; both Run 2 drivers bypass it via `--rebinfile`/`--rebinhist`. Left alone. |
| `scripts/install_pyBumpHunter.sh` disagrees with the pyBumpHunter install `install.sh` actually runs — it hardcodes a Python from `LCG_105` and `pip install`s numpy/matplotlib/scipy/uproot straight into the venv, where `install.sh`'s own inline block uses the plain system `python3 -m venv` and installs only the pyBumpHunter egg. Nothing sources this script; the venv on disk (`pyBumpHunter/pyBH_env`) matches `install.sh`, not it. | `scripts/install_pyBumpHunter.sh` | Not on the `install.sh` path this repo actually uses. Found while closing the gaps in [plans/2026-09-15-reproducibility-lock.md](plans/2026-09-15-reproducibility-lock.md) §6; out of that section's stated scope. Left alone. |

The first nine were found during the survey behind
[plans/2026-09-15-reproducibility-lock.md](plans/2026-09-15-reproducibility-lock.md), verified,
and confirmed off the J50/J100 path — which is why they are disclosed here rather than fixed.

**A tenth entry, retracted rather than kept.** While building `env`, a probe that ran a bare
`lsetup "views …"` line and then tried to import numpy/scipy/uproot failed with
`ModuleNotFoundError`, and was disclosed here as "numpy/scipy/uproot are not importable via the
documented BumpHunter activation sequence." While building `record` it turned out the same
simplified probe also mis-reported `cmake`/ROOT — both resolved to `/usr/bin` instead of the LCG
view, because `lsetup`'s `PATH` edits do not survive outside the exact shell that ran them in this
non-interactive session. Re-running the numpy/scipy/uproot probe behind the framework's *actual*
setup (`scripts/setup_buildAndFit.sh`, which every real driver sources) instead of the simplified
one-liner succeeds cleanly. The activation sequence was never broken; the first probe was an
unfaithful reproduction of it. See the CHANGELOG entry for 2026-09-16 (the `record` section) for
the full retraction, kept there rather than rewritten away, per this repository's own rule for
mistakes recorded in the append-only notebook.

## Harness issues — found 2026-09-16 auditing the reproducibility-lock implementation

Issues 12–21 differ in kind from the eleven above. Those live in the analysis code the harness
guards, were surveyed *before* the harness was built, and are recorded because fixing them is not
worth it. These live in `tests/repro.py` and its own documentation, were found by auditing that
implementation against
[plans/2026-09-15-reproducibility-lock.md](plans/2026-09-15-reproducibility-lock.md) after it was
declared complete, and each is recorded **with the fix it needs**, because unlike the others they
are meant to be fixed.

**All ten (12–21) are now fixed, between 2026-09-16 18:40 and 2026-09-17 12:25; each entry's
header carries its fix date, and the `Fix` paragraph below it is the proposal that was carried
out, kept as written.** 12 and 13 were requirements of the plan that were never implemented, so
the plan's closing claim that "both implementation (§1–§6) and Verification (steps 1–7) are
complete" (CHANGELOG, 2026-09-16 17:20) was wrong at the time it was written. That entry is
append-only and stands as written; this section is the correction. (This paragraph itself said
"every other `Fix` is still a proposal awaiting review" until 2026-09-17 12:45, long after 14–21
were fixed — see issue 24 below.)

### 12. `env` computes the built binaries' SHA-256 but never compares them — **High** — **Fixed 2026-09-16 18:40**

**Fixed.** See CHANGELOG.md's 2026-09-16 18:40 entry. `compare_binary_digests()` now compares the
observed digests against the baseline's provenance and fails `env` (and therefore `check`) on a
mismatch, skipping when no baseline exists. The rest of this entry is kept as the record of what
was wrong and why, per this file's own rule of updating in place rather than deleting.

**What.** Plan §1 requires `env` to compare the SHA-256 of `xmlAnaWSBuilder/build/bin/XMLReader`
and `quickFit/build/quickFit` against the digests in the baseline provenance, because "the SHA
pins cover the *sources*, not the binaries actually built from them … a stale or locally rebuilt
binary passes every other check here". The digests are computed, printed, and written into both
baselines — but nothing ever compares them. `env`'s own detail line still reads *"not yet
compared: no baseline provenance exists until 'record' is built"*, which stopped being true the
moment the baselines were cut.

**Where.** [tests/repro.py:439-448](tests/repro.py#L439-L448) computes and prints, never compares;
[tests/repro.py:485-500](tests/repro.py#L485-L500) builds `live_versions` without them, so they
miss even the non-fatal version-drift warning; [tests/repro.py:708-715](tests/repro.py#L708-L715)
has `check` verify `input_sha256` only.

**Affects.** Both analyses, silently. Demonstrated by setting `quickFit`'s recorded digest in
`tests/baseline_J100.json` to a bogus value: `env` reported 20/20 PASS and `check --from` reported
PASS, both exit 0. A quickFit or XMLReader rebuilt from the same pinned source — different
compiler, different flags, a local source edit reverted after building — is invisible to the
entire harness, and those two binaries are what actually produce the numbers.

**Fix.**

1. Extract the comparison as a pure function — `compare_binary_digests(observed, recorded)`
   returning the same `(name, ok, detail)` triples the other checks use — so it is testable with
   no ROOT, no CVMFS and no baseline on disk.
2. Call it from `_report_env()`, which already loads the baseline provenance for the version
   comparison, and append its results to `checks` before the pass/fail summary is computed. `env`
   and `check` both inherit it with no further wiring, and `check` then refuses to run a fit on a
   changed binary, which is what plan §5 intends by running `env` first.
3. Make it **fail**, not warn. Plan §1 files it with the pins, not with the versions that cannot
   be pinned, and its whole rationale is a case nobody should be able to walk past. Skip silently
   when no baseline exists, exactly as the version comparison already does.
4. Word the failure so the legitimate cause is obvious: a rebuild is the likely reason, and the
   way out is a deliberate re-cut (`record --force --reason "rebuilt quickFit after …"`), not a
   flag that suppresses the check.
5. Replace the stale "not yet compared" detail string.
6. Extend `selfcheck` to cover the new function: match, mismatch, a digest missing from the
   baseline, and the no-baseline case.
7. Correct `doc/IMPROVEMENTS.md`'s description of `env` in the same change.

**A trade-off to settle while fixing, not after.** The same source rebuilt on a different machine
legitimately yields a different digest, so this check fails for anyone running the harness
elsewhere. That is the right trade — the baselines are already machine-specific, plan §4 adds
`--rtol` for the cross-machine case, and plan "Using this while the repository changes" expects
bit-identical results on this one — but it belongs in the README's Reproducibility section as a
stated limitation rather than being discovered by whoever runs it next.

### 13. The repointed `install.sh` clone URLs were never verified to resolve — **Medium** — **Fixed 2026-09-16 19:05**

**Fixed.** The repository owner ran the blobless-clone/`cat-file -e` check from this entry's Fix,
outside an agent session, on all three URLs. All three reported ok:
`xmlAnaWSBuilder`, `quickFit` and `workspaceCombiner` each resolve at
`https://github.com/tofitsch/<name>.git` and the pinned SHA is fetchable from each. See
CHANGELOG.md's 2026-09-16 19:05 entry. The rest of this entry is kept as the record of what was
skipped and why, per this file's own rule of updating in place rather than deleting.

**What.** Plan Verification step 2 requires cloning one dependency from its new GitHub URL and
checking out its pinned SHA, and says so in terms: *"Do not skip this — an `install.sh` naming a
reachable-looking but wrong remote is the exact failure this change exists to remove"*, with
*"if the branch-scope hook blocks it, run it by hand outside the agent"* already anticipated. It
was skipped. The reason given (CHANGELOG, 2026-09-16 17:00) is that the URLs are "already
confirmed reachable and correct by `env`'s pin checks, which read the clones' actual `git
remote`/`HEAD` state" — but `env` reads neither `git remote` nor anything about reachability. It
runs `git rev-parse HEAD` and `git status --porcelain` against clones that already exist locally,
which cannot test a URL.

**Where.** [install.sh:3](install.sh#L3), [install.sh:10](install.sh#L10),
[install.sh:17](install.sh#L17); plan Verification step 2.

**Affects.** A fresh install on a new account — the single thing `install.sh` exists for — remains
unproven. The corroborating evidence is good: all four clones on disk have `origin` set to exactly
the URLs `install.sh` now names, so that is where they came from. That is evidence, not the check.

**Fix.** One command, run **outside an agent session** — `git ls-remote` is refused here by the
branch-scope hook (confirmed), so this cannot be closed from inside Claude Code:

```bash
cd "$(mktemp -d)"
for r in xmlAnaWSBuilder quickFit workspaceCombiner; do
  git clone --filter=blob:none --no-checkout "https://github.com/tofitsch/$r.git" "$r"
done
git -C xmlAnaWSBuilder   cat-file -e 6b84050f3c0206a6f30eb40b103cc101e68505cc && echo "xmlAnaWSBuilder ok"
git -C quickFit          cat-file -e 0408030b6c8d74a2e2c27a864a02756132d08f5a && echo "quickFit ok"
git -C workspaceCombiner cat-file -e 7d484ad3f89c4075d2c567aa4503fc56e1bb9468 && echo "workspaceCombiner ok"
```

A blobless clone costs seconds and a few MB rather than the AFS quota the changelog cited for a
full `install.sh` re-run, and `cat-file -e` proves the pinned commit is actually fetchable from
that URL — which `git ls-remote` cannot, since the pins are ancestors rather than ref tips. Record
the result in the CHANGELOG. Do **not** automate this into `env`, which has to stay offline and
fast.

### 14. Baseline provenance records the *declared* pins, not the *observed* ones — **Low** — **Fixed 2026-09-16 19:30**

**Fixed.** `run_env_checks()` now puts each clone's observed `git rev-parse HEAD` (and each
`RooFitExtensions` checkout's) into `pins`, and `record` refuses to write when any `env` check
fails unless given `--force --reason "..."`. See CHANGELOG.md's 2026-09-16 19:30 entry. The rest
of this entry is kept as the record of what was wrong and why, per this file's own rule of
updating in place rather than deleting.

**What.** `provenance.pins` is built from `install.sh`'s text and from each clone's own
`install_roofitext.sh`, not from `git rev-parse HEAD`. `record` also does not gate on `env`
passing. On a tree where a clone has drifted, `env` fails but `record` still writes the *pinned*
SHAs into the baseline as though they had produced the numbers — the exact thing a provenance
block exists to prevent.

**Where.** [tests/repro.py:460-464](tests/repro.py#L460-L464),
[tests/repro.py:648](tests/repro.py#L648).

**Affects.** Only a baseline cut on a tree whose `env` is red, which is rare and always
deliberate — hence Low — but that is precisely the case where an accurate record matters most.

**Fix.** Two small changes. Have `run_env_checks()` put each clone's observed `HEAD` (and each
`RooFitExtensions` HEAD) into `pins` instead of the parsed declaration: on a green tree the value
is identical, because the checks already assert the two agree, so the committed baselines do not
change. Then have `record` refuse to write when any `env` check fails unless given `--force
--reason`, reusing the guard it already has for overwriting a baseline.

### 15. `env` compares versions against only the first baseline file — **Low** — **Fixed 2026-09-17 10:15**

**Fixed.** `_report_env()` now loops over every `tests/baseline_*.json`, comparing versions (and,
since issue 12's fix, binary digests) against each one's own provenance in turn, naming the file
in the warning. See CHANGELOG.md's 2026-09-17 10:15 entry. The rest of this entry is kept as the
record of what was wrong and why, per this file's own rule of updating in place rather than
deleting.

**What.** The version-drift comparison reads `sorted(glob("baseline_*.json"))[0]` — always
`baseline_J100.json` when it exists. `baseline_J50.json`'s `provenance.versions` is never read.
Harmless today, because `record` warns when the two disagree at capture time, but it is a silent
single-baseline assumption inside a harness built around two.

**Where.** [tests/repro.py:487-500](tests/repro.py#L487-L500).

**Fix.** Loop over every `tests/baseline_*.json` and report drift per file, naming each. Three
lines, and it retires the "(`tests/baseline_J100.json` if present, else `baseline_J50.json`)"
wording in `doc/IMPROVEMENTS.md` along with it.

### 16. The "note" tolerance class is unreachable — **Low** — **Fixed 2026-09-17 10:40**

**Fixed.** `NOTE_LEAVES`, the `"note"` branch in `classify()`/`compare()`, and the `notes` return
value (and its `selfcheck` assertions) are deleted. `compare()` now returns just the failures
list. See CHANGELOG.md's 2026-09-17 10:40 entry. The rest of this entry is kept as the record of
what was wrong and why, per this file's own rule of updating in place rather than deleting.

**What.** Plan §4 says keys recording the observed environment (ROOT version, active view) are
printed as notes and never fail. `check` deliberately excludes `provenance` from the comparison —
a later decision, documented in CHANGELOG 2026-09-16 16:10, and the right one, since the candidate
has no provenance to compare against — so no note-class key ever reaches `compare()`. `NOTE_LEAVES`
and the note branch are exercised only by `selfcheck`'s synthetic data.

**Where.** [tests/repro.py:55](tests/repro.py#L55),
[tests/repro.py:71-75](tests/repro.py#L71-L75),
[tests/repro.py:99-102](tests/repro.py#L99-L102),
[tests/repro.py:743-749](tests/repro.py#L743-L749).

**Affects.** Nothing at runtime. It is dead code that reads as live: a future reader may assume
`check` surfaces environment drift through it, when `env` is the only thing that does.

**Fix.** Delete `NOTE_LEAVES`, the `"note"` branch in `classify()` and `compare()`, the `notes`
return value and its `selfcheck` assertions — roughly fifteen lines out. The alternative, feeding
the observed environment into the candidate so notes fire for real, adds a second and weaker
version-drift report next to `env`'s, which already does the job properly.

### 17. `extract_postfit` hardcodes four TDirectory names — **Low** — **Fixed 2026-09-17 11:05**

**Fixed.** `extract_postfit` now iterates `f.GetListOfKeys()`, keeps keys whose class inherits
from `TDirectory`, and dedupes by name; the explicit raise and the `top_dir` entry in `ANALYSES`
are both gone. See CHANGELOG.md's 2026-09-17 11:05 entry. The rest of this entry is kept as the
record of what was wrong and why, per this file's own rule of updating in place rather than
deleting.

**What.** Plan §3 captures the chi2 block from "every TDirectory"; the implementation iterates a
fixed list of four names derived from `top_dir`. A missing directory raises (good), but an extra
or renamed one is invisible, and `directory_listing` covers files, not the structure inside
`PostFit_*.root`.

**Where.** [tests/repro.py:571-590](tests/repro.py#L571-L590), and `top_dir` in `ANALYSES` at
[tests/repro.py:518-535](tests/repro.py#L518-L535).

**Fix.** Iterate `f.GetListOfKeys()`, keep keys whose class inherits from `TDirectory`, and dedupe
by `GetName()` — ROOT key cycles can list one name more than once. Keep the existing
`name.endswith("_rebinned")` rule for which directories get postfit bins. `compare()` then catches
a missing directory as a missing key and an extra one as an unexpected key, so both the explicit
raise and the `top_dir` entry in `ANALYSES` can go: net less code. The baselines do not need
re-cutting — all three `PostFit_*.root` files on disk contain exactly the four
`TDirectoryFile`s already captured (verified 2026-09-16), so `check` should stay green across the
change, and would say so loudly if it did not.

### 18. `check` verifies input hashes inside the per-analysis loop — **Low** (cosmetic) — **Fixed 2026-09-17 11:30**

**Fixed.** `_check_input_hashes()` now runs for every selected analysis in `cmd_check`, ahead of
the driver loop, and stops before any driver runs if one fails. See CHANGELOG.md's 2026-09-17
11:30 entry. The rest of this entry is kept as the record of what was wrong and why, per this
file's own rule of updating in place rather than deleting.

**What.** Plan §5: "Runs `env` and the four input hashes first and stops if either fails". `env`
does run first, globally, but each analysis's two input hashes are checked inside the loop — so a
full `check` completes the entire J100 fit before noticing that a J50 input moved, and `--quick`
never checks J50's two at all.

**Where.** [tests/repro.py:708-715](tests/repro.py#L708-L715) inside `_check_one`, called from
[tests/repro.py:786-788](tests/repro.py#L786-L788).

**Affects.** Nothing about correctness — the change is still caught, and still stops that
analysis. It costs roughly two and a half wasted minutes in a rare case.

**Fix.** Hoist the hash verification for every selected analysis into `cmd_check` ahead of the
loop, keeping the per-analysis message. About five lines moved.

### 19. `--rtol` scales `atol` as well as `rtol` — **Low** (documentation) — **Fixed 2026-09-17 11:50**

**Fixed.** Kept the atol-scaling behaviour — it is the useful, defensible half, since a baseline
value near zero needs `atol` widened too for any scale to have an effect — and renamed the flag
to `--tol-scale` (and the internal `rtol_scale` parameter to `tol_scale` throughout) so the name
matches what it does, documenting both terms in `doc/IMPROVEMENTS.md`. See CHANGELOG.md's
2026-09-17 11:50 entry. The rest of this entry is kept as the record of what was wrong and why,
per this file's own rule of updating in place rather than deleting.

**What.** The flag is named for `rtol`, and plan §4 describes it as scaling "both float classes" —
meaning tight and pvalue, not both tolerance terms. The implementation multiplies `atol` by the
same factor. Defensible, since it keeps near-zero comparisons usable when the scale is widened,
but it is neither documented nor what the name says.

**Where.** [tests/repro.py:109](tests/repro.py#L109).

**Fix.** Decide, then say so. Either drop `* rtol_scale` from the `atol` line, or keep the
behaviour and rename the flag `--tol-scale`, documenting it in the README and
`doc/IMPROVEMENTS.md`. Nothing depends on the flag yet, so renaming costs nothing.

### 20. The README does not carry the plan's `global_Pval` warning — **Low** — **Fixed 2026-09-17 12:05**

**Fixed.** Added a paragraph to the README's Reproducibility section, adapted from the plan's own
Risks wording (already approved, so restating it is not a new physics claim): `global_Pval`
quantised at 1e-4 from 10 000 seeded pseudo-experiments is the first thing to move on an LCG
bump, and a `global_Pval`/`significance` failure alongside an `env` numpy warning means the stack
moved, not the fit. See CHANGELOG.md's 2026-09-17 12:05 entry. The rest of this entry is kept as
the record of what was missing and why, per this file's own rule of updating in place rather than
deleting.

**What.** Plan Risks: "`global_Pval` will be the first number to move on any LCG bump … Say so in
the README, so such a failure is read as 'numpy changed', not 'the fit changed'." The README's
Reproducibility section tells the reader to check whether `env` warned about version drift, but
never names `global_Pval` or numpy, so the connection the plan asked for is not made.

**Where.** [README.md:199-210](README.md#L199-L210).

**Affects.** Whoever first hits a BumpHunter p-value mismatch after an LCG view changes — the
failure the plan predicted would happen first.

**Fix.** One sentence in that section: `global_Pval` comes from 10 000 pseudo-experiments seeded
at 666 and quantised at 1e-4, it is the first quantity to move if the view's numpy changes, and a
`global_Pval`-only failure alongside an `env` numpy warning means the stack moved, not the fit.
Left for the repository owner to word, being a statement about the physics rather than the tool.

### 21. The parser unit tests recorded in the changelog were never committed — **Low** — **Fixed 2026-09-17 12:25**

**Fixed.** Re-added to `selfcheck`: `parse_install_sh_pins` against synthetic text covering a
blank line between `cd` and its checkout, the literal `cd $x` from `install.sh`'s build loop, and
`cd ..` immediately followed by a checkout line (the only arrangement that actually exercises the
`!= ".."` guard — confirmed discriminating by reverting the guard locally and observing the test
would have caught it); plus basic coverage for `parse_lsetup_view` and `parse_pyvenv_cfg`. See
CHANGELOG.md's 2026-09-17 12:25 entry. The rest of this entry is kept as the record of what was
claimed and what was actually there, per this file's own rule of updating in place rather than
deleting.

**What.** CHANGELOG 2026-09-16 13:50 reports that `parse_install_sh_pins`, `parse_lsetup_view` and
`parse_pyvenv_cfg` were "unit-tested against synthetic input covering a blank line between `cd`
and its checkout, the literal `cd $x` from `install.sh`'s build loop … and `cd ..`". Those tests
are not in the repository — `selfcheck` covers `compare()` and nothing else. The claim is true of
what was run and false of what can be re-run.

**Where.** [tests/repro.py:120-196](tests/repro.py#L120-L196) (`cmd_selfcheck`),
[tests/repro.py:220-253](tests/repro.py#L220-L253) (the untested parsers).

**Affects.** `install.sh`'s formatting is the input to the pin checks, which gate everything else.
Exposure is small, because a parse that loses a pin surfaces as `no cd/checkout pair found in
install.sh` and a parse that mispairs one surfaces as a SHA mismatch — both loud failures rather
than silent passes. What is missing is the net that says so.

**Fix.** Re-add them inside `selfcheck` as about fifteen lines of `assert` against inline
synthetic strings: the three cases the changelog names, plus `cd ..`. No framework, no fixtures,
no new file — `selfcheck` exists for exactly this and still needs no ROOT.

## Harness issues — found 2026-09-17 reviewing the completed reproducibility lock

Issues 22–27 come from a second review, asked for after issues 12–21 were closed: read the whole
reproducibility lock again — code, baselines and documentation — against
[plans/2026-09-15-reproducibility-lock.md](plans/2026-09-15-reproducibility-lock.md), and look for
problems nobody had disclosed yet. The plan itself is fully implemented; `selfcheck`, `env` (24/24)
and a full `check` (both analyses, real driver runs, ~3.5 min) all pass on the tree as it stands.
These six are what the review found on top of that.

**None of them invalidates a recorded number.**

**Everything this work introduced is fixed; the one pre-existing bug is recorded and left alone.**
That split was the repository owner's instruction on 2026-09-17: change what we introduced, record
what we inherited. So 22, 24, 25, 26 and 27 are fixed (24 on sight, the rest on 2026-09-17 13:20),
while **issue 23 stays open** — the write it describes has been in `FindBHWindow.py` since 2021 and
belongs to the fit path, not the harness. What was corrected there is only this work's own share of
it: the README and `doc/IMPROVEMENTS.md` claimed an isolation broader than the truth, and now say
what actually happens.

### 22. `compare()` treats NaN as a match — **Medium** — **Fixed 2026-09-17 13:20**

**Fixed.** `compare()` now tests for NaN before the tolerance comparison: exactly one side NaN is a
mismatch reported as `(NaN mismatch)`, both sides NaN is a match, everything else compares as
before. `selfcheck` covers all three combinations. See CHANGELOG.md's 2026-09-17 13:20 entry. The
rest of this entry is kept as the record of what was wrong, per this file's own rule of updating in
place rather than deleting.

**What.** The float comparison is `if diff > atol + rtol * abs(b)`, and every comparison against
NaN is `False`. A candidate value of NaN therefore passes against any baseline value, for every
leaf in the tight and pvalue classes: fitted parameters and their errors, `minNll`, `chi2`,
`chi2/ndof`, postfit bin contents, the data integral, and every p-value. Confirmed directly:
`compare({'minNll': 1259.11}, {'minNll': nan})` returns `[]`, while the same comparison against
`inf` correctly fails.

**Where.** [tests/repro.py:101](tests/repro.py#L101), the `diff > atol + rtol * abs(b)` test in
`compare()`.

**Affects.** Both analyses. The exposure is a fit that fails into NaN rather than failing loudly —
precisely the failure mode this harness is the compensating control for, since XMLReader and
quickFit only warn and still return 0 (see the first table above). In practice such a fit would
probably also move `status`/`covQual`, which are exact-compared and would fail, and a NaN in the
postfit histogram would likely disturb the data integral too — so it is unlikely that a NaN run
passes `check` outright. But that is luck, not design, and the one component that exists to catch
this is the one that silently agrees.

**Fix.** Guard the float branch: a mismatch if exactly one of baseline and candidate is NaN, a
match if both are, the existing tolerance test otherwise (`math.isnan`). Roughly three lines, plus
a `selfcheck` case for each of the three combinations. Worth doing even though `status` would
probably catch it anyway — the check is cheap and the alternative is relying on a coincidence.

### 23. `check` overwrites `bump.png` and `BH_statistics.png` in the repository root — **Low** — **open; documentation half corrected 2026-09-17 13:20**

**Status.** The write itself is left alone: it predates this work by four years, it is on the fit
path rather than in the harness, and the repository owner's instruction on 2026-09-17 was that
pre-existing bugs are recorded, not fixed, for now. What *was* corrected is this work's own share —
the README and `doc/IMPROVEMENTS.md` described an isolation broader than the truth, and now state
that any run reaching the BumpHunter step, `check` included, rewrites those two files at the
repository root. The fix below stands as the proposal for whenever the fit path is next opened.

**What.** `FindBHWindow.py` writes its two plots with bare relative filenames, so they land in the
process's working directory rather than in the run folder. `check` runs each driver from the
repository root, so a `check` that exercises J50 rewrites those two files at the top of the
repository — outside `run/check_scratch/`, which is the only place the README and
`doc/IMPROVEMENTS.md` say `check` writes.

**Where.** [python/FindBHWindow.py:88](python/FindBHWindow.py#L88) and
[python/FindBHWindow.py:91](python/FindBHWindow.py#L91) (`filename="bump.png"`,
`filename="BH_statistics.png"`); [tests/repro.py:787](tests/repro.py#L787), where `_run_driver`
does `cd "{REPO_ROOT}"`.

**Affects.** Anyone who keeps the real J50 BumpHunter plots at the repository root: a later `check`
replaces them with the scratch run's, with no warning. Nothing tracked changes — `*.png` is
gitignored, which is why `git status` stayed clean and this went unnoticed through the whole
implementation. The behaviour predates this work (the write has been there since 2021-11-02, and
every real J50 driver run does the same thing); what is new is the isolation claim written around
it in 2026-09-16's documentation.

**Fix.** Either pass a folder-qualified filename from `run_anaFit.py` into `plot_bump`/`plot_stat`
so the plots land beside the rest of the run's output — which is where they belong anyway, and
would make them visible to `directory_listing` — or, if a fit-path change is out of scope, state
the behaviour in the README's Reproducibility section and in `doc/IMPROVEMENTS.md` so the isolation
claim stops being broader than the truth.

### 24. This file said issues 14–21 were still proposals after they were fixed — **Low** — **Fixed 2026-09-17 12:45**

**Fixed.** The paragraph now states that all ten are fixed and that each `Fix` below it is the
proposal that was carried out. Corrected rather than left open, because a file whose stated purpose
is honest disclosure cannot carry a false statement about its own contents while new issues are
appended beneath it.

**What.** The preamble to the 12–21 section read "**Below, issues 12 and 13 are fixed … every other
`Fix` is still a proposal awaiting review, not a record of work done**". That was accurate when
written on 2026-09-16 and stopped being accurate on 2026-09-17 as 14 through 21 were fixed in turn
— each entry's own header was updated to say **Fixed**, but the paragraph introducing them was not.

**Where.** `KNOWN_ISSUES.md`, the paragraph opening the "Harness issues — found 2026-09-16"
section.

**Affects.** A reader trusting the section preamble over the individual entries would conclude
eight open harness bugs remained. Nothing in the code.

### 25. The pyBumpHunter egg check compares against a hardcoded constant — **Low** — **Fixed 2026-09-17 13:20**

**Fixed.** `EXPECTED_PYBUMPHUNTER_EGG_VERSION` is deleted. The check now derives the expected
suffix from the pyBumpHunter pin it already parses out of `install.sh` (`+g<first 7 hex>`) and
asserts the installed egg's version ends with it, so bumping the pin moves the expectation with it.
`find_pybumphunter_egg_version` reports two eggs as an ambiguity that fails the check rather than
silently picking the first. See CHANGELOG.md's 2026-09-17 13:20 entry. The rest of this entry is
kept as the record of what was wrong.

**What.** Plan §1's rule is that every expected value is parsed from the file that already declares
it, "without inventing a new source of truth". The egg check breaks that rule: it compares the
installed egg's version against `EXPECTED_PYBUMPHUNTER_EGG_VERSION`, a constant in the harness,
rather than against the short form of the pyBumpHunter SHA it already parses out of `install.sh`.
Related, in the same check: `find_pybumphunter_egg_version` takes `sorted(glob(...))[0]`, so if the
venv ever holds two eggs it reports whichever sorts first rather than noticing the ambiguity.

**Where.** [tests/repro.py:267](tests/repro.py#L267) (the constant),
[tests/repro.py:311-316](tests/repro.py#L311-L316) (`find_pybumphunter_egg_version`),
[tests/repro.py:484-486](tests/repro.py#L484-L486) (the check).

**Affects.** Nothing today — the constant agrees with the pin, and `env` passes 24/24. It bites
whenever the pyBumpHunter pin in `install.sh` is deliberately bumped: the clone SHA check passes,
the egg check fails, and its message blames the egg for disagreeing with a constant nobody thought
to update, rather than saying the venv needs rebuilding against the new pin. The check is right
about *what* is wrong and misleading about *why*.

**Fix.** Derive the expected short SHA from the already-parsed pin for `pyBumpHunter` and assert
the egg version ends with `+g<short sha>`, keeping pyBumpHunter's own `0.4.3.dev16` versioning out
of it (that is not something this repository pins). Fail with both the installed and the expected
value, as now. Optionally report a second egg as its own failure instead of silently picking one.

### 26. A leaf whose *type* changes crashes the comparator; a malformed baseline crashes `env` — **Low** — **Fixed 2026-09-17 13:20**

**Fixed.** `compare()` now requires *both* values to be numeric before doing arithmetic on them and
reports a type change as `(type changed: float -> str)`; `selfcheck` covers it. `_report_env()`
skips a baseline whose JSON is invalid or whose provenance block is missing or incomplete, naming
the file and what is missing, instead of raising. See CHANGELOG.md's 2026-09-17 13:20 entry. The
rest of this entry is kept as the record of what was wrong.

**What.** Two diagnosability gaps, both turning a reportable condition into a traceback. In
`compare()`, a baseline float against a candidate string reaches `abs(c - b)` and raises
`TypeError: unsupported operand type(s) for -: 'str' and 'float'` instead of being reported as a
mismatch — the type guard on the line above tests only the *baseline* value's type. In
`_report_env()`, a baseline file missing `provenance`, `provenance["versions"]` or
`provenance["binary_sha256"]` raises `KeyError` rather than saying which file is malformed.

**Where.** [tests/repro.py:94](tests/repro.py#L94) and [tests/repro.py:101](tests/repro.py#L101);
[tests/repro.py:553](tests/repro.py#L553) and [tests/repro.py:576](tests/repro.py#L576).

**Affects.** Neither can happen while the extractors and `record` are the only writers of these
documents — the types are fixed by the ROOT calls that produce them, and `record` always writes a
complete provenance block. Both become reachable the moment a baseline is hand-edited or produced
by a future variant of the tooling, which is exactly when a clear message matters most.

**Fix.** In `compare()`, test both values' types and report a type change as a mismatch in its own
right. In `_report_env()`, skip a baseline whose provenance is missing or incomplete with a named
warning rather than raising. Four or five lines each; `selfcheck` can cover the comparator half
with no ROOT.

### 27. `README.md` and `CLAUDE.md` still call the sub-frameworks "CERN GitLab" ones — **Low** — **Fixed 2026-09-17 13:20**

**Fixed.** Both opening paragraphs now say the three sub-frameworks are cloned at pinned SHAs from
their public GitHub mirrors. The CERN GitLab references that are still accurate — the upstream
project and its documentation, in the README's Links section — are untouched. See CHANGELOG.md's
2026-09-17 13:20 entry. The rest of this entry is kept as the record of what was wrong.

**What.** Both open by describing the framework as wrapping "three CERN GitLab C++
sub-frameworks", while the links beside that phrase point at GitHub and `install.sh` has cloned
from `github.com/tofitsch/...` since the plan's §6 repoint. The sentence was true when written on
2026-09-15; §6 made it stale on 2026-09-16 and neither file was revisited. The upstream project
genuinely is hosted on CERN GitLab (the README's Links section still points there), so the phrase
is half-true, which is the awkward kind.

**Where.** [README.md:3-4](README.md#L3-L4), [CLAUDE.md:7-8](CLAUDE.md#L7-L8).

**Affects.** Documentation only. The risk is a reader concluding the clone URLs still resolve at
CERN GitLab, which is the exact confusion §6 existed to remove — those URLs are unreachable, which
is why they were repointed.

**Fix.** Say the sub-frameworks are mirrored on GitHub and cloned from there at pinned SHAs, and
keep the CERN GitLab reference where it is accurate (the upstream project and its documentation).
`CLAUDE.md` carries unrelated uncommitted changes in the working tree — read it before editing, as
the plan's §7 already warns.

## Harness issues — found 2026-09-17 in a third review

Issues 28–31 come from a third review of the reproducibility lock, after 22–27 were closed. The
plan remains fully implemented: `selfcheck`, `env` (24/24) and `check --from` all pass on the tree
as it stands, every §1–§7 requirement and Verification step 1–7 is in place, and the committed
baselines still match the numbers the CHANGELOG records. These four are what was found on top of
that.

**All four are the same defect: a condition the harness should *report* instead makes it crash.**
Four places raise a bare exception where they should print a failure line or a recorded value.

**All four are recorded and none is being fixed**, which is a deliberate call rather than a
backlog. Under the triage rule in [CLAUDE.md](CLAUDE.md) (*Triaging issues*), the class that comes
first is anything that could let an analysis run to completion and produce a result that is now
unphysical because of a code change. **None of these four can do that.** Every one fails closed: it
crashes, so nothing completes, no number is produced, and nobody can be misled by one. They are
ugly, not dangerous. Two of the four are also unreachable for anyone who follows the documentation
— 31 needs a hand-edited baseline, which `README.md` tells you not to do, and 28 needs the four
input spectra to have been moved.

These were first reported with 28 ranked Medium, on how confusing the failure looks rather than on
what it can cost. On the rule above all four are Low.

**Issue 29 is the one to revisit first** if the extractors are ever opened: it is the only one the
coming refactor will trip by itself rather than through a mistake, and it lands at the exact moment
someone is asking whether their rewrite moved the physics.

### 28. A missing input spectrum crashes `check` instead of failing it — **Low** — **open; recorded, not fixed**

**What.** `sha256_of()` is `hashlib.sha256(path.read_bytes())` with no existence guard, so an input
path recorded in a baseline that no longer exists raises `FileNotFoundError` out of the list
comprehension that compares the hashes. Confirmed by running `_check_input_hashes` against a
baseline naming a moved file: `FileNotFoundError: [Errno 2] No such file or directory:
'.../Input/data/dijetTLA/moved_away.root'`. Plan §2 makes this function the gate that "verifies
them before running anything and stops on a mismatch"; a moved or deleted input is the most
serious form of that condition, since it means the baseline has stopped describing anything, and it
is the one input state that produces no diagnosis. `record` has the same hole when it builds a new
provenance block.

**Where.** [tests/repro.py:872-874](tests/repro.py#L872-L874) (`_check_input_hashes`),
[tests/repro.py:829](tests/repro.py#L829) (`cmd_record`), via
[tests/repro.py:355](tests/repro.py#L355) (`sha256_of`).

**Affects.** Both analyses, but only if the four tracked input spectra are moved or deleted —
which is a deliberate act, not an accident. The traceback names the missing path in full, so the
person who moved it has what they need to understand it. Left alone.

**Fix.** Check `is_file()` before hashing and report a missing input as its own failure line
alongside the mismatches, in the same shape §2 already specifies. Two or three lines.

**Related, not a bug.** `check` iterates the *baseline's* recorded inputs while `record` iterates
`ANALYSES[…]["inputs"]`. That asymmetry is deliberate and correct — it is what keeps `check`
path-independent — but it means a driver that gains a fifth input stays unguarded until the
baseline is re-cut. Worth knowing during the refactor.

### 29. A PostFit or FitResult file whose contents changed crashes the extractor — **Low** — **open; recorded, not fixed**

**What.** `d.Get("chi2")` on a TDirectory without that histogram returns a null pointer, which
PyROOT hands back as a bare `TObject`; the dict comprehension on the next line then raises
`AttributeError: 'TObject' object has no attribute 'GetNbinsX'` (confirmed on a synthetic file).
The same pattern sits in `d.Get("postfit")`/`d.Get("data")` for a `*_rebinned` directory, in
`f.Get("fitResult")` → `fr.floatParsFinal()`, and in `extract_bhresults`, where `bh["pyBHresult"]`
raises `KeyError` on a truncated or restructured `BHresults.json`. `f.Close()` is skipped on all of
these paths.

The precise shape of the gap is that **presence is guarded and content is not**: `extract_variant`
checks `is_file()` on both ROOT files and returns `None` for a missing one, which `check` turns
into a clean `FAIL: … has no FitResult/PostFit`. It is the file that exists and is not what we
expect that crashes. Likewise the comment above `extract_postfit` is right that a *renamed
directory* is caught by `compare()` as a missing key (issue 17's fix) — but the histogram names
inside (`chi2`, `postfit`, `data`) are still hardcoded, and that half has no such protection.

**Where.** [tests/repro.py:734-741](tests/repro.py#L734-L741) (`extract_postfit`),
[tests/repro.py:706-707](tests/repro.py#L706-L707) (`extract_fit_result`),
[tests/repro.py:746-751](tests/repro.py#L746-L751) (`extract_bhresults`).

**Affects.** Both analyses, and unlike the other three this one is reached by the refactor itself
rather than by a mistake: [python/ExtractPostfitFromWS.py](python/ExtractPostfitFromWS.py) is
squarely in the set of files the plan expects to be rewritten, and a rewrite that renames the chi2
histogram or creates a directory before filling it lands here. What should print
`missing: unmasked.chi2.J100yStar06_rebinned.pval` — the finding the harness exists to produce —
prints an `AttributeError` about a `TObject` instead. Left alone for now; see the note above about
revisiting this one first.

**Fix.** Null-check each `Get()` and record the absence as a missing key, so `compare()` reports it
as the missing quantity it is. Roughly one line per `Get()`, plus a `selfcheck` case that needs no
ROOT if the check is factored out.

### 30. `_view_binary_version` catches neither a timeout nor an OSError — **Low** — **open; recorded, not fixed**

**What.** Three unguarded exits on the happy path: `subprocess.TimeoutExpired` after 30 s (both
binaries live on `/cvmfs/sft.cern.ch`, so a cold cache or a stalled mount reaches this);
`OSError`, including the TOCTOU window between `exe.is_file()` and `subprocess.run()`, which on
CVMFS is exactly when a mount is most likely to vanish; and `IndexError`, because
`proc.stdout.strip().splitlines()[0]` indexes an empty list if a binary exits 0 while printing its
version to stderr.

Its sibling `_atlas_probe` wraps the identical call in `try/except (subprocess.TimeoutExpired,
OSError)` and documents why: *"Never raises — plan section 1 records these values rather than
asserting them, precisely because they cannot be pinned from this repository."* This function
serves that same §1 clause — the resolved ROOT and `cmake` versions are the canonical
record-never-assert values — and a crash is the hardest possible assert. The plan's amended §1 is
explicit that version drift must never fail the command, because "a check that fails for reasons
nobody can act on is a check that gets ignored"; a stalled CVMFS mount is precisely such a reason.

**Where.** [tests/repro.py:384-398](tests/repro.py#L384-L398), against
[tests/repro.py:359-377](tests/repro.py#L359-L377) for the guarded sibling.

**Affects.** `env`, `record` and `check` alike, since `run_env_checks()` calls both
`resolve_cmake_version` and `resolve_root_version` before anything else runs. Not reachable by any
amount of care — it is infrastructure — but rare, and when CVMFS is sick the drivers will not run
either, so a broken session is self-evident rather than confusing. Left alone.

**Fix.** The same `try/except (subprocess.TimeoutExpired, OSError)` as `_atlas_probe`, returning
`unavailable (timed out after 30s)`, plus a guard for empty stdout. Per §1's closing line, a
version recorded as unavailable is a true and useful thing for a baseline to say.

### 31. `record`'s cross-baseline versions read was left unhardened — **Low** — **open; recorded, not fixed**

**What.** `json.loads(other_path.read_text())["provenance"]["versions"]` raises `ValueError` on
invalid JSON and `KeyError` on a missing or partial provenance block. This implements plan §1's
"`record` warns when it is about to write a versions block that disagrees with the other
baseline's" — and `_report_env` reads *the same field of the same file for the same purpose* and
was hardened under issue 26, printing `WARNING: <file> has no usable provenance block (missing …) -
skipping its comparisons`. Issue 26's fix simply did not carry across to the second reader.

Also brittle, though within spec: `other` is a binary J100/J50 flip, so a third entry in `ANALYSES`
would silently compare against J100 only. Plan §1 says "Both baselines carry the same versions
block", written for exactly two analyses.

**Where.** [tests/repro.py:814-823](tests/repro.py#L814-L823), against
[tests/repro.py:598-615](tests/repro.py#L598-L615) for the hardened equivalent.

**Affects.** `record` only, and only against a baseline that has been hand-edited or half-written
— which `README.md` tells you not to do (re-cut with `record --force --reason "…"` instead). The
least reachable of the four. Left alone.

**Fix.** Reuse the guard `_report_env` already has. Three or four lines.

**A consistency note worth keeping.** The same reasoning applies backwards to **issue 26**, which
was fixed on a weaker trigger than any of these four — its own entry concedes it "cannot happen
while the extractors and `record` are the only writers of these documents". The bar was set low
there. That is a reason to leave the bar where it is wanted now, not a reason to chase parity with
a past decision.

## Harness issues — found 2026-09-17 in a fourth review

Issues 32–37 come from a fourth review, after 28–31 were recorded. The plan is still fully
implemented: `selfcheck`, `env` and `check --from` against both recorded run directories all pass
on the tree as it stands, and both committed baselines still describe the runs on disk.

These six were then sorted by a sharper question than the previous reviews asked — **can this make
`check` reach the wrong verdict?** A *false pass* means `check` prints PASS while a physics number
has moved; a *false fail* means it prints FAIL while nothing has moved. That question reorders them
against the severity labels they were first reported with, and the reordering is the useful part of
this review:

| | False pass | False fail |
|---|---|---|
| 32 `record --force` silences the env gate | **yes**, via a baseline cut from an unpinned tree | yes, later, against a correct tree |
| 33 `_check_one` whitelists three top-level keys | **yes**, if `record` ever gains a section | no |
| 34 `classify()` defaults to bit-exact | no | **yes**, reached by the refactor itself |
| 35 `provenance.pins` never compared | no | no — it misattributes a real failure |
| 36 `parse_install_sh_pins` and `cd ..` | no | yes, unreachable as `install.sh` reads today |
| 37 issue 18's `--quick` half left unfixed | no | no |

So 32 and 33 are the two that can put a number in front of someone while `check` says PASS, which
is the class [CLAUDE.md](CLAUDE.md)'s triage rule puts first. 35 was first reported as Medium and is
ranked Low here: it cannot change a verdict, only the diagnosis.

**All six are fixed, 2026-09-17 15:05.** All six lived in `tests/repro.py` or its documentation —
none touched the fit path — so none of them ran into the "pre-existing bugs are recorded, not
fixed" rule that keeps issue 23 open. The committed baselines were **not** re-cut: `check --from`
against both recorded run directories passes unchanged after the fixes, which is what says the
comparison semantics did not move.

### 32. `record --force` bypasses *and silences* the env gate — **Medium** — **Fixed 2026-09-17 15:05**

**Fixed.** The failing checks are now printed whenever any fail, and only the *refusal* is
conditional on `--force`; a forced re-cut prints them followed by `WARNING: recording anyway
because --force was given. The provenance block below describes the tree as it actually is, not as
install.sh declares it.` See CHANGELOG.md's 2026-09-17 15:05 entry. The rest of this entry is kept
as the record of what was wrong.

**What.** Issue 14 added the rule "`record` refuses to write when any `env` check fails, unless
given `--force --reason`". The refusal *and the report of what failed* were both inside
`if failed_checks and not args.force:` — so on a forced re-cut nothing was printed at all. That
matters more than it looks, because **re-cutting an existing baseline always needs `--force`**
(`baseline_path.exists() and not args.force` a few lines above), and re-cutting is the only route
the README documents. The gate therefore only ever fired on a *first* cut: on every re-cut it was
both inactive and invisible.

**Where.** [tests/repro.py:787-793](tests/repro.py#L787-L793), against
[tests/repro.py:778](tests/repro.py#L778) for the `--force` that every re-cut needs.

**Affects.** Both analyses, and it is the one issue in this review with a **false-pass** route
reachable through documented use. Cut or re-cut a baseline on a tree where a sub-framework clone
has hand-modified sources — which `env`'s "no modified tracked files" check exists to catch — and
the baseline encodes numbers produced by an unpinned stack while its provenance records the pinned
SHA. Every later `check` on that tree then passes, and the harness's green light stops meaning what
the README says it means. The symmetric false-fail follows later, when the same baseline is checked
against a correct tree and the failure reads as "the refactor moved the physics".

**Fix.** Print the failed checks unconditionally; keep the refusal conditional on `--force`. Four
lines moved, no behaviour change on a green tree.

**Related, recorded rather than fixed.** Two smaller things in the same function, both left alone
deliberately:

- `record`'s gate reads `run_env_checks()` directly, so it does **not** include the binary-digest
  comparison that `env` and `check` get from `_report_env()`. A baseline can be cut on a tree whose
  binaries match no existing baseline without a word. Wiring it in would mean a first cut is gated
  on the *other* analysis's digests, which is a defensible check but a new one, and not what issue
  12 asked for.
- `record` extracts numbers from a run directory that may predate the current binaries — by default
  the *old* `run/…` directory — while recording the digests and versions as they are *now*. A
  re-cut after a legitimate rebuild therefore pairs old numbers with a new digest, asserting that a
  binary produced numbers it never produced. Detecting that properly needs the run directory to
  carry its own provenance, which is a bigger change than the hole justifies; the honest mitigation
  is to re-run the fit before re-cutting, and that is now stated in the README.

### 33. `_check_one` compares a whitelist of three top-level keys — **Low** — **Fixed 2026-09-17 15:05**

**Fixed.** `expected` is now built by dropping `BASELINE_ONLY_KEYS`
(`provenance`, `analysis`, `source_dir`) from the baseline instead of naming the three keys to
keep, so a section added to `record` later is compared by default. Identical behaviour on today's
baselines — `check --from` still passes for both — and `check` now fails closed on a section the
candidate does not produce, rather than ignoring it. See CHANGELOG.md's 2026-09-17 15:05 entry.

**What.** `expected` was assembled as `{"directory_listing": …, "unmasked": …}` plus `"masked"`
when present. Plan §4 says "a missing or extra key is a failure in its own right", and `compare()`
enforces that at every level *below* the top — but the top level itself was a whitelist, so
anything the baseline held and the whitelist did not name was never compared.

**Where.** [tests/repro.py:913-916](tests/repro.py#L913-L916).

**Affects.** Nothing today: the whitelist happened to name every non-metadata key both baselines
carry. It becomes a **false pass** the moment `record` grows a section — a second fit variant, a
new quantity block — and whoever adds it does not also edit `_check_one`. The new section would be
recorded, committed, and silently never checked, with `check` printing PASS over it. The refactor
this harness exists to guard is exactly when someone would add one.

**Fix.** Invert it: drop the baseline-only metadata keys rather than naming the keys to compare.
One line, and it fails in the safe direction — an unexpected baseline section shows up as missing
from the candidate, which is loud.

### 34. `classify()` defaults to bit-exact with nothing saying so — **Low** — **Fixed 2026-09-17 15:05**

**Fixed.** The default is unchanged — it fails in the safe direction — but `compare()` now says
why: an unclassified *numeric* leaf reports `compared exactly: leaf 'newQuantity' has no tolerance
class. If this is a float quantity, add one to TOLERANCE_BY_LEAF` instead of the bare
`exact match required`. A `leaf_name()` helper was factored out of `classify()` for it, and
`selfcheck` covers both the new message and that a classified leaf of the same shape still passes
the same nudge. See CHANGELOG.md's 2026-09-17 15:05 entry.

**What.** `TOLERANCE_BY_LEAF.get(leaf, "exact")` — any leaf not in the table is compared bit-exactly.
That is the right default, but neither the plan, `doc/IMPROVEMENTS.md` nor the failure message said
it, and a float compared bit-exactly fails on the last ULP.

**Where.** [tests/repro.py:70-72](tests/repro.py#L70-L72) (`classify`),
[tests/repro.py:96-103](tests/repro.py#L96-L103) (the failure text).

**Affects.** A **false fail**, and the only one in this review the refactor reaches by itself
rather than through a mistake. Two steps to get there: a rewritten
[python/ExtractPostfitFromWS.py](python/ExtractPostfitFromWS.py) adds a labelled chi2 bin, the
baseline is re-cut so the new leaf is on the baseline side (before that it fails as `unexpected`
regardless of class), and from then on that one leaf fails on any rebuild or other machine while
its classified siblings pass within tolerance. One quantity moving alone is exactly the shape of a
real physics finding, which is what made this worth a message rather than a comment.

**Fix.** Keep the default, name it in the failure. Six lines.

### 35. `provenance.pins` is recorded and never read back — **Low** — **Fixed 2026-09-17 15:05**

**Fixed.** `compare_recorded_pins()` compares the live pins against each baseline's
`provenance.pins` and fails `env` (and therefore `check`) on any difference, naming the pin and the
way out. It reuses `compare()` rather than adding a second comparison engine — every leaf there is
a SHA, a view name or a version string, which `classify()` already handles exactly, and missing and
extra pins are reported too. `selfcheck` covers agreement, a drifted top-level SHA, a drifted
nested `RooFitExtensions` SHA, a pin absent from the baseline, and the no-baseline case. `env` goes
from 24 checks to 26 (one per baseline) and still passes on this tree; demonstrated failing against
a throwaway baseline with one bogus pin, which failed that check alone and exited 1. See
CHANGELOG.md's 2026-09-17 15:05 entry.

**What.** A baseline's provenance holds three blocks describing the stack. `versions` is compared
by `_report_env()` and warns (plan §1: it cannot be enforced); `binary_sha256` is compared and
fails (issue 12). `pins` — the four clone SHAs, the three `RooFitExtensions` SHAs, the LCG view,
the venv's Python version and the installed egg version — was written at
[tests/repro.py:827](tests/repro.py#L827) and read by nothing. Same "records but never compares"
defect as issue 12, which was ranked **High**.

**Where.** [tests/repro.py:827](tests/repro.py#L827) (written),
[tests/repro.py:617-647](tests/repro.py#L617-L647) (`_report_env`, which read the other two).

**Affects.** Neither a false pass nor a false fail — which is why it is Low here despite being
issue 12's twin, and a correction to the Medium it was first reported as. It is a *misattribution*:
`env` passing meant only "this tree agrees with `install.sh` as it currently reads", not "this is
the stack the baselines were cut with". The sharpest case is pyBumpHunter, which computes J50's
`global_Pval`: bump its pin, re-clone, rebuild the venv, and every check passes — the clone-SHA
check because the declaration moved with it, and the egg check because issue 25's fix derives its
expectation from that same declaration. No pyBumpHunter binary is hashed. `check` would still fail
on the moved `global_Pval`, correctly, but with `env` green the reader is pushed to the wrong end
of the diagnosis order plan §5 and the README both set out — and the README's own `global_Pval`
paragraph tells them to read such a failure as "numpy changed", when here it is "pyBumpHunter
changed".

**Fix.** Compare it, and fail rather than warn: pins are the enforceable half of the stack, plan §1
files them with the assertions, and a deliberate bump is already expected to need a re-cut, exactly
as a deliberate rebuild does under issue 12.

### 36. `parse_install_sh_pins` does not void a pending pairing on `cd ..` — **Low** — **Fixed 2026-09-17 15:05**

**Fixed.** A `cd` whose target starts with `..` now sets the pending directory to `None` instead of
being skipped, so stepping out of a directory voids the pairing. `selfcheck` covers `cd quickFit` /
`cd ..` / checkout and the `cd ../..` form, both of which must pin nothing. See CHANGELOG.md's
2026-09-17 15:05 entry.

**What.** The parser skipped `cd ..` (`if m and m.group(1) != ".."`) but left `current_dir` set, so
`cd quickFit` → `cd ..` → `git checkout <sha>` attributed that SHA to `quickFit` — a directory the
script had already left. Confirmed directly. `cd ../..`, which `install.sh`'s build loop does use,
was not even recognised as stepping out.

**Where.** [tests/repro.py:312-315](tests/repro.py#L312-L315).

**Affects.** Nothing today — `install.sh` has no checkout after a `cd ..` that is not already
paired, which is why `env` passes 24/24. If it ever did, the effect is a **false fail**: a
mispaired SHA is compared against the wrong clone's HEAD and fails loudly, and a clone left with no
pin fails as `no cd/checkout pair found in install.sh`. There is no route to a false pass — a
mispairing cannot accidentally name the correct SHA.

**Fix.** One line, plus the `selfcheck` case. Also retired a misleading comment in `selfcheck`
claiming a checkout right after `cd ..` "is the only way to exercise that guard at all": true of
the old `!= ".."` guard, but it read as though the case were covered when the missing reset was
not.

### 37. Issue 18's `--quick` half was left unfixed and recorded as Fixed — **Low** — **Fixed 2026-09-17 15:05**

**Fixed.** Documentation only: the README and `doc/IMPROVEMENTS.md` now say that `check` verifies
the input hashes of every *selected* analysis, and that `--quick` therefore checks J100's two and
not J50's — which is all its comparison depends on. No code change. See CHANGELOG.md's 2026-09-17
15:05 entry.

**What.** Issue 18's own Objective named two defects: hashes checked inside the per-analysis loop,
*and* "`--quick` never looked at J50's inputs at all". The fix addressed the first. The second is
still true — `cmd_check` hashes only the selected analyses — but the entry is headed **Fixed**, the
CHANGELOG entry is titled "check verifies every input hash before running any fit", and plan §5
says "the four input hashes". Nothing says the second half was left deliberately.

**Where.** `KNOWN_ISSUES.md` issue 18; CHANGELOG 2026-09-17 11:30; plan §5.

**Affects.** No verdict, in either direction: `--quick` compares only J100's baseline, and J100's
two inputs *are* checked. This is a stale claim about the harness, not a hole in it — the same
failure mode as issue 24, in a file whose whole purpose is honest disclosure.

**Fix.** Say "every selected analysis" rather than "the four", and say what `--quick` does not
cover. Checking all four under `--quick` was considered and rejected: it would hash two files whose
contents cannot affect the comparison being made, and the plan's own rationale for `--quick` is
that a check people skip protects nothing.

## Analysis-path issues — found 2026-09-17 in a fifth review

Issues 38–42 come from a fifth review with a narrower brief than the earlier ones: **what could let
a mistaken, non-physical analysis pass?** The first four reviews worked over `tests/repro.py`; this
one worked over the fit path itself — the drivers, `python/run_anaFit.py`,
`python/ExtractPostfitFromWS.py` and the cards.

**All five are pre-existing, and none is introduced by the reproducibility lock.** They were
first recorded and left alone under the repository owner's standing instruction that pre-existing
fit-path bugs are recorded rather than fixed — the rule that keeps issue 23 open. **On 2026-09-17
the owner lifted that rule for two of them: 38 and 42 are fixed (16:10); 39, 40 and 41 stay
open.**

The two that were fixed are the two with a route to a wrong result nobody is told about. The three
left open are a question for whoever owns the statistics (39), a physics judgement about whether
`covQual=2` is acceptable (40), and a latent case verified not to be triggered by anything recorded
(41). None of the three can be settled by editing code.

**What protects the two locked analyses, and what does not.** For J50 and J100, `tests/repro.py
check` compares the recorded outputs, so any of these biting would move a number and fail. Every
one of them is unguarded for *new* work — a different range, a different parameter count, the fits
the coming refactor will add — because a new configuration has no baseline. That is where the
exposure is.

### 38. `main()` discards `run_anaFit`'s return value, so a rejected fit exits 0 — **High** — **Fixed 2026-09-17 16:10**

**Fixed**, at the root and at both live callers. `main()` now does `return run_anaFit(…)`, so the
verdict reaches `sys.exit`. Both Run 2 drivers capture the status, print an explicit
`ERROR: … this result must not be used` banner, and report it as their own exit status. They still
produce the postfit plots on a failure — those are the diagnostics you want in order to see *why*
it failed; what is no longer possible is the run reporting success. The status is carried by a
`( exit … )` subshell rather than `exit`, because both drivers are `{ … }` brace groups that their
own headers tell you to **source** — a bare `exit` would kill an interactive shell — while
`tests/repro.py` runs them with `bash`. Verified both ways. See CHANGELOG.md's 2026-09-17 16:10
entry. The rest of this entry is kept as the record of what was wrong.

**What.** `run_anaFit()` computes the framework's only "this result is not acceptable" verdict: if
p(chi2) fails the mask threshold, BumpHunter finds the most significant window, the fit is repeated
with that window blinded, and if p(chi2) *still* fails it prints `Exiting with failed fit status.`
and returns `-1` (`python/run_anaFit.py` line 431). That verdict is then thrown away twice over:

1. `main()` calls `run_anaFit(datafile=…)` as a bare statement with no `return` (line 502), so
   `main()` returns `None` and `sys.exit(None)` exits **0**. Confirmed by running the same call
   shape in isolation.
2. The driver does not check the exit code in any case, and goes straight on to `plotPostFit.py`
   and `plot_postfit.cpp` — so a rejected fit renders `postFit.pdf`, `post_fit.pdf` and the EDM
   plot exactly as an accepted one does (`scripts/run_anaFit_run2.sh` lines 77–100, and the J50
   driver likewise).

**Where.** `python/run_anaFit.py` lines 502 and 529; `scripts/run_anaFit_run2.sh` line 77.

**Affects.** Every analysis, and it is a **false pass** in the strictest sense: the code does the
work of deciding the fit is unusable, says so on stdout, and then reports success. Nothing in the
output distinguishes a twice-rejected fit from an accepted one except a line in the log. Same
failure mode as the recorded "XMLReader and quickFit only warn and still return 0", but worse,
because here the verdict is the framework's *own* and is deliberately computed.

**Fix.** `return run_anaFit(…)` at line 502 — two words, and it changes nothing about any run that
passes. Then decide separately whether the drivers should stop on it; note that making the exit
code meaningful may start surfacing real failures in anything that does check it (the HTCondor path
being the obvious one), which is the point, but is a behaviour change worth making deliberately.

### 39. The p(chi2) gate reads a different histogram depending on whether a mask is active — **Medium** — **Fixed 2026-09-18 12:35**

**Settled by the repository owner and fixed.** Both branches now read
`<channel>_bkgonly_rebinned`, so the `if maskmin > -1 …` conditional collapses to a single line and
the two `#should be <channel> or <channel>_rebinned?` comments are replaced by the reason. This
entry was filed as a question for whoever owns the statistics rather than a bug with a correct
patch, and that is how it was closed — by a decision, not by an edit chosen here.

**The choice is corroborated by a comment that was already in the code.** The line above the branch
read *"If we used masking in a b-only fit then we need to calculate the p-val from the correctly
normalized postfit distribution"* — so the masked branch was deliberately on `_bkgonly` for a
normalisation reason, and the unmasked branch had simply never been given the same treatment.
Unifying on `_bkgonly_rebinned` makes the gate consistent with the reasoning already written down.
It is also what `plot_postfit.cpp` reads for its displayed chi2, so the gate and the plot now agree
about which distribution is being judged.

**Verified, and the verdict chain was genuinely exercised in both directions.** J100's initial gate
now reads 0.0148783 where it read 0.0148562, and still does not mask; J50's reads 0.0024813 where
it read 0.0024417, still masks, and its masked gate still accepts at 0.0190617. `tests/repro.py
check` passes on both analyses with both baselines untouched — J50's masked block still present,
J100's still absent, which is what confirms no verdict moved. See CHANGELOG.md's 2026-09-18 12:35
entry. The rest of this entry is kept as the record of what was wrong.

**What.** `build_fit_extract` returns the p-value the threshold decision is made on, and picks its
source by whether a mask range was passed:

```python
if maskmin > -1 or maskmax > -1:
    pval = pfe.GetPval(channel+"_bkgonly_rebinned")  # should be <channel> or <channel>_rebinned?
else:
    pval = pfe.GetPval(channel+"_rebinned")          # should be <channel> or <channel>_rebinned?
```

So the *initial* gate reads `<channel>_rebinned` and the *masked* accept/reject decision reads
`<channel>_bkgonly_rebinned`. The two are different numbers, and the comment — in the code as
written — shows the choice was never settled.

**Where.** `python/ExtractPostfitFromWS.py` is where both come from; the selection is
`python/run_anaFit.py` lines 127–131.

**Affects.** Both gates, in principle. From the recorded baselines the two differ by roughly 1–2%
relative:

| Fit | `_rebinned` | `_bkgonly_rebinned` | read by the gate |
|---|---|---|---|
| J100 unmasked | 0.0148562 | 0.0148783 | `_rebinned` |
| J50 unmasked | 0.0024417 | 0.0024813 | `_rebinned` |
| J50 masked | 0.0188064 | 0.0190617 | `_bkgonly_rebinned` |

No recorded verdict changes — all three are unambiguous against the 0.01 threshold — so nothing
published is affected. A fit landing between the two values would be accepted or rejected according
to which histogram the gate happened to read, with no record of the choice. Left alone as a
question for whoever owns the statistics, not a bug to be patched by picking one.

**Fix.** Decide which histogram the goodness-of-fit gate is defined on, use it in both branches,
and delete the comment. If the switch is deliberate — the masked fit's normalisation differs, which
the comment above it hints at — say so there in a sentence instead.

### 40. Nothing checks fit status or covariance quality; every recorded fit has a forced covariance — **Medium** — **Fixed 2026-09-17 20:30** (reported and gateable; whether `covQual=2` is acceptable remains the owner's judgement)

**Fixed**, in the sense the entry asked for: the property is no longer invisible.
`report_fit_quality()` in `python/run_anaFit.py` reads `status()` and `covQual()` from the
`fitResult` immediately after `quickFit` and before anything is extracted, and prints one line
naming the value and its meaning:

```
FIT QUALITY: status=1 covQual=2 (full, but forced positive-definite) [.../FitResult_anaFit_sixPar_bkgOnly.root]
```

A new `--mincovqual` (default **2**) refuses anything worse, with a message saying that the fitted
*errors* come from this matrix and feed the spurious-signal, injection-linearity and limit studies.
The default is 2 deliberately: it accepts exactly what is already on record and refuses a
degradation, so it cannot break the two locked analyses while still catching the case this entry
was filed about. A file with no `fitResult` warns rather than crashing.

**What this does not do, and deliberately.** It does not decide whether `covQual=2` is good enough
for these fits. That is a physics judgement for the repository owner, as the original entry said;
what has changed is that the framework can now state the property and be told what to do about it.
Every recorded fit is still `status=1, covQual=2`.

Verified on the recorded fit results (all three report `status=1 covQual=2`, matching the
baselines), on the refusal path (`--mincovqual 3` refuses readably), on the missing-`fitResult`
path, and on the **live driver path** — `scripts/run_anaFit_run2.sh` run end to end emits the line.
`tests/repro.py check` passes on both analyses. See CHANGELOG.md's 2026-09-17 20:30 entry. The rest
of this entry is kept as the record of what was wrong.

**What.** `grep` for `covQual` or `status()` across `python/` and `scripts/` returns **nothing**: no
part of the framework reads either. Every fit this repository has recorded was minimised with a
covariance matrix MINUIT had to force positive-definite. From
`run/run_481_3000_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`:

```
Warning in <Minuit2>: MnPosDef Matrix forced pos-def by adding to diagonal 0.00492847
                covariance matrix quality: Full matrix, but forced positive-definite
                Status : MINIMIZE=1 HESSE=1
```

at every one of the retries, while the run's closing summary prints `Fit Summary of POIs (STATUS
OK)`. All three recorded fits carry `status=1, covQual=2` in their baselines.

**Where.** `python/` and `scripts/` generally — the absence is the issue. The values are visible in
`FitResult_*.root`'s `fitResult` and in `quickFitLog_*.log`.

**Affects.** The **parameter errors** rather than the central values. `covQual=2` means the matrix
was full but forced positive-definite, so the fitted uncertainties come from a matrix with ~0.005
added to its diagonal; the minimum itself is reported `Valid` and the retries land on the same FCN,
which is what the 2026-09-15 14:38 CHANGELOG entry reasoned about. That entry is right about the
minimum and silent about the errors, and the errors are what the downstream studies — spurious
signal, injection linearity, limits — consume. For J50/J100 the harness pins `status` and `covQual`
exactly, so a *degradation* fails `check`; for any new configuration nothing checks, and `STATUS
OK` is the last word the log prints.

**Fix.** Read `fitResult.status()`/`covQual()` after the fit and print a clear line — ideally refuse
to proceed below a configured `covQual`. Cheap, and it turns a property nobody sees into one
decision. Whether `covQual=2` is acceptable for these fits is a physics judgement for the
repository owner; this entry only records that the framework cannot currently tell you.

### 41. `getChi2` silently excludes bins with no data error or a non-positive fit — **Low** (latent) — **open; recorded, not fixed**

**What.** The chi2 loop accumulates a bin only under `if valueErrorData > 0. and postFitValue > 0.`,
and a skipped bin is counted in neither `chi2` nor `chi2bins`. An unweighted bin with zero observed
events has zero error, so **empty bins are dropped from the goodness-of-fit and from the degrees of
freedom**, with nothing reported. The exclusion is not numerically necessary: with
`useSumW2=False` the residual is `(data - fit)/sqrt(fit)`, whose denominator is the *fit*, so a bin
with zero data is perfectly computable. A dropped bin removes `fit` from the chi2 and 1 from ndof,
so for a bin where the fit predicts more than about one event — an observation of zero against a
prediction of several, i.e. a real deficit — the discarded term is the discrepant one.

**Where.** `python/ExtractPostfitFromWS.py`, the bin loop in `getChi2` (lines 59–76).

**Affects.** Nothing recorded. **Verified inactive in all three recorded fits**: every bin of every
`PostFit_*.root` directory has a positive data error and a positive fit value, and the recorded
`nbins` equals the histogram's own bin count in each case (J100 2519 fine / 57 rebinned, J50 2695 /
65) — the only reduction anywhere is the masked J50 run dropping exactly its BumpHunter window
(2695→2615 fine, 65→62 rebinned), which is by design. It becomes reachable as soon as a fit range
extends into the sparse high-mass tail where bins empty out, which is what a reach extension does.
Left alone as latent.

**Fix.** Guard on `postFitValue > 0` alone and let zero-data bins contribute, or keep the exclusion
and report the count of skipped bins alongside `nbins` so it is visible in the chi2 block. The
second is nearly free and does not change any recorded number.

### 42. `nPars` is a substring match on the background file's path, silently defaulting to 5 — **Low** — **Fixed 2026-09-17 16:10**

**Fixed.** `run_anaFit.py` now gathers the card's `[PAR<n>,` matches first, then compares the
highest index against `nPars` before either the prefit or the range assignment runs: a disagreement
prints both numbers and exits, and a card with no `PAR` placeholders at all warns that `nPars` came
from the file name alone. Checked against all twelve tracked `background_*.template` files — every
one is accepted — and against a `sixPar` card deliberately renamed `…_6Par` (refused: card up to
PAR6, nPars=5) and `…_tenPar` (refused: card up to PAR6, nPars=10). See CHANGELOG.md's 2026-09-17
16:10 entry.

**One claim in this entry was wrong, and is corrected here rather than edited away.** It said that
with `nPars` too small "a `PARn` placeholder is never substituted, so XMLReader fails — but warns
and returns 0". That is not what happened: `parRangeLow`/`parRangeHigh` are sized `nPars`, so a
card declaring a higher index raised `IndexError: list assignment index out of range` on the range
assignment, well before any substitution — confirmed directly. That direction failed closed all
along. The silent direction was only the other one, `nPars` *larger* than the card declares, where
PreFit fits a higher-order function and hands wrong starting values to a card of a different order.
The fix covers both and makes the first one readable instead of a traceback.

**What.** The number of background parameters is decided by testing the path for the words
`three`…`ten`, and if none matches, `nPars` stays at its initialised value of **5**, with no
message. `nPars` then sizes the prefit's parameter ranges, selects the PreFit function order and
bounds the `PAR1..PARn` substitution loop. Two lines further on, the same function already parses
the card's actual `[PAR<n>,` placeholders with a regex — so the information needed to check the
guess is in hand and unused.

**Where.** `python/run_anaFit.py` lines 216–236 (the derivation) against lines 244–250 (the card's
real PAR indices).

**Affects.** No card on the J50/J100 path: checked all twelve tracked `background_*.template` files,
and every word-named one agrees with the highest `PAR<n>` its card declares (`fivePar`→5,
`sixPar`→6, `sevenPar`→7, up to `tenPar`→10). Two real cases do disagree:
`config/dijetTLAnlo/background_dijetTLAnlo_J100yStar06_CT14nnlo.template` gets `nPars=5` by default
(benign — it declares no `PAR` placeholders at all), and a digit-named variant such as
`…_6Par.template` would silently get 5.

The collision hazard this first looked like is **smaller than it appears**, and that is worth
recording so nobody re-raises it: the `elif` chain tests `four`, `five`, `six` before `seven`,
`nine`, `ten`, so a spurious keyword elsewhere in the path cannot override the real one — checked
with paths containing `stephen` and `tenPar_studies` wrapped around a `sixPar` card, both of which
still give 6.

What remains is the silent default. Too small, and a `PARn` placeholder is never substituted, so
XMLReader fails — but warns and returns 0, and per issue 38 the process still exits 0. Too large,
and PreFit fits a higher-order function and hands wrong starting values to a card of a different
order, which produces a complete and plausible result from the wrong starting point.

**Fix.** Compare against the card: take the `max` of the `PAR<n>` indices already parsed at line
244 and stop if it disagrees with `nPars`. Three lines, and it converts a naming slip from a silent
wrong answer into a refusal.

## Driver setup guard — found 2026-09-17 in external review

Issue 43 comes from a GitHub Copilot review comment on the `README.md` passage added by the
repository-relative output directory work. The finding is correct on the mechanics and its
severity was overstated; both are recorded below. It is the first issue here raised from outside
the review series, and it is the first to find a *documentation* claim that is false rather than
merely stale.

### 43. Drivers continue after `setup_buildAndFit.sh`'s wrong-directory guard fires — **Low** — **Fixed 2026-09-17 17:20**

**Fixed** in all six drivers that source `scripts/setup_buildAndFit.sh`, together with the two
documentation claims that were the reason for fixing a fail-closed issue at all. Verified 12/12
(each driver sourced and under `bash`: error printed, status 1, no `run/` created, interactive
shell alive) and `tests/repro.py check --quick` PASS against `tests/baseline_J100.json`, which
exercises the working path. The four `setup_buildCombineFit.sh` call sites are deliberately not
guarded — see the plan. See CHANGELOG.md's 2026-09-17 17:20 entry. The rest of this entry is kept
as the record of what was wrong.

**What.** `scripts/setup_buildAndFit.sh` lines 5–8 refuse to run outside the repository root:

```bash
if [[ ! -d xmlAnaWSBuilder ]] || [[ ! -d quickFit ]]; then
    echo "Execute from FrequentistFramework directory!"
    return 1
fi
```

`return` in a sourced script returns from *that script*, not from the script that sourced it. Every
driver sources it as a bare statement and never tests the status, so control comes straight back
and the run proceeds: `mkdir -p $out_dir` creates `run/` in whatever directory the user was
actually in, and the fit chain is entered with no CVMFS environment. Reproduced directly, and the
same both ways the drivers are invoked — sourced, as their own headers instruct, and under `bash`,
as `tests/repro.py` runs them.

The same hole swallows a *missing* setup script: `. scripts/setup_buildCombineFit.sh` prints
`No such file or directory`, returns 1, and the four drivers that source it carry on regardless.

**Where.** `scripts/run_anaFit.sh:6`, `run_anaFit_run2.sh:14`, `run_anaFit_run2_J50.sh:13`,
`run_anaFit_syst.sh:6`, `run_anaFitLoop.sh:5`, `run_anaFit_flowchart.sh:6`. The
`setup_buildCombineFit.sh` variant is the already-recorded "does not exist, but is sourced by
eight live call sites" entry in the table at the top of this file.

**Affects.** **Nothing that can reach a number, which is why this is Low and not High.** The guard
fires only when `xmlAnaWSBuilder/` and `quickFit/` are absent — in which case
`xmlAnaWSBuilder/build/bin/XMLReader` and `quickFit/build/quickFit` cannot exist either, and the
LCG view was never set up. The run dies at `import ROOT`, or, if ROOT leaks in from elsewhere, at
`d.FindBin()` on a null `TFile` a few lines into `build_fit_extract`. It fails closed. Per
[CLAUDE.md](CLAUDE.md)'s *Triaging issues* rule that is the lower tier: it costs an afternoon, it
cannot put a wrong number in front of anyone.

**The reason it is being fixed rather than recorded and left is the documentation.**
`CHANGELOG.md`'s 2026-09-15 15:40 entry states:

> In each driver the `mkdir -p $out_dir` was moved to after the `setup_buildAndFit.sh` guard runs,
> so a wrong-directory invocation aborts before creating anything.

That is false: the `mkdir` runs. And it was the stated justification for `out_dir=${OUT_DIR:-$PWD/run}`
— so a live design decision rests on a guarantee that does not hold. `README.md` lines 58–61 are
true about the setup script in isolation but sit directly under "All commands must be run from the
repository root", and read as enforcement of the drivers. This is the failure mode issues 24 and 37
were filed for, in the files whose whole job is honest disclosure.

**Fix.** Test the status. The idiom has to survive both invocation styles, since the headers say
to source these scripts while `tests/repro.py` runs them with `bash`:

```bash
if ! . scripts/setup_buildAndFit.sh; then
    echo "ERROR: run this from the FrequentistFramework repository root." >&2
    return 1 2>/dev/null || exit 1
fi
```

`return` succeeds when sourced; when executed it fails silently and `exit 1` takes over. Same
reasoning as issue 38's `( exit … )` subshell — a bare `exit` would kill an interactive shell.
Plan: [plans/2026-09-17-driver-setup-guard.md](plans/2026-09-17-driver-setup-guard.md).

## Plot labelling — found 2026-09-17 in external review

Issue 44 comes from the same GitHub Copilot review as issue 43, on the channel parameterization
added to `plot_postfit.cpp` by the Run 2 work. Recorded and **not fixed**, on the repository
owner's decision, because it changes no fitted quantity. The investigation behind the entry found
the problem to be one step wider than the review comment described.

### 44. `plot_postfit.cpp` stamps every plot with a hardcoded, wrong `#sqrt{s}` and luminosity — **Medium** — **open; recorded, not fixed**

**What.** `plot_postfit.cpp` line 29 defines

```cpp
lumi_label = "#sqrt{s} = 13 TeV, 25 fb^{-1}";
```

as a file-scope constant, drawn unconditionally at line 238. It has been there since the macro was
first added (`5cce670`, "added postfit macro"), has never been a parameter, and there is no way for
a caller to override it. It is wrong for **every** live caller, not only the Run 2 ones the review
comment named:

| Caller | Data | Label claims | Actually |
|---|---|---|---|
| `scripts/run_anaFit_run2.sh:118` | full Run 2 J100 | 13 TeV, 25 fb⁻¹ | √s correct, exposure wrong |
| `scripts/run_anaFit_run2_J50.sh:121` | full Run 2 J50, **prescaled** | 13 TeV, 25 fb⁻¹ | √s correct, exposure wrong — and for a prescaled stream the meaningful quantity is an effective exposure, not a single delivered luminosity |
| `scripts/run_anaFit.sh:165` | `data/data23_histos.root` | **13 TeV**, 25 fb⁻¹ | 2023 is Run 3: **13.6 TeV**. The centre-of-mass energy is wrong too. |

The wrong √s on the Run 3 ISR TLA plot was not part of the review comment and predates the channel
parameterization entirely. What that change did was extend an already-wrong label to two new
analyses.

**Where.** `plot_postfit.cpp:29` (the constant) and `:238` (the draw). Callers as tabled above,
plus `scripts/test.sh:81`. `python/plotPostFit.py`, the other postfit plotter, draws no such label
at all.

**Affects — no fitted quantity, which is why this is recorded rather than fixed.** Verified three
ways: the cards are `Lumi="1"` with `MultiplyLumi="0"`, so the fit is a shape fit on raw counts
that never reads a luminosity; `tests/baseline_J100.json` and `baseline_J50.json` contain no
luminosity field anywhere (their fitted content is `chi2`, `fitResult`, `postfit_bins`); and the
label is drawn text, applied after everything is computed. p(chi2), the fitted parameters and the
postfit bins are unaffected.

**What it does affect is the artefact people look at.** Both locked analyses' plots on disk carry
the wrong string today — `run/run_481_3000_sixPar/post_fit.pdf` and
`run/run_J50_302_2997_sixPar/post_fit.pdf`, three occurrences each, confirmed by extracting the
text — and every future run reproduces it. The exposure is one of the few numbers a reader takes
straight off a bump-hunt plot. `atlas_label = "Work in progress"` limits the blast radius but does
not make the number right. This is the tension worth stating plainly: by
[CLAUDE.md](CLAUDE.md)'s ranking question this is a wrong number that reaches a plot, while by the
same document's fit-path framing it cannot make a *result* unphysical. It is filed as Medium on
that split, and left open deliberately, not overlooked.

**Fixing it will not disturb the reproducibility lock.** The baselines record `post_fit.pdf` only
as a filename in `directory_listing` and never hash its contents, so changing the label cannot
move `tests/repro.py check` and neither baseline would need re-cutting.

**Fix, for whoever picks it up.** Make the label a parameter of `plot_postfit()` and have an
unsupplied value draw **no exposure claim** — `#sqrt{s} = …` alone, or nothing — rather than
falling back to a value. A missing label is a gap someone notices; a wrong one is a gap nobody
notices. Each driver then passes the √s and exposure its own dataset warrants.

**The numbers are not in this repository.** That one string is the only luminosity anywhere in the
tree, and nothing records what dataset any input corresponds to, so the correct values for J100,
for prescaled J50, and for `data23_histos.root` have to come from whoever owns those datasets.
They were deliberately not guessed at when this entry was written.

**Already-distributed plots are not covered by any fix.** Changing the macro corrects future runs;
it does not correct a PDF already in a slide deck or a note. Whether either of the two on disk has
left this machine is not something the repository can answer.

### 45. `plotPostFit.py` prints the p-value under a `#chi^{2}/ndof` label — **Medium** — **Fixed 2026-09-17 18:25**

**Fixed.** `python/plotPostFit.py:43` now reads `GetBinContent(2)`, with a comment naming the bin
layout so the next reader does not have to rediscover it. Re-running the plotter over both locked
analyses' existing `PostFit_*.root` prints `#chi^{2}/ndof = 1.000` for J100 and `1.039` for J50,
against baseline values of 1.00002 and 1.03893 and the C++ macro's `χ2/Ndof: 1.00` — where before
the fix the same files gave 0.496 and 0.078, the p-values. The recorded 2026-09-15 run outputs were
not overwritten (verification plots were written to a scratch directory; both `postFit.pdf` mtimes
still read 2026-09-15). See CHANGELOG.md's 2026-09-17 18:25 entry. The rest of this entry is kept
as the record of what was wrong.

**The p-value line suggested below was not added** — the fix is the bin index alone. The C++ macro
already shows both numbers, and adding a second line here was not asked for.

**What.** `python/plotPostFit.py` lines 41–45 build the label `"#chi^{2}/ndof = "` and then fill it
from **bin 6** of the chi2 histogram. Bin 6 is the p-value. `python/ExtractPostfitFromWS.py` lines
84–110 write the histogram and label its own axis, so there is no ambiguity about what each bin
holds:

| bin | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| content | `chi2` | `chi2/ndof` | `nbins` | `npars` | `ndof` | `pval` |

The variable is even called `rchi2`. The intent was reduced chi2; the index is the p-value's.

**Where.** `python/plotPostFit.py:43` — `rchi2 = h_rchi2.GetBinContent(6)`, which should be `(2)`.
Present since the script was first added; the Run 2 work changed the hardcoded `"Run3TLA/chi2"` to
`args.channel+"/chi2"` on the line above and did not touch the bin index.

**`plot_postfit.cpp` next to it is a correct reference implementation**, which is what makes this
unambiguous rather than a judgement call: lines 140–160 read `GetBinContent(2)` into
`native_chi2_ndof` and `GetBinContent(6)` into `native_pval`, and label each as what it is.

**Affects — no fitted quantity, and every plot the Python plotter draws.** The value is read out of
a finished ROOT file purely for display; nothing downstream consumes it. But both locked analyses'
`postFit.pdf` on disk carry the wrong number today, and the two plotters that run in the *same
driver invocation* disagree about the same fit:

| | `post_fit.pdf` (C++) | `postFit.pdf` (Python) | truth (from `tests/baseline_J100.json`) |
|---|---|---|---|
| J100 | `χ2/Ndof: 1.00`, `p-val: 0.4960` | `χ2/ndof = 0.496` | chi2/ndof 1.00002, pval 0.49599 |
| J50 | — | `χ2/ndof = 0.078` | chi2/ndof 1.03893, pval 0.07806 |

**This is the sharp end of it.** A goodness-of-fit number is exactly what a reader uses to judge
whether the background model describes the data, and the wrong value is *plausible*: 0.496 reads as
a badly over-fitted background, when the true reduced chi2 is 1.00 — a good fit. J50 reads as 0.078,
which would look like a catastrophe, against a true 1.039. It does not look like a bug, it looks
like a result. The review comment that raised it quoted 0.015 against 1.48; those are the
*rebinned* numbers, and the Python plotter reads the unrebinned channel directory, so the values
actually displayed are the ones tabled above. The diagnosis is unaffected.

**Fix.** One character: `GetBinContent(6)` to `GetBinContent(2)` at line 43. It cannot move any
recorded number — the baselines compare the chi2 dictionary read from the ROOT file, not the PDF,
and never hash plot contents, so neither baseline would need re-cutting. Worth considering at the
same time: draw the p-value on its own line as well, since p(chi2) is the quantity the framework
actually gates on (`--maskthreshold`), and the C++ macro already shows both.

**Noted while confirming this.** The Python plotter reads `<channel>/chi2` where the C++ macro
reads `<channel>_bkgonly/chi2`. For these background-only fits the two agree to five digits
(1.00002 against 1.00002), so it is not a second bug, but the two plotters are not reading the same
directory and nothing says which is intended. Related to but distinct from issue 39, which is about
which histogram the *threshold decision* reads.

**Left open on the same basis as issue 44**: the repository owner's rule that a defect which does
not move a fit result is recorded rather than fixed. Unlike issue 44, nothing here is unknown — the
correct value is in the file being read, and a correct sibling implementation sits beside it.

## Binning selection — found 2026-09-17 in external review

Issue 46 comes from a fourth GitHub Copilot review comment. Unlike issues 44 and 45, which are
display defects, **this one can change a fitted number without saying so** — it is the class
[CLAUDE.md](CLAUDE.md)'s triage rule puts first.

### 46. A partial `--rebinfile`/`--rebinhist` pair silently falls back to truncated binning — **High** — **Fixed 2026-09-17 19:15** (the silent fallback; see the note on the fallback's own silence)

**Fixed.** A half-given pair is now refused at both entry points, before anything runs:
`run_anaFit()` (so the driver path is refused before `XMLReader` and `quickFit`, not after) and
`PostfitExtractor.__init__` (which covers both `run_anaFit.py`'s direct construction and
`ExtractPostfitFromWS.py`'s standalone CLI). Verified in both directions and on the live silent
route — reproducing the real failure by running `scripts/run_anaFit_run2.sh` with its `rebinhist`
shell variable emptied now refuses with a message naming both values and the 1000 GeV truncation,
and produces **no output files at all**, where before it would have fitted with truncated binning.
A complete pair and an empty pair are both still accepted. `tests/repro.py check` (full, both
analyses) passes. See CHANGELOG.md's 2026-09-17 19:15 entry. The rest of this entry is kept as the
record of what was wrong.

**Still outstanding, deliberately.** The fallback branch remains silent about being a fallback and
about the 1000 GeV limit, and `createBinning.py`'s return code is still discarded. That is §2 of
[plans/2026-09-17-rebin-pair-guard.md](plans/2026-09-17-rebin-pair-guard.md), not yet implemented.
With a partial pair now refused, the fallback is reached only when *neither* value is given — the
legitimate dijetisrTLA path, whose `rangehigh=1000` is exactly where `createBinning.py` stops — so
what is left is a readability problem, not a route to a wrong number.

**What.** `python/run_anaFit.py:88` selects the resolution binning with

```python
if rebinfile and rebinhist:
```

so supplying *one* of the pair is not an error — it is indistinguishable from supplying neither,
and control drops into the fallback branch, which builds
`Input/data/dijetisrTLA/mjjResolutionBinning_<rangelow>.root` and, if that file is absent,
generates it with `python/createBinning.py`. That generator defaults to `--end 1000` and
`run_anaFit.py` does not pass `-e`, so the fallback binning **stops at 1000 GeV**. The code says so
itself, in a comment three lines below the branch. Both Run 2 drivers fit to 3000 and 2997 GeV.

The rebinned histogram is not cosmetic: `getChi2` runs over it, and the resulting p-value is what
`--maskthreshold` gates on and what the BumpHunter masking loop consumes. A silently truncated
binning therefore changes the rebinned chi2, the p-value, the accept/reject verdict and the BH
window.

**Where.** `python/run_anaFit.py:88` (the selection) and `:96-100` (the fallback and its own
warning comment). The same pattern is at `python/ExtractPostfitFromWS.py:287` and `:308`, which
have their own `--rebinfile`/`--rebinhist` CLI arguments (`:424-425`) and the same partial-pair
hole when that script is run standalone; there a partial pair silently produces *no* rebinned
channel at all.

**Reachable, and exactly one of the two directions is silent.** Both Run 2 drivers pass the pair as
shell variables, and the two are quoted differently — necessarily so, because the J100 histogram
name contains spaces:

```
--rebinfile $rebinfile \
--rebinhist "$rebinhist" \
```

Confirmed by running argparse both ways:

| what goes wrong | what argparse sees | result |
|---|---|---|
| `rebinhist` empty or misspelled variable — **quoted**, so an empty word survives | `--rebinhist ''` | `''` is falsy → **silent fallback**, no message |
| `rebinfile` empty or misspelled variable — **unquoted**, so the word vanishes | `--rebinfile --rebinhist` | argparse refuses, `exit 2` — fails closed |

So the direction that is quoted, and quoted for a good reason, is the direction that fails open.

**Affects — not the two locked analyses as they stand, and that is not much comfort.** Both drivers
pass both values correctly today and `tests/repro.py check` passes, so J50 and J100 are unaffected
right now. The exposure is a typo, an edited driver, or any new configuration — and a baseline
cannot catch what has no baseline.

**Worse: whether it fails loudly is environment-dependent.** On this machine
`Input/data/dijetisrTLA/` does not exist, `createBinning.py`'s hardcoded input path
(`/afs/cern.ch/work/t/tofitsch/...`) is not readable — already recorded in the table at the top of
this file — and its failure is not checked, so `PostfitExtractor` is handed a nonexistent rebin
file and dies on a null histogram. It fails *closed* here. On a machine where that binning file
exists, or where it was generated once by an earlier run, the same mistake silently rebins to
1000 GeV and produces a complete, plausible, wrong result. The machine where you would notice is
not the machine where it bites.

**Fix.** Reject the partial pair. The review comment suggests raising at the selection site, which
is correct as far as it goes, but that point sits *after* `XMLReader` and `quickFit` have already
run, and `build_fit_extract` is called twice (`:374` and `:437`, the second being the BumpHunter
masked repeat). Better to validate once at the choke point both call sites route through — the top
of `run_anaFit()` — so a typo is refused before any fit is done rather than partway through the
second one. `ExtractPostfitFromWS.py`'s standalone CLI deserves the same two lines.

Worth doing at the same time, and cheap: have the fallback branch *say* it is falling back, and
check `createBinning.py`'s return code instead of discarding it. The silence is as much the defect
as the branch condition.

## Found while fixing, not while reviewing — 2026-09-17

Issue 47 was not raised by a review. It surfaced while verifying issue 46's guard: the refusal
worked, and the driver then reported it as something it was not. Recorded here under its own
heading rather than under the binning section above, because it has nothing to do with binning —
it is a consequence of there now being more than one way for `run_anaFit.py` to exit non-zero.

**Independently confirmed.** A fifth GitHub Copilot review comment, on
`scripts/run_anaFit_run2.sh:117-119`, reported the same defect from the opposite direction — from
reading the banner rather than from tripping it — and listed further routes to a non-zero exit:
invalid cards, a missing channel, missing inputs and extraction errors. Its suggested wording is
the first of the two fixes proposed below, arrived at separately. Two independent findings agreeing
on both the defect and the remedy is the strongest evidence this entry has.

### 47. The Run 2 drivers' failure banner asserts a cause it cannot know — **Low** — **open; recorded, not fixed**

**What.** Both Run 2 drivers print, on any non-zero exit from `run_anaFit.py`:

```
ERROR: run_anaFit.py exited N - the fit did not pass p(chi2) even with
       the BumpHunter window masked, so this result must not be used.
```

That names one specific cause. It is the cause issue 38's fix was written for, but it is not the
only way the script exits non-zero: any traceback does too — a missing input file, the `IndexError`
described under issue 42, and now the `ValueError` added for issue 46. Observed directly while
verifying that fix: a run refused for a half-given rebin pair, before any fitting happened at all,
was reported as having failed p(chi2) with the BumpHunter window masked.

**Where.** `scripts/run_anaFit_run2.sh` and `scripts/run_anaFit_run2_J50.sh`, in the
`if [[ -n $anafit_failed ]]` block.

**Affects.** No number, and not the safety verdict — "this result must not be used" is correct
whatever the cause. Only the diagnosis is wrong, and it points the reader at the p(chi2) gate when
the real failure may be somewhere else entirely. Pre-existing: every traceback route existed before
issue 46's guard was added, which only made the mismatch easy to observe.

**Fix.** State the status and point at the log rather than asserting why — the log is three lines
up and says exactly what happened. Alternatively, distinguish the framework's own `-1` verdict from
any other non-zero status, since only `-1` means "the fit was rejected"; that is a slightly larger
change, and the p(chi2) rejection path would need re-testing to confirm it still reports correctly.

## Plot selection — found 2026-09-17 in external review

### 48. `postFit.pdf` plots the rejected fit when the accepted one is the masked fit — **Medium** — **Fixed 2026-09-18 12:20**

**Fixed.** Both Run 2 drivers now plot whichever fit was accepted — the masked one where a masked
fit happened, the unmasked one otherwise — and `plotPostFit.py` takes a new `-l/--label` that is
drawn on the plot saying which it is. The label is not decoration: it is what stops this being a
silent substitution, which was the objection to the review comment's original patch. Verified on a
real J50 run: `postFit.pdf` reads `masked fit - BumpHunter window blinded` with
`#chi^{2}/ndof = 1.040`, against the baseline's masked 1.04006, where before it showed the rejected
fit's 1.039.

**One plot, not two, and the reason is worth keeping.** The first implementation emitted a second
file, `postFit_masked.pdf`. That made `tests/repro.py check` fail J50 on `directory_listing`, which
is compared exactly — a baseline re-cut would have been needed for a change that moves no number.
The repository owner's call was that the record should only change when the physics does, which is
right: re-cutting is the one operation that can quietly bless a real regression, and "it is only a
filename" is exactly the claim a re-cut makes unfalsifiable afterwards. **Nothing was lost by
dropping the second file** — `post_fit.pdf` from `plot_postfit.cpp` already draws the unmasked and
masked fits side by side with the masked region and the BumpHunter p-value, so the rejected fit
remains available as the diagnostic it is meant to be. Confirmed on the recorded J50 output before
the second file was removed.

`tests/repro.py check` passes on both analyses with both baselines untouched, and a J50 run's file
listing is now identical to the recorded one. See CHANGELOG.md's 2026-09-18 12:20 entry. The rest of
this entry is kept as the record of what was wrong.

**Worth knowing, and recorded here because it is the general lesson:** `check` compares plot
**filenames only** — `grep` for `pdf` in `tests/repro.py` returns nothing, and the baselines hold
plot names in `directory_listing` and nothing else about them. Issues 44, 45 and 48 would all have
passed a green `check`, and all three were found by reading code. The lock protects numbers, not
plots.

**What.** Both Run 2 drivers plot a fixed filename:

```bash
python python/plotPostFit.py -i ${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root \
                             -o ${folder}/postFit.pdf -c "$channel"
```

When a fit fails the p(chi2) gate, `run_anaFit.py` re-runs it with the BumpHunter window blinded and
writes `PostFit_..._bkgOnly_masked.root`. If *that* passes, the masked fit is the accepted result —
but the plot command still reads the unmasked file. `postFit.pdf` then shows the fit that was
**rejected**, with nothing on it saying so.

**This is not hypothetical — it is what the recorded J50 result does.** Both drivers set
`maskthreshold=0.01`, and from `tests/baseline_J50.json`:

| | rebinned p-value | verdict at 0.01 |
|---|---|---|
| unmasked — **what `postFit.pdf` plots** | 0.00248 | **rejected** |
| masked — the accepted result | 0.01906 | accepted |

`run/run_J50_302_2997_sixPar/` contains the full masked set (`PostFit_*_masked.root`,
`FitResult_*_masked.root`, the masked workspace and log), and `postFit.pdf` is drawn from the
unmasked file regardless. J100 passes the gate first time (rebinned p 0.01488 > 0.01), writes no
masked files, and is therefore unaffected — so the two analyses' `postFit.pdf` mean different
things, and nothing in the filename or the plot distinguishes them.

**Where.** `scripts/run_anaFit_run2_J50.sh:111-112` and the identical lines at
`scripts/run_anaFit_run2.sh:114-115`. The review comment named only the J50 driver; the J100 one
carries the same code and would behave the same way the first time its fit fails the gate.

**`plot_postfit.cpp` next to it already does this correctly** — the same pattern as issue 45. It
loads both the native and masked files, guards on `plot_masked`, and labels the masked panel
"masked fit" with its own chi2 and BumpHunter window. So each run produces one complete plot
(`post_fit.pdf`) and one that silently shows the rejected fit (`postFit.pdf`).

**Affects.** No fitted number: both fits are in the ROOT files and both are recorded in the
baseline, which is why `tests/repro.py check` passes and has nothing to say about this. What is
affected is which of two real fits a reader is looking at. The quantities differ modestly here —
the accepted masked fit has an unrebinned chi2/ndof of 1.04006 against the rejected 1.03893, so the
number printed on the plot barely moves — but the drawn background curve, the residuals and the
data are the rejected fit's, and the framework's own verdict applies to the other one.

**Fix — but not by silent substitution.** The review comment's patch plots the masked file when it
exists. That is the right selection, but on its own it makes `postFit.pdf` mean one thing for J100
and another for J50 with nothing saying which, which is the defect in a new place. The comment's
own parenthetical is the better half: **emit both, with explicit labels**, or at minimum draw the
mask state onto the plot so the file is self-describing. `plot_postfit.cpp` is the working model.
Whichever is chosen, it belongs in both drivers, not just J50's.
