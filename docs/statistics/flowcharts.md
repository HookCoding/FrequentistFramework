# Unblinding flowcharts

The unblinding procedure (analysis note, Section 10.1, Figures 10.1–10.5) is organised as four flowcharts. The first three are executed **at every unblinding stage** (4%, 20%, 100%); the last one replaces the "inspection" flowchart at the 100% stage. Throughout, *fail* means $p(\chi^2) \le 0.01$ **or** a numerically unstable fit, and every BumpHunter window exclusion is capped at **three $m_{jj}$ resolution bins**.

!!! note "Guidelines, not law"
    The flowcharts are guidelines agreed with the conveners. If the data produces a situation they don't cover, the procedure is adapted in consultation with the conveners rather than followed blindly.

## 1. Validating a fit strategy (Figure 10.1)

Starting point: $N_\text{par} = 4$ and the full fit range (from the 95% trigger-efficiency point; ~85 GeV at the first stage, later 125 GeV).

```mermaid
flowchart TD
    START([Unblinded dataset<br/>Npar = 4, full range]) --> BFIT{"B-only fit (Npar+2)<br/>p > 0.01 and stable?"}

    BFIT -- fail 1st time --> BH[BumpHunter window exclusion<br/>max 3 resolution bins]
    BH --> ATSTART{Window at start<br/>of spectrum?}
    ATSTART -- yes --> INC[Npar += 1]
    ATSTART -- no --> BFIT
    BFIT -- fail 2nd time --> INC
    INC --> NPMAX{Npar &le; 8?}
    NPMAX -- yes --> BFIT
    NPMAX -- no --> RANGE[Fit range start +1 GeV,<br/>re-derive resolution binning,<br/>reset Npar = 4] --> BFIT

    BFIT -- pass --> PD[Generate pseudo-data:<br/>bin-wise Poisson fluctuation of the<br/>Npar+2 template, 100 toys, no upscaling]
    PD --> TESTS{"Tests on pseudo-data<br/>(per signal type, mass, width)<br/>1. B-only fit (Npar)<br/>2. Spurious signal &lt; 0.5 sigma_fit<br/>3. Signal injection &lt; 0.5 sigma_fit<br/>4. Bkg stability &lt; 3 sigma_stat"}
    TESTS -- any failure --> DISC[Discard Npar,<br/>Npar += 1] --> NPMAX2{Npar &le; 8?}
    NPMAX2 -- yes --> TESTS
    NPMAX2 -- no --> ALT[Fit range start +1 GeV<br/>OR drop a signal point] --> BFIT
    TESTS -- all pass --> KEEP([Fit strategy retained<br/>Npar, range])
```

Key prescriptions:

- **Pseudo-data generation privileges a wide range over low $N_\text{par}$**: only after $N_\text{par} = 8$ fails is the range reduced (by 1 GeV at the lower edge), and the resolution binning is re-derived from the new range start (otherwise BumpHunter masking misbehaves).
- A BumpHunter exclusion sitting **at the beginning of the spectrum** signals a turn-on/selection bias rather than a bump — it is absorbed by increasing $N_\text{par}$, not masked.
- **The test phase privileges increasing $N_\text{par}$ over restricting the range** (the successful B-only fit already validated the range).
- Once a strategy with $N_\text{par} \le 8$ passes, higher $N_\text{par}$ values (up to 8) are also validated so an $F$-test can be made later.
- All passing $(N_\text{par}, \text{range})$ combinations are retained, ordered by ascending range start.

## 2. Choosing a fit strategy (Figure 10.2)

```mermaid
flowchart TD
    IN([Strategies from<br/>'Validating a fit strategy']) --> SORT[Sort by fit range,<br/>largest to smallest]
    SORT --> ONE{Largest fit range<br/>appears once?}
    ONE -- yes --> DONE([Chosen fit strategy<br/>Npar, range])
    ONE -- no --> NP[Sort its Npar values,<br/>smallest to largest]
    NP --> FIT{"B-only fit (Npar)<br/>pass and stable?"}
    FIT -- fail 1st --> BH2[BumpHunter window exclusion<br/>max 3 resolution bins] --> FIT
    FIT -- fail 2nd --> DROP[Discard this Npar] --> FIT
    FIT -- pass --> FT{F-test vs next larger Npar:<br/>p F &ge; 0.05?}
    FT -- yes: keep simplest --> DONE
    FT -- no: prefer larger Npar --> FIT
```

