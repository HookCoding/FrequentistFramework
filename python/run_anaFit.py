#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
from ExtractPostfitFromWS import PostfitExtractor, _check_rebin_pair
from ExtractFitParameters import FitParameterExtractor
from PreFit import PreFitter
import subprocess
import ROOT

def execute(cmd):  
    print("EXECUTE:", cmd)
    sys.stdout.flush() # keeps print and subprocess output in sync
    rtv = subprocess.call(cmd, shell=True)
    return rtv

def replaceinfile(f, old_new_list):
    with open(f, 'r') as file :
        filedata = file.read()

    try:
        for tup in old_new_list:
            filedata = re.sub(tup[0], tup[1], filedata)
    except:
        print("ERROR: replaceinfile expects a list of tuples of strings [(old1,new1),...] as input")
        print(old_new_list)
        sys.exit(-1)

    with open(f, 'w') as file:
        file.write(filedata)

def getchannel(categoryfile):
    # the channel name lives in the category card; deriving it beats hardcoding it per flavour
    with open(categoryfile) as f:
        m = re.search(r'Channel Name="([^"]+)"', f.read())
    if not m:
        print("ERROR: no 'Channel Name=' found in %s" % categoryfile)
        sys.exit(-1)
    return m.group(1)

def _failure_message(what, rtv, logfile=None):
    """Build the text of the error raised when a shelled-out binary exits non-zero."""
    msg = "%s failed with exit code %d." % (what, rtv)
    if rtv > 128:
        msg += " Exit %d means it was killed by signal %d, typically a segfault." % (rtv, rtv - 128)
    if logfile:
        msg += " Its output is in %s." % logfile
    return (
        msg + " The run stops here rather than extracting numbers from whatever the output "
        "file happens to contain."
    )

def execute_checked(cmd, what, logfile=None):
    """execute(), but a non-zero exit stops the run instead of printing a warning.

    These binaries do signal hard failures - a nonexistent card makes XMLReader exit 139
    (SIGSEGV), as does a nonexistent workspace for quickFit - and the framework used to
    print "Check if tolerable" and carry on into extraction regardless. Soft failures, a
    fit that runs, does not converge and exits 0, are not caught here; report_fit_quality()
    below is what catches those. See KNOWN_ISSUES.md.
    """
    rtv = execute(cmd)
    if rtv != 0:
        raise RuntimeError(_failure_message(what, rtv, logfile))
    return rtv

def _xmlreader_command(topfile):
    return 'xmlAnaWSBuilder/build/bin/XMLReader -x %s -o "logy integral" --minimizerStrategy 0' % topfile

def _quickfit_command(wsfile, poi_option, range_option, fitresultfile, logfile):
    return ("quickFit/build/quickFit --chi2fit 1 --poissonerror 1 -f %s -d combData %s --checkWS 1 "
            "--hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 2 "
            "--nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-6 %s -o %s &> %s"
            % (wsfile, poi_option, range_option, fitresultfile, logfile))

def _poi_option(poi):
    """Turn the parameter of interest into the quickFit flag, and say which fit is being run."""
    if poi:
        print("Now running s+b quickFit")
        return "-p %s" % poi
    print("Now running bkg-only quickFit")
    return ""

