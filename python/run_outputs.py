"""The set of files one run_anaFit() invocation produces in its run folder.

Run folders are reused - `folder` is a function of rangelow, rangehigh and pars - and nothing
used to delete what a previous run left there, so leftovers were read as the current run's:
the drivers select the postfit file to plot on the *existence* of the masked one,
plot_postfit.cpp draws the masked curve from whatever masked files it finds, and it stamps the
plot with BHresults.json whenever that file is present. See KNOWN_ISSUES.md issue 49.

Kept in its own module, free of ROOT, so it can be unit-tested against the recorded baselines
without the CVMFS environment. Every name here mirrors the line in run_anaFit.py that creates
it; when a new product is added there it must be added here too. tests/test_run_outputs.py
checks this list against two recorded runs, but that check is static JSON on both sides and
cannot see a run_anaFit.py change - the guarantee that a live run's output stays a subset of
this list is tests/repro.py check's manifest assertion in _check_one(). See
KNOWN_ISSUES.md issue 53.
"""


def _cards(folder, sigmean, sigwidth):
    """The four templated XML cards. sigwidth == -999 is the Z' sample mode, which renames
    the top and category cards after the mass point; the background and signal cards keep
    their names in both modes."""
    suffix = "_mR%s" % sigmean if sigwidth == -999 else ""
    return [
        "{}/dijetTLA_fromTemplate{}.xml".format(folder, suffix),
        "{}/category_dijetTLA_fromTemplate{}.xml".format(folder, suffix),
        "{}/background_dijetTLA_fromTemplate.xml".format(folder),
        "{}/signal_dijetTLA_fromTemplate.xml".format(folder),
    ]


def _fit_products(fitresultfile):
    """A FitResult path, and the four files build_fit_extract() derives from it by string
    replacement. Written the same way round as the code that creates them, so the two stay
    comparable by eye."""
    return [
        fitresultfile,
        fitresultfile.replace("FitResult", "PostFit"),
        fitresultfile.replace("FitResult", "FitParameters"),
        fitresultfile.replace("FitResult", "quickFitLog").replace(".root", ".log"),
        fitresultfile.replace("FitResult", "edm").replace(".root", ".pdf"),
    ]


def derived_outputs(folder, wsfile, outputfile, sigmean=None, sigwidth=None):
    """Every file this invocation may write into `folder`, whether or not it will.

    The masked twins and the Limits file are included unconditionally and that is the point:
    their presence is what a later reader - the drivers, plot_postfit.cpp, or whatever reads
    Limits_*.root - takes as current. A run that does not mask, or does not request limits,
    must not find a previous run's.

    AnaWSBuilder.dtd is deliberately absent - a symlink recreated only when missing, carrying
    no run state. postFit.pdf and post_fit.pdf are present although the *drivers* write them:
    they are derived from this function's output and live in its folder, so a run that dies
    before they are redrawn must not leave the previous run's looking current.
    """
    cards = _cards(folder, sigmean, sigwidth)
    paths = list(cards)
    # The masked repeat copies only the top and category cards (run_anaFit.py's
    # tmptopfilemasked / tmpcategoryfilemasked); the background and signal cards are reused
    # as they are.
    paths += [c.replace(".xml", "_masked.xml") for c in cards[:2]]

    for ws in (wsfile, wsfile.replace(".root", "_masked.root")):
        paths += [ws, ws.replace(".root", ".pdf")]  # XMLReader plots the workspace beside it

    for fitresult in (outputfile, outputfile.replace(".root", "_masked.root")):
        paths += _fit_products(fitresult)

    paths.append(outputfile.replace("FitResult", "Limits"))

    paths += [
        "{}/BHresults.json".format(folder),  # written only when the BumpHunter step runs
        "{}/postFit.pdf".format(folder),     # plotPostFit.py, from the driver
        "{}/post_fit.pdf".format(folder),    # plot_postfit.cpp, from the driver
    ]
    return paths
