## Tier 1 — Safety net (do this before touching any structure)

1. **Characterization ("golden-master") tests** — the highest-leverage thing by far. Run the current pipeline once on a fixed input, freeze the outputs (fit parameters, p(χ²), p(BH), CLs limit points) to disk as the reference, then assert every future run reproduces them within tolerance. Tools: **`pytest`** + **`numpy.testing.assert_allclose`** (with an explicit `rtol`, because fits aren't bit-reproducible), or the **`approvaltests`** library, which is purpose-built for exactly this "pin the output of legacy code" workflow. This is what lets a nervous postdoc rip a 2000-line script apart and *know* the Z′ limits didn't move.
2. **Pin the environment** — `conda env export` or a `requirements.txt`/`environment.yml`. RooFit/ROOT behaviour is version-sensitive; a refactor that coincides with an unpinned ROOT upgrade is undebuggable. This pairs with the Bartels §9.1.1 footnote point — the numerically-robust RooFit log-L only exists in newer versions, so you *want* the version recorded.
3. **Git**, if it isn't already, with the reference outputs committed. Nothing else matters if you can't get back to a known-good state.

## Tier 2 — Zero-friction automated cleanup (instant wins, no learning curve)

These require no decisions and no expertise — run once, code is measurably better:

1. **`ruff`** — extremely fast linter that catches the pathologies spaghetti is full of: unused imports, variables assigned but never read, shadowed names, undefined names. For untangling "is this 40-line block even used?" it's invaluable, and it's a single command.
2. **`black`** — auto-formatter with no config and no style arguments to bikeshed. Makes the diff of every *subsequent* refactor readable, which matters enormously when reviewers are physicists.
3. Optionally wrap both in **`pre-commit`** so they run automatically — but for a non-SWE audience I'd introduce that *later*; a `make lint` or a one-line script is less intimidating at first.

## Tier 3 — Assisted structural refactoring

1. **An IDE with real refactoring support** — **VS Code + Pylance**, or **PyCharm**. The "extract function," "rename symbol across the whole project," and "inline variable" operations done *mechanically and safely* are exactly what a scientist needs to turn a monolith into functions without hand-editing (and hand-breaking) 30 call sites. This is the most underrated ease-of-use tool on the list.
2. If they live in **notebooks**: **`jupytext`** (pairs each notebook with a plain `.py` so it's diffable and testable) and **`nbstripout`** (keeps output cruft out of git).

## Tier 4 — Only now, the orchestration layer

Once the code is functions-with-tests rather than a script, introduce the DAG from our earlier discussion. For **this audience specifically**, my ranking shifts toward minimal ceremony:

- **Hamilton** *(my top pick for non-engineers)* — you write plain Python functions; the function name is the output, its parameter names are its inputs, and Hamilton assembles the dependency DAG automatically. No new DSL, no decorators required, provenance for free. It maps directly onto the "layer-2 dependency DAG" I described (`background_fit → bumphunter`, `sb_fit → cls_limit`), and the retry/masking loop just lives *inside* a function as ordinary code. The conceptual jump from "I have functions" to "I have a pipeline" is the smallest of any tool here.
- **Snakemake** — the HEP/bioinformatics staple; file-based, wildcard rules give you "one fit per (mass, width)" and native Slurm/HTCondor submission. Best if the sweep is the pain point and outputs are naturally files. The rule DSL is a modest hurdle.
- **Avoid** dagster / Prefect / Airflow to start — powerful, but the operational overhead (servers, schedulers, concepts) is wrong for a small group of physicists.

## Suggested starting move

Concretely, I'd start Tier 1 + Tier 2 in the first sitting: add `ruff` + `black`, pin the env, and write **one** characterization test that runs the current unblinded-analysis script end-to-end and freezes the limit/​p-value outputs. That alone converts the refactor from "scary" to "routine," and it's maybe an afternoon of work.

I can scaffold that for you now — a `pyproject.toml` with ruff/black configured, a `pytest` characterization-test template with the `assert_allclose` tolerance pattern stubbed for the p(χ²)/p(BH)/CLs outputs, and a `Hamilton` module sketch with the six nodes from the mapping doc wired up as plain functions. Want the safety-net scaffold, the Hamilton skeleton, or both?