def _mask_options(maskrange, channel):
    """Turn the BumpHunter window into the quickFit range flag and the two mask boundaries.

    The pair travels together deliberately: a single -1 would make _compute_chi2_terms
    (ExtractPostfitFromWS.py) mask everything on one side, and nothing else enforces that
    maskmin and maskmax move as a pair.
    """
    if maskrange:
        maskmin = maskrange[0]
        maskmax = maskrange[1]
        print(">>>>>>>>>>>>>>>>>>>>>>>>>> BH mask range: "+str(maskmin)+","+str(maskmax))
        return "--range SBLo_%s,SBHi_%s" % (channel, channel), maskmin, maskmax
    print(">>>>>>>>>>>>>>>>>>>>>>>>>> no BH mask range: setting to -1 both maskmin and maskmax!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    return "", -1, -1

def _derived_output_paths(fitresultfile):
    """Derive every filename that is named after the fit result file.

    postfitfile must match plot_postfit.cpp's own Form("%s/PostFit_anaFit_%sPar_bkgOnly.root", ...):
    that contract exists only by convention across the two files and has no other check.
    """
    return {
        "logfile": fitresultfile.replace("FitResult", "quickFitLog").replace(".root", ".log"),
        "edmplot": fitresultfile.replace("FitResult", "edm").replace(".root", ".pdf"),
        "postfitfile": fitresultfile.replace("FitResult", "PostFit"),
        "parameterfile": fitresultfile.replace("FitResult", "FitParameters"),
    }


def _read_fit_quality(fitresultfile):
    """Read the fit status and covariance quality out of the fit result file.

    Returns (status, covqual), or None when the file holds no fitResult - a warning is printed
    and the file is closed in that case rather than raising, so a caller can decide what to do
    with a fit result it cannot assess.
    """
    f = ROOT.TFile(fitresultfile, "READ")
    r = f.Get("fitResult") if f and not f.IsZombie() else None
    if not r:
        print("WARNING: no fitResult in %s - cannot check fit status or covariance quality"
              % fitresultfile)
        if f:
            f.Close()
        return None
    status, covqual = r.status(), r.covQual()
    f.Close()
    return status, covqual

# RooFitResult::covQual(): -1 not available, 0 not calculated, 1 approximate,
# 2 full but forced positive-definite, 3 accurate. Every fit this repository has recorded is 2 -
# MINUIT added ~0.005 to the diagonal - so 2 is the default floor: it accepts what is already on
# record and refuses anything worse. Whether 2 is good enough for these fits is a physics
# judgement; this reports it so the judgement can be made. See KNOWN_ISSUES.md issue 40.
def _require_covqual(status, covqual, mincovqual, fitresultfile):
    """Print the quality line and refuse a covariance worse than mincovqual."""
    meaning = {-1: "not available", 0: "not calculated", 1: "approximate",
               2: "full, but forced positive-definite", 3: "accurate"}
    print("FIT QUALITY: status=%d covQual=%d (%s) [%s]"
          % (status, covqual, meaning.get(covqual, "unknown"), fitresultfile))
    if covqual < mincovqual:
        raise RuntimeError(
            "covQual=%d (%s) is below the required %d for %s. The fitted parameter ERRORS come "
            "from this matrix and feed the spurious-signal, injection-linearity and limit studies. "
            "Pass --mincovqual to lower the bar deliberately if that is what you want."
            % (covqual, meaning.get(covqual, "unknown"), mincovqual, fitresultfile))

def report_fit_quality(fitresultfile, mincovqual):
    """Print the fit's status and covariance quality, and refuse if the covariance
    is worse than mincovqual. Returns nothing; raises on an unacceptable fit."""
    quality = _read_fit_quality(fitresultfile)
    if quality is None:
        return
    status, covqual = quality
    _require_covqual(status, covqual, mincovqual, fitresultfile)


def build_fit_extract(topfile, datafile, datahist, rangelow, wsfile, fitresultfile, poi=None, maskrange=None,
                      channel="Run3TLA", rebinfile=None, rebinhist=None, mincovqual=2):
    execute_checked(_xmlreader_command(topfile),
                    "XMLReader (workspace build) on %s" % topfile) # minimizer strategy fast

    _poi = _poi_option(poi)
    _range, maskmin, maskmax = _mask_options(maskrange, channel)

    paths = _derived_output_paths(fitresultfile)
    logfile = paths["logfile"]
    edmplot = paths["edmplot"]

    execute_checked(_quickfit_command(wsfile, _poi, _range, fitresultfile, logfile),
                    "quickFit on %s" % wsfile, logfile=logfile)

    # Before anything is extracted from it: a fit nobody looked at is what issue 40 is about.
    report_fit_quality(fitresultfile, mincovqual)

    execute("python plot_edm.py %s %s" % (logfile, edmplot))

    postfitfile = paths["postfitfile"]
    parameterfile = paths["parameterfile"]

    datafirstbin = _data_first_bin(datafile, datahist, rangelow)
    binningFileName, binningHistName = _resolve_binning(rebinfile, rebinhist, rangelow)

    pval = _extract_postfit(datafile, datahist, datafirstbin, fitresultfile,
                            binningFileName, binningHistName, maskmin, maskmax,
                            postfitfile, channel)

    _extract_parameters(fitresultfile, parameterfile)

    return (pval, postfitfile, parameterfile)

def _data_first_bin(datafile, datahist, rangelow):
    """Read the data histogram and return the bin index just below the fit range."""
    f = ROOT.TFile(datafile)
    d = f.Get(datahist)
    datafirstbin = d.FindBin(rangelow) - 1
    f.Close()
    return datafirstbin

def _resolve_binning(rebinfile, rebinhist, rangelow):
    """Choose the resolution binning used for BH: an explicit --rebinfile/--rebinhist pair
    (e.g. the published Run 2 analysis binning) as-is, or the dijetisrTLA fallback, generated
    if it does not already exist.

    NOTE: createBinning.py's return code is ignored, as today. The fallback also defaults to
    --end 1000, so it truncates the rebinned chi2 for any rangehigh > 1000 - both Run 2 drivers
    avoid it by always supplying the pair.
    """
    if rebinfile and rebinhist:
        return rebinfile, rebinhist

    #binningFileName = f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"
    binningFileName = f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"
    binningHistName = "mjjBinning"

    print(binningFileName)
    if not os.path.exists(binningFileName):
        execute(f"python3 python/createBinning.py -s {rangelow} -o {binningFileName}")

    return binningFileName, binningHistName

def _extract_postfit(datafile, datahist, datafirstbin, fitresultfile, binningFileName, binningHistName,
                     maskmin, maskmax, postfitfile, channel):
    """Construct the PostfitExtractor, read the gating p-value, and write PostFit_*.root.

    The banner below prints the constructor call about to be made but has never printed maskmax
    alongside maskmin - a divergence between what is printed and what is actually constructed
    that predates this refactor and is left as-is.
    """
    print("EXECUTE: pfe = PostfitExtractor(")
    print("datafile=", datafile)
    print("datahist=", datahist)
    print("datafirstbin=", datafirstbin)
    print("wsfile=", fitresultfile)
        #rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
    print("rebinfile=", binningFileName)
    print("rebinhist=", binningHistName)
    print("maskmin=", maskmin)
    print("bkgonly=", True)
    print(")")

    pfe = PostfitExtractor(
        datafile=datafile,
        datahist=datahist,
        datafirstbin=datafirstbin,
        wsfile=fitresultfile,
        #rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
        rebinfile=binningFileName,
        rebinhist=binningHistName,
        maskmin=maskmin,
        maskmax=maskmax,
        #bkgonly=bkgonly_opt
        bkgonly=True
    )
    # The goodness-of-fit gate is defined on the background-only rebinned postfit, in both the
    # masked and unmasked cases. The gate asks whether the BACKGROUND MODEL describes the data, so
    # the background-only distribution is the one it should be read from - and for a masked b-only
    # fit that is also the correctly normalised distribution, which is why the masked branch
    # already used it. The unmasked branch used to read `<channel>_rebinned` instead, with a
    # comment asking which was right; the two differ by 1-2% relative, so a fit landing between
    # them was accepted or rejected according to which branch it happened to take. Settled by the
    # repository owner 2026-09-18. See KNOWN_ISSUES.md issue 39.
    pval = pfe.GetPval(channel+"_bkgonly_rebinned")

    print("pfe.WriteRoot(", postfitfile, ", dirPerCategory=True)")
    pfe.WriteRoot(postfitfile, dirPerCategory=True)
    #pfe.WriteRoot(postfitfile) # this looks problematic

    return pval

def _extract_parameters(fitresultfile, parameterfile):
    fpe = FitParameterExtractor(wsfile=fitresultfile)
    fpe.WriteRoot(parameterfile)

def _link_dtd(folder):
    """Symlink the DTD into the run folder if it is not already there.

    The dijetisrTLA copy is used for the dijetTLA analyses too, which is deliberate today.
    """
    if not os.path.isfile("{}/AnaWSBuilder.dtd".format(folder)):
      #execute("ln -sf $PWD/config/dijetTLA/AnaWSBuilder.dtd $PWD/{}/AnaWSBuilder.dtd".format(folder))
      #execute("ln -sf ~/WORK/tla/FrequentistFramework/config/dijetisrTLA/AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder))
      execute("ln -sf `realpath config/dijetisrTLA/AnaWSBuilder.dtd` {}/AnaWSBuilder.dtd".format(folder))
      print("this is happening")

def _temp_card_paths(folder, sigwidth, sigmean):
    """Build the four temporary card paths inside the run folder.

    sigwidth == -999 is the Z' sentinel: the top and category cards carry _mR<sigmean> so
    different mass points don't collide in the same folder; the signal and background cards
    don't need to, since they are the same shape regardless of mass point.
    """
    if sigwidth == -999: # running on zprime samples:
      print("Running in Zprime samples")
      tmpcategoryfile="{0}/category_dijetTLA_fromTemplate_mR{1}.xml".format(folder, sigmean)
      tmptopfile="{0}/dijetTLA_fromTemplate_mR{1}.xml".format(folder, sigmean)
    else:
      tmpcategoryfile="{}/category_dijetTLA_fromTemplate.xml".format(folder)
      tmptopfile="{}/dijetTLA_fromTemplate.xml".format(folder)
    tmpsignalfile="{}/signal_dijetTLA_fromTemplate.xml".format(folder)
    tmpbackgroundfile="{}/background_dijetTLA_fromTemplate.xml".format(folder)
    return tmptopfile, tmpcategoryfile, tmpsignalfile, tmpbackgroundfile

def _stage_cards(topfile, categoryfile, signalfile, tmptopfile, tmpcategoryfile, tmpsignalfile):
    """Copy the template cards into the run folder."""
    shutil.copy2(topfile, tmptopfile)
    shutil.copy2(categoryfile, tmpcategoryfile)
    if signalfile:
        shutil.copy2(signalfile, tmpsignalfile)

def _fill_top_card(tmptopfile, tmpcategoryfile, wsfile, signame):
    """Substitute the three top-card placeholders."""
    replaceinfile(tmptopfile,
                  [("CATEGORYFILE", tmpcategoryfile),
                   ("OUTPUTFILE", wsfile),
                   ("SIGNAME", signame),
               ])

def _fill_category_card(tmpcategoryfile, datafile, datahist, rangelow, rangehigh, nbins, nbkg, nsig,
                        signame, tmpsignalfile):
    """Substitute the nine category-card placeholders."""
    replaceinfile(tmpcategoryfile, [
        ("DATAFILE", datafile),
        ("DATAHIST", datahist),
        ("RANGELOW", str(rangelow)),
        ("RANGEHIGH", str(rangehigh)),
        ("BINS", str(nbins)),
        ("NBKG", nbkg),
	("NSIG", nsig),
	("SIGNAME", signame),
	("SIGNALFILE", tmpsignalfile)
    ])

def _signal_replacements(signame, sigmean, sigwidth, systdict):
    """Build the ordered list of signal-card substitutions.

    The final [MAG_...] -> [0] sweep zeroes any systematic magnitude placeholder the systdict
    branch above did not fill, and must stay last for that to work.
    """
    replacements = [("SIGNAME", str(signame)),
                    ("SIGMEAN", str(sigmean)),
                    ("SIGWIDTH", str(sigwidth)),
        ]

    if systdict != None:
        print("replacing in signalfile now")
        replacements.append(("NOMINAL_MEAN", str(systdict["nominal_mean"])))
        replacements.append(("NOMINAL_WIDTH", str(systdict["nominal_sigma"])))
        replacements.append(("NOMINAL_ALPHAL", str(systdict["nominal_alpha_l"])))
        replacements.append(("NOMINAL_ALPHAH", str(systdict["nominal_alpha_h"])))
        replacements.append(("NOMINAL_NL", str(systdict["nominal_n_l"])))
        replacements.append(("NOMINAL_NH", str(systdict["nominal_n_h"])))
        for source in systdict["unc_mean_sources"]:
            val = systdict["unc_mean_sources"][source]
            replacements.append(("\[MAG_SCALE_"+str(source)+"\]", "["+str(val)+"]"))
        for source in systdict["unc_sigma_sources"]:
            val = systdict["unc_sigma_sources"][source]
            replacements.append(("\[MAG_RESOLUTION_"+str(source)+"\]", "["+str(val)+"]"))

    #set any unreplaced uncertainties to 0 (starting with MAG_ and then any letters, numbers or _ -):
    replacements.append(("\[MAG_[a-zA-Z0-9_\-]*\]", "[0]"))
    return replacements

def _npars_from_filename(backgroundfile):
    """Derive the number of background parameters from the card's file name.

    KNOWN_ISSUES 42: a name matching no keyword silently falls back to 5 rather than raising.
    "three" is tested with its own `if`, and every keyword after it is an `elif` off "four" - so
    a name containing both "three" and "four" gives 4, not 3: the `three` branch runs first but
    does not stop the `four`/`elif` chain below it from also matching. Both quirks are preserved
    here rather than repaired.
    """
    nPars = 5

    if "three" in  backgroundfile:
        nPars = 3
    if "four" in  backgroundfile:
        nPars = 4
    elif "five" in  backgroundfile:
        nPars = 5
    elif "six" in  backgroundfile:
        nPars = 6
    elif "seven" in  backgroundfile:
        nPars = 7
    elif "eight" in  backgroundfile:
        nPars = 8
    elif "nine" in  backgroundfile:
        nPars = 9
    elif "ten" in  backgroundfile:
        nPars = 10

    return nPars

def _parse_card_par_ranges(tmpbackgroundfile):
    """Read the [PARn, low, high] placeholders out of the background card.

    A line containing "<!--" is skipped even when it holds placeholders - a commented-out line
    does not declare a parameter - and only lines containing "<ModelItem" are scanned at all.
    """
    cardmatches = []
    with open(tmpbackgroundfile) as f:
        for line in f:
            if not "<!--" in line and "<ModelItem" in line:
                cardmatches += re.findall('\[PAR(\d+),[ ]*([+-]?[0-9]+(?:[.][0-9]*)?),[ ]*([+-]?[0-9]+(?:[.][0-9]*)?)[ ]*\]', line)
    return cardmatches

def _check_card_pars(cardmatches, nPars, backgroundfile):
    """Refuse a card whose highest declared parameter index disagrees with nPars.

    The card is the authority on how many parameters it has; nPars is a substring guess off the
    file name, which silently falls back to 5 when no keyword matches (KNOWN_ISSUES 42). Checked
    here before the prefit spends 2000*nPars retries fitting the wrong function order, and before
    _card_par_ranges' assignment turns a card with more parameters than nPars into a bare
    IndexError.
    """
    cardpars = sorted({int(m[0]) for m in cardmatches})
    if not cardpars:
        print("WARNING: %s declares no [PARn, ...] placeholders, so the prefit has "
              "nothing to substitute into it; nPars=%d comes from the file name alone."
              % (backgroundfile, nPars))
    elif max(cardpars) != nPars:
        print("ERROR: %s declares parameters up to PAR%d, but nPars=%d was derived from "
              "its file name. Rename the card so the two agree, or correct the mapping "
              "in run_anaFit.py." % (backgroundfile, max(cardpars), nPars))
        sys.exit(-1)

def _card_par_ranges(cardmatches, nPars):
    """Build the parameter bounds: start from the defaults, then let the card override them."""
    # [1, -30, -30, -30, ...]
    parRangeLow = [1]+[-30]*(nPars-1)
    parRangeHigh = [1]+[30]*(nPars-1)

    for m in cardmatches:
        #m[0] is parN
        #m[1] is rangeLow
        #m[2] is rangeHigh
        parRangeLow[int(m[0])-1] = float(m[1])
        parRangeHigh[int(m[0])-1] = float(m[2])

    return parRangeLow, parRangeHigh

def _substitute_prefit_parameters(tmpbackgroundfile, initPars, nPars):
    """Write the fitted starting values back into the background card.

    KNOWN_ISSUES: each PARn is substituted in turn starting at PAR1, and re.sub has no word
    boundary here, so with ten parameters PAR1's substitution also matches the "PAR1" prefix of
    "PAR10" and corrupts it before PAR10's own turn arrives. Harmless at the five or six
    parameters either driver uses; preserved here rather than fixed.
    """
    for i in range(nPars):
        replaceinfile(tmpbackgroundfile,
                      [("PAR%d" % (i+1), str(initPars[i]))
                   ])

def _format_nbkg(_nbkg):
    """Format the prefit background yield as the card's "value, min, max" triple.

    The upper bound is twice the fitted value - a physics choice for the card's nbkg fit range,
    not an arbitrary margin.
    """
    return "%.1E, 0, %.1E" % (_nbkg, 2*_nbkg)

def _fit_accepted(pval, maskthreshold):
    """Decide whether a p(chi2) passes the gate. Strict >, so a p-value exactly equal to the
    threshold fails."""
    return pval > maskthreshold

def _run_bumphunter(postfitfile, channel, folder):
    """Run the BumpHunter window search in its own virtual environment, writing
    <folder>/BHresults.json.

    Reads channel+"_rebinned/postfit" and channel+"_rebinned/data" - the non-background-only
    histograms - while the p(chi2) gate is read from the background-only rebinned postfit
    (build_fit_extract / _extract_postfit). A real asymmetry between the two, not a typo to fix
    here.
    """
    # need to unset pythonpath in order to not use cvmfs numpy
    #execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "J100yStar06_rebinned/postfit", "J100yStar06_rebinned/data", "{}/BHresults.json".format(folder)))
    execute("source pyBumpHunter/pyBH_env/bin/activate; python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, channel+"_rebinned/postfit", channel+"_rebinned/data", "{}/BHresults.json".format(folder)))

def _read_bh_results(folder):
    """Load the BumpHunter results written by _run_bumphunter()."""
    with open("{}/BHresults.json".format(folder)) as f:
        return json.load(f)

def _masked_card_paths(tmptopfile, tmpcategoryfile, wsfile, outputfile):
    """Derive the four masked-variant paths.

    Uses str.replace, not a suffix operation - a ".xml"/".root" occurring anywhere else in the
    path, e.g. in a directory name, would be replaced too. Neither driver's paths do that.
    """
    tmptopfilemasked = tmptopfile.replace(".xml", "_masked.xml")
    tmpcategoryfilemasked = tmpcategoryfile.replace(".xml", "_masked.xml")
    wsfilemasked = wsfile.replace(".root", "_masked.root")
    outfilemasked = outputfile.replace(".root", "_masked.root")
    return tmptopfilemasked, tmpcategoryfilemasked, wsfilemasked, outfilemasked

def _write_masked_cards(tmptopfilemasked, tmpcategoryfilemasked, tmptopfile, tmpcategoryfile,
                        wsfile, wsfilemasked, blindrange):
    """Copy the top and category cards to their masked variants and inject the blinding
    attributes: Blind="true" on the top card's OutputFile, and BlindRange="<range>" on the
    category card's Binning."""
    shutil.copy2(tmptopfile, tmptopfilemasked)
    shutil.copy2(tmpcategoryfile, tmpcategoryfilemasked)

    replaceinfile(tmptopfilemasked,
                  [(tmpcategoryfile,tmpcategoryfilemasked),
                   (r'(OutputFile="[A-Za-z0-9_/.-]*")',r'\1 Blind="true"'),
                   (wsfile, wsfilemasked),])
    replaceinfile(tmpcategoryfilemasked,
                  [(r'(Binning="\d+")', r'\1 BlindRange="%s"' % blindrange)])

def _run_limit(wsfile, poi, outputfile):
    """Run quickLimit. Unreached by either locked analysis - repro.py does not cover this path,
    so the exact-string test in the unit suite is the only check it has."""
    #rtv=execute("timeout --foreground 1800 quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-8 --muScanPoints 20 --minStrat 1 --nllOffset 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")))
    # Same treatment as XMLReader and quickFit above. NOTE: the --dolimit path is not
    # exercised by either locked analysis, so this gate is reasoned-about, not regression-tested.
    execute_checked("quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-06 --muScanPoints 20 --minStrat 2 --nllOffset 0 --GKIntegrator 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")),
                    "quickLimit on %s" % wsfile)

