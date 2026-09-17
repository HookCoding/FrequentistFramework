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
| XMLReader and quickFit only *warn* on failure and still return 0; nothing gates on their exit codes, so a failed fit can look like a successful one | `python/run_anaFit.py:44,71` | Every fit. This is exactly why `tests/repro.py check` diffs baseline outputs rather than trusting exit codes. Left alone at the source; worked around in the harness. |
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

**Below, issues 12 and 13 are fixed (2026-09-16 18:40 and 19:05); every other `Fix` is still a
proposal awaiting review, not a record of work done.** 12 and 13 were requirements of the plan
that were never implemented, so the plan's closing claim that "both implementation (§1–§6) and
Verification (steps 1–7) are complete" (CHANGELOG, 2026-09-16 17:20) was wrong at the time it was
written. That entry is append-only and stands as written; this section is the correction.

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
