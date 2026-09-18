# Refuse a partial `--rebinfile`/`--rebinhist` pair

**Written** 2026-09-17. **Branch** `claude-skills`. Resolves
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 46.

## The problem

`python/run_anaFit.py:88` selects the resolution binning with `if rebinfile and rebinhist:`, so
supplying one of the pair is indistinguishable from supplying neither: control drops into the
fallback, which generates its binning with `python/createBinning.py`. That generator defaults to
`--end 1000` and is called without `-e`, so the fallback binning stops at 1000 GeV while both Run 2
drivers fit to 3000 and 2997.

The rebinned histogram is not cosmetic. `getChi2` runs over it; its p-value is what
`--maskthreshold` gates on and what the BumpHunter masking loop consumes. A silent truncation moves
the rebinned chi2, the p-value, the accept/reject verdict and the BH window.

Exactly one of the two directions is silent, and it is the one that must be quoted: the drivers
pass `--rebinfile $rebinfile` unquoted and `--rebinhist "$rebinhist"` quoted, because the J100
histogram name contains spaces. An empty `rebinhist` therefore arrives as `''` — falsy, silent
fallback. An empty `rebinfile` makes the word vanish and argparse refuses. Verified both ways.

Whether it fails loudly is environment-dependent, which is its worst property. On this machine the
fallback dies on a null histogram, because `Input/data/dijetisrTLA/` does not exist and
`createBinning.py`'s hardcoded input is unreadable. Where that binning file exists, or was generated
once by an earlier run, the same typo silently produces a complete, plausible, wrong result.

## Scope

Two guards and, separately, the silence around the fallback itself. Not a rewrite of the binning
logic: the fallback is correct for the analysis it was written for — `scripts/run_anaFit.sh` fits
to `rangehigh=1000`, exactly where `createBinning.py` stops — so the branch is not the bug. The
branch *condition* and its silence are.

## Sections

### §1 — Refuse the partial pair, at the two choke points

Not at the selection site (`run_anaFit.py:88`), which is what the review comment suggested. That
point sits after `XMLReader` and `quickFit` have already run, and `build_fit_extract` is reached
twice (`:374`, and `:437` for the BumpHunter masked repeat) — so a typo would be caught only after
a fit had been done, and possibly after two. Guard instead where the values enter:

- **`run_anaFit()`**, at the top, before any fitting. Both `build_fit_extract` call sites route
  through it, so one check covers the whole driver path.
- **`PostfitExtractor.__init__`**, which both `run_anaFit.py`'s direct construction and
  `ExtractPostfitFromWS.py`'s own `--rebinfile`/`--rebinhist` CLI route through. One check there
  covers the standalone entry point and any future caller, rather than patching the CLI parser
  alone.

Both raise rather than warn: this is a "the run you asked for is not the run you would get" case,
and it must fail closed.

**Verification.** A partial pair in each direction is refused, at both entry points, before
anything runs; a complete pair and an empty pair are both still accepted; `tests/repro.py check`
(full, both analyses) still passes, since both drivers pass complete pairs and nothing about the
accepted path changes.

### §2 — Make the fallback audible

Independent of §1 and smaller. Once a partial pair is refused, the fallback is only ever reached
when *neither* value was given, which is the legitimate dijetisrTLA path — but it is still silent
about two things worth saying:

- It does not announce that it is falling back, or that the binning it is about to generate stops
  at 1000 GeV. The warning exists only as a source comment.
- `execute(f"python3 python/createBinning.py …")`'s return code is discarded, so a failed
  generation proceeds to hand `PostfitExtractor` a file that does not exist. Same class as the
  recorded "XMLReader and quickFit only warn and still return 0".

**Verification.** The fallback path prints its warning and stops on a failed generation; the
`check` run is unaffected, since neither driver takes the fallback.

## What this does not do

It does not make `createBinning.py` usable — its hardcoded, unreadable input path stays as recorded
in the table at the top of `KNOWN_ISSUES.md`. It does not add an `--end` pass-through, which would
change the generated binning for the analysis that currently uses it correctly. And it does not
touch the second-order question recorded under issue 45, which histogram directory each plotter
reads.