def run_anaFit(datafile,
               datahist,
               topfile,
               categoryfile,
               wsfile,
               outputfile,
               nbkg,
               nsig,
               rangelow,
               rangehigh,
               signame,
               backgroundfile=None,
               signalfile=None,
               dosignal=False,
               dolimit=False,
               sigmean=1000,
               sigwidth=7.,
               maskthreshold=0.01,
               doprefit=False,
               folder="run/",
               systdict=None,
               covariancedict=None,
               rebinfile=None,
               rebinhist=None,
               mincovqual=2):

    # --rebinfile and --rebinhist are a pair. Supplying one used to be indistinguishable from
    # supplying neither: the selection in build_fit_extract is `if rebinfile and rebinhist`, so a
    # half-given pair fell through to the fallback binning, which createBinning.py generates only
    # up to 1000 GeV - silently changing the rebinned chi2, the p-value --maskthreshold gates on,
    # and the BumpHunter window, for any rangehigh above that. Refused here rather than at the
    # selection site, which is reached only after XMLReader and quickFit have run, and is reached
    # twice when the masked repeat happens. Shared with PostfitExtractor.__init__'s own guard - see
    # ExtractPostfitFromWS._check_rebin_pair(). See KNOWN_ISSUES.md issue 46.
    _check_rebin_pair(rebinfile, rebinhist)

    nbins=rangehigh - rangelow
    print("Fitting", nbins, "bins in range", rangelow, "-", rangehigh)

    # The channel name is authored once, in the category card. xmlAnaWSBuilder turns it into
    # the RooCategory label, hence the PostFit_*.root directory names and the SBLo_/SBHi_
    # blind ranges. Deriving it here keeps dijetisrTLA ("Run3TLA") and dijetTLA
    # ("J100yStar06") working without a second place to keep in sync.
    channel = getchannel(categoryfile)
    print("Channel name from", categoryfile, "->", channel)

    args_names = locals()
    for key, value in args_names.items():
      print(f"{key}: {value}")

    # generate the config files on the fly in run dir
    _link_dtd(folder)
    tmptopfile, tmpcategoryfile, tmpsignalfile, tmpbackgroundfile = _temp_card_paths(folder, sigwidth, sigmean)

    print("--------------------------------------> tmpcategoryfile: "+tmpcategoryfile)
    print("--------------------------------------> tmptopfile: "+tmptopfile)

    _stage_cards(topfile, categoryfile, signalfile, tmptopfile, tmpcategoryfile, tmpsignalfile)

    _fill_top_card(tmptopfile, tmpcategoryfile, wsfile, signame)

    if backgroundfile:
        shutil.copy2(backgroundfile, tmpbackgroundfile) 
        replaceinfile(tmpcategoryfile, 
                      [("BACKGROUNDFILE", tmpbackgroundfile)])
        
        if doprefit:
            nPars = _npars_from_filename(backgroundfile)

            cardmatches = _parse_card_par_ranges(tmpbackgroundfile)
            _check_card_pars(cardmatches, nPars, backgroundfile)
            parRangeLow, parRangeHigh = _card_par_ranges(cardmatches, nPars)

            print("Starting PreFit in parameter ranges:")
            print(parRangeLow)
            print(parRangeHigh)

            pf = PreFitter(
                datafile = datafile,
                datahist = datahist,
                xMin = rangelow,
                xMax = rangehigh,
                nPars = nPars,
                nRetries1 = 2000*nPars,
                nRetries2 = 2*nPars,
                fitLog = True,
                parRangeLow = parRangeLow,
                parRangeHigh = parRangeHigh,
            )

            initPars,_nbkg = pf.Fit()
            print(_nbkg)
            nbkg = _format_nbkg(_nbkg)
            print(_nbkg)

            print("Starting fit with initial pars", initPars)

            _substitute_prefit_parameters(tmpbackgroundfile, initPars, nPars)

    _fill_category_card(tmpcategoryfile, datafile, datahist, rangelow, rangehigh, nbins, nbkg, nsig,
                        signame, tmpsignalfile)

    if signalfile:
        #replaceinfile(tmpsignalfile,
        #              [("SIGMEAN", str(sigmean)),
        #               ("SIGWIDTH", str(sigwidth)),
        #])
        #  if covariancedict != None:
        #      print("replacing in signalfile now")
        #      replacements.append(("NOMINAL_MEAN", str(covariancedict["nominal_mean"])))
        #      replacements.append(("NOMINAL_WIDTH", str(covariancedict["nominal_sigma"])))
        #      replacements.append(("NOMINAL_ALPHAL", str(covariancedict["nominal_alpha_l"])))
        #      replacements.append(("NOMINAL_ALPHAH", str(covariancedict["nominal_alpha_h"])))
        #      replacements.append(("NOMINAL_NL", str(covariancedict["nominal_n_l"])))
        #      replacements.append(("NOMINAL_NH", str(covariancedict["nominal_n_h"])))
        #      replacements.append(("MAG_SCALE", str(covariancedict["covariance_cholesky"][4][4])))
        #      replacements.append(("MAG_RESOLUTION", str(covariancedict["covariance_cholesky"][5][5])))
        #      replacements.append(("MAG_CROSSTERM", str(covariancedict["covariance_cholesky"][5][4])))
        replacements = _signal_replacements(signame, sigmean, sigwidth, systdict)
        replaceinfile(tmpsignalfile, replacements)

    if dosignal:
        poi="nsig_%s" % signame
        if sigwidth == -999:
    	    # poi="nsig_mR{}_gq0p1".format(sigmean)
            poi="nsig_mR{}".format(sigmean)
    else:
        poi=None

    
    print("##################################################################################################    do signal is ", dosignal)
    print("##################################################################################################    poi is  ", poi)

    #shutil.copy2('/afs/cern.ch/work/t/tofitsch/tlafits/tomas/background_dijetTLA_fromTemplate.xml', tmpbackgroundfile) #XXX
    #shutil.copy2('/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/background_dijetTLA_fromTemplate.xml', tmpbackgroundfile) #XXX
    pval_global, postfitfile, parameterfile = build_fit_extract(topfile=tmptopfile,
                                                                datafile=datafile, 
                                                                datahist=datahist, 
                                                                rangelow=rangelow, 
                                                                wsfile=wsfile, 
                                                                fitresultfile=outputfile,
                                                                poi=poi,
                                                                channel=channel,
                                                                rebinfile=rebinfile,
                                                                rebinhist=rebinhist,
                                                                mincovqual=mincovqual,
							                                )
                                                        

    print ("Global fit p(chi2)=%.3f" % pval_global)

    if _fit_accepted(pval_global, maskthreshold): #or True:
        print("p(chi2) threshold passed. Exiting with succesful fit.")
    else:
        print("p(chi2) threshold not passed.")

        #   if True:
        print("Now running BH for masking.")

        _run_bumphunter(postfitfile, channel, folder)

        #blind_min = 135
        #blind_max = 136

        #cmd = [
        #    "sed",
        #    "-i",
        #    "-E",
        #    f's/"MaskMin": [0-9.]+, "MaskMax": [0-9.]+, "BlindRange": "[0-9]+,[0-9]+"/'
        #    f'"MaskMin": {blind_min}, "MaskMax": {blind_max}, "BlindRange": "{blind_min},{blind_max}"/',
        #    "{}/BHresults.json".format(folder)
        #]
        #
        #subprocess.run(cmd, check=True)

        # pass results of pyBH via this json file
        BHresults = _read_bh_results(folder)

        tmptopfilemasked, tmpcategoryfilemasked, wsfilemasked, outfilemasked = _masked_card_paths(
            tmptopfile, tmpcategoryfile, wsfile, outputfile)

        _write_masked_cards(tmptopfilemasked, tmpcategoryfilemasked, tmptopfile, tmpcategoryfile,
                            wsfile, wsfilemasked, BHresults["BlindRange"])

        pval_masked,_,_ = build_fit_extract(tmptopfilemasked,
                                            datafile=datafile, 
                                            datahist=datahist, 
                                            rangelow=rangelow, 
                                            wsfile=wsfilemasked, 
                                            fitresultfile=outfilemasked, 
                                            poi=poi,
                                            maskrange=(int(BHresults["MaskMin"]), int(BHresults["MaskMax"])),
                                            channel=channel,
                                            rebinfile=rebinfile,
                                            rebinhist=rebinhist,
                                            mincovqual=mincovqual,
                                            )

        print("Masked fit p(chi2)=%.3f" % pval_masked)

        if _fit_accepted(pval_masked, maskthreshold):
            print("p(chi2) threshold passed. Continuing with successful (window-excluded) fit.")
            wsfile=wsfilemasked
        else:
            print("p(chi2) threshold still not passed.")
            print("Exiting with failed fit status.")
            return -1

    print()

    # blindrange not yet implemented with quickLimit
    if dolimit and dosignal and _fit_accepted(pval_global, maskthreshold):
        print("Now running quickLimit")
        _run_limit(wsfile, poi, outputfile)

    return 0

