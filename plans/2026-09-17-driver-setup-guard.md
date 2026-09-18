# Make the drivers stop when the setup guard fires

**Written** 2026-09-17. **Branch** `claude-skills`. Resolves
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 43.

## The problem

`scripts/setup_buildAndFit.sh` refuses to run outside the repository root with `return 1`. Every
driver sources it as a bare statement and never tests the status. `return` in a sourced script
returns from that script alone, so control comes back to the driver and the run continues — it
creates `run/` in the wrong directory and enters the fit chain with no environment.

It fails closed (issue 43 records why: the binaries the guard protects cannot exist when it
fires), so on this repository's triage rule it would ordinarily be recorded and left. It is being
fixed because the documentation asserts the opposite, and one of those assertions is the
justification for a live design decision: `CHANGELOG.md` 2026-09-15 15:40 says a wrong-directory
invocation "aborts before creating anything", which is why `out_dir` is `$PWD`-relative.

## Scope

Six drivers that source `scripts/setup_buildAndFit.sh`, plus the two documentation claims.

**Out of scope: the four `setup_buildCombineFit.sh` call sites.** They source a file that does not
exist anywhere in the repository, and are recorded in `KNOWN_ISSUES.md` as broken before any of
this work and deliberately left alone. Guarding them would make them fail loudly instead of
silently, which is an improvement, but it changes the behaviour of a driver nobody can currently
run and cannot be verified — there is no working NLO fit to test against. Left for whoever fixes
that driver. Noted here so the omission is deliberate and visible rather than an oversight.

`submission/` and `config/` copies are not touched: they are other people's HTCondor checkouts
and commented-out history.

## Sections

### §1 — Guard the six drivers, correct the two documentation claims

Replace the bare source with a tested one in `scripts/run_anaFit.sh`, `run_anaFit_run2.sh`,
`run_anaFit_run2_J50.sh`, `run_anaFit_syst.sh`, `run_anaFitLoop.sh` and
`run_anaFit_flowchart.sh`:

```bash
if ! . scripts/setup_buildAndFit.sh; then
    echo "ERROR: run this from the FrequentistFramework repository root." >&2
    return 1 2>/dev/null || exit 1
fi
```

`return` succeeds when the driver is sourced, as the headers instruct; when it is run with `bash`,
as `tests/repro.py` does, `return` fails silently and `exit 1` takes over. A bare `exit` is not an
option — it would kill an interactive shell — the same constraint issue 38 met with `( exit … )`.

Then the documentation:

- `CHANGELOG.md` 2026-09-15 15:40 — the "aborts before creating anything" sentence is false as
  written. Per this repository's rule, correct it *in place with a note saying what was wrong*,
  the way issue 42's entry was corrected, rather than editing the claim away.
- `README.md` lines 58–61 — say that the drivers stop, now that they do.
- A new `CHANGELOG.md` entry for this work.

**Verification.** For each of the six: `bash -n`; then run it from a scratch directory containing
only a copy of `scripts/`, both sourced and under `bash`, and confirm it prints the error, sets
status 1, creates no `run/`, and leaves an interactive shell alive. Then confirm a real fit still
runs from the repository root — `scripts/run_anaFit_run2.sh` end to end, against
`tests/baseline_J100.json`, which is what `tests/repro.py check --quick` exists to compare.

This is one section because the guard is one line six times and the documentation is the reason
for doing it; splitting them would leave a commit whose message is contradicted by the CHANGELOG
sitting next to it.

## What this does not do

It does not make a *right*-directory run any safer. The guard only ever tested for two directories
existing; a run from the repository root with a half-built `xmlAnaWSBuilder` still reaches
`XMLReader` and, per the recorded issue on exit codes, a failure there still warns and returns 0.
That is issue 38's territory, already fixed at the source, and not reopened here.