The widest validated fit range wins; among equal ranges the [$F$-test](validation-tests.md#f-test) selects the **lowest $N_\text{par}$** that still describes the data.

## 3. Inspecting partially unblinded data (Figure 10.4 — 4% and 20% stages)

```mermaid
flowchart TD
    IN([Chosen fit strategy]) --> FIT{"B-only fit (Npar)<br/>pass and stable?"}
    FIT -- pass --> BHP{Full-range BumpHunter<br/>p &gt; 0.05?}
    FIT -- fail --> BH[BumpHunter window exclusion<br/>max 3 resolution bins] --> FIT2{"B-only fit (Npar)<br/>pass and stable?"}
    FIT2 -- fail --> CAL[Check for calibration /<br/>selection features]
    FIT2 -- pass --> BHP
    BHP --> CAL2[Check for calibration features<br/>regardless of outcome]
    CAL --> UND[Understand features]
    CAL2 --> GOOD{All good?}
    UND --> GOOD
    GOOD -- yes, with convener approval --> NEXT([Proceed to next<br/>unblinding phase])
```

Unblinding proceeds **only after any feature introduced by the jet calibration or analysis selection is understood**.

## 4. Inspecting the fully unblinded data (Figure 10.5 — 100% stage)

Two independent workflows run on the chosen fit strategy:

```mermaid
flowchart TD
    subgraph BHI[BumpHunter interpretation]
        B1{"B-only fit (Npar)<br/>pass and stable?"} -- pass --> CONS([Data consistent<br/>with B-only])
        B1 -- fail 1st --> M1[BumpHunter window exclusion<br/>max 3 resolution bins] --> B2{"B-only fit (Npar)<br/>pass?"}
        B2 -- fail 2nd --> F2[Understand feature affecting fit] --> NOI([No clear BH interpretation<br/>consult conveners])
        B2 -- pass --> P{Full-range BH<br/>p &gt; 0.05?}
        P -- yes --> CHK[Check masked features] --> CONS
        P -- no --> CHK2[Check for calibration features] --> SIG([Quantify discovery<br/>significance])
    end

    subgraph ZI[Gaussian / Z' interpretation]
        S1{"S+B fit per signal<br/>type, mass, width<br/>pass and stable?"} -- fail 1st --> M2[BumpHunter window exclusion<br/>max 3 resolution bins] --> S1
        S1 -- fail 2nd --> DEAD([S+B model failed<br/>to describe the data])
        S1 -- "pass, significant S" --> C2[Check for calibration features] --> STAT
        S1 -- "pass, no significant S" --> STAT([Statistical analysis:<br/>CLs limits or discovery])
    end
```

- The **BumpHunter interpretation** displays the B-only fit and the most discrepant region; discovery significance is quantified from its B-only fit results.
- The **Gaussian/$Z'$ interpretation** performs S+B fits for every signal hypothesis; in the absence of a significant signal, CL$_\text{s}$ limit setting proceeds. Signal properties would be measured with the S+B fits if an excess appears.
- Before the 100% stage the "validating" and "choosing" flowcharts (1 and 2) are re-run **without modification** on the full dataset.

## Visual summary (Figure 10.3)

The first flowchart can be viewed as a scan of the 2D plane spanned by the lower fit boundary $m_{jj}^\text{min}$ (x-axis) and $N_\text{par}$ (y-axis): starting at (85 GeV, $N_\text{par}$ = 4–5), each column is scanned upward through $N_\text{par} \le 8$ with B-only fits; the surviving points are then scanned upward again with the SS/SILT tests; and the passing configuration with the **lowest $m_{jj}^\text{min}$** is selected, to preserve sensitivity to the lowest signal masses.