def _build_parser():
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--datafile', dest='datafile', type=str, required=True, help='Input data file')
    parser.add_argument('--datahist', dest='datahist', type=str, required=True, help='Input finebinned data histogram name')
    parser.add_argument('--topfile', dest='topfile', type=str, required=True, help='Input top-level xml card')
    parser.add_argument('--categoryfile', dest='categoryfile', type=str, required=True, help='Input category xml card')
    parser.add_argument('--backgroundfile', dest='backgroundfile', type=str, help='Input background xml card')
    parser.add_argument('--signalfile', dest='signalfile', default= None, type=str, help='Input signal xml card')
    parser.add_argument('--wsfile', dest='wsfile', type=str, required=True, help='Output workspace file')
    parser.add_argument('--outputfile', dest='outputfile', type=str, required=True, help='Output fitresult file')
    parser.add_argument('--nbkg', dest='nbkg', type=str, required=True, help='Initial value and range of nbkg par (e.g. "2E8,0,3E8")')
    parser.add_argument('--nsig', dest='nsig', type=str, default='0,-1E6,1E6', help='Initial value and range of nsig par (e.g. "0,-1E6,1E6")')
    parser.add_argument('--rangelow', dest='rangelow', type=int, help='Start of fit range (in GeV)')
    parser.add_argument('--rangehigh', dest='rangehigh', type=int, help='End Start of fit range (in GeV)')
    parser.add_argument('--dosignal', dest='dosignal', action="store_true", help='Perform s+b fit (default: bkg-only)')
    parser.add_argument('--dolimit', dest='dolimit', action="store_true", help='Perform limit setting')
    parser.add_argument('--signame', dest='signame', type=str, help='Name of the signal parameter')
    parser.add_argument('--sigmean', dest='sigmean', type=int, default=1000, help='Mean of signal Gaussian for s+b fit (in GeV)')
    parser.add_argument('--sigwidth', dest='sigwidth', type=float, default=7., help='Width of signal Gaussian for s+b fit (in %). If -999 dealing with Zprime samples.')
    parser.add_argument('--maskthreshold', dest='maskthreshold', type=float, default=0.01, help='Threshold of p(chi2) below which to run BH and mask the most significant window')
    parser.add_argument('--mincovqual', dest='mincovqual', type=int, default=2,
                        help='Refuse a fit whose RooFitResult covQual is below this '
                             '(-1 not available, 0 not calculated, 1 approximate, 2 full but '
                             'forced positive-definite, 3 accurate). Default 2, which is what '
                             'every recorded fit here has. See KNOWN_ISSUES.md issue 40.')
    parser.add_argument('--doprefit', dest='doprefit', action="store_true", help='Perform ROOT prefit before quickFit')
    parser.add_argument('--folder', dest='folder', type=str, default='run', help='Output folder to store configs and results (default: run)')
    parser.add_argument('--sysfile', dest='sysfile', type=str, help='Path to json file containing signal systematics dict')
    parser.add_argument('--rebinfile', dest='rebinfile', type=str, default=None,
                        help='ROOT file whose histogram bin edges define the rebinning used for the '
                             'rebinned chi2/p-value and for BumpHunter. Default: auto-generate '
                             'Input/data/dijetisrTLA/mjjResolutionBinning_<rangelow>.root')
    parser.add_argument('--rebinhist', dest='rebinhist', type=str, default=None,
                        help='Histogram name inside --rebinfile (may be a directory-qualified path). '
                             'Default: mjjBinning')
    return parser

def _load_systdict(sysfile, sigmean):
    """Load the signal systematics dict for one mass point.

    Returns None when no --sysfile was given. Raises where the file is read, immediately -
    rather than ~400 lines later inside _signal_replacements(), where a missing sigmean entry
    would otherwise surface as a KeyError far from its cause.
    """
    if not sysfile:
        return None
    with open(sysfile) as f:
        return json.load(f)[str(sigmean)]

def main(args):
    parser = _build_parser()
    args = parser.parse_args(args)
    if not args.signame:
        if args.sigwidth == -999:
            args.signame="mR%s" % (args.sigmean)
        else:
            args.signame="mean%s_width%s" % (args.sigmean, args.sigwidth)

    # create dir if not exists: https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    try: 
        os.makedirs(args.folder)
    except OSError:
        if not os.path.isdir(args.folder):
            raise
    print("current working directory", os.getcwd())

    systdict = _load_systdict(args.sysfile, args.sigmean)
    covariancedict = None
    #if args.covariancefile:
    #    with open(args.covariancefile) as f:
    #        covariancedict = json.load(f)[str(args.sigmean)]

    print(args.nbkg,args.nsig,args.dosignal,args.dolimit,args.sigmean,args.sigwidth,args.signame,args.maskthreshold,args.doprefit)
    # `return`, not a bare call: run_anaFit gives -1 when a fit fails p(chi2), gets
    # its most significant window masked, is re-fitted and fails again. Dropping
    # that made sys.exit(None) exit 0, so the framework's own "this result is not
    # acceptable" verdict reported success (KNOWN_ISSUES 38).
    return run_anaFit(datafile=args.datafile,
               datahist=args.datahist,
               topfile=args.topfile,
               categoryfile=args.categoryfile,
               backgroundfile=args.backgroundfile,
               signalfile=args.signalfile,
               wsfile=args.wsfile,
               outputfile=args.outputfile,
               nbkg=args.nbkg,
               nsig=args.nsig,
               rangelow=args.rangelow,
               rangehigh=args.rangehigh,
               dosignal=args.dosignal,
               dolimit=args.dolimit,
               sigmean=args.sigmean,
               sigwidth=args.sigwidth,
               folder=args.folder,
               signame=args.signame,
               maskthreshold=args.maskthreshold,
               doprefit=args.doprefit,
               rebinfile=args.rebinfile,
               rebinhist=args.rebinhist,
               mincovqual=args.mincovqual,
               systdict=systdict)



if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
