import os

from run_execution import execute, execute_required


def build_fit_extract(
    topfile,
    datafile,
    datahist,
    rangelow,
    rangehigh,
    wsfile,
    fitresultfile,
    poi=None,
    maskrange=None,
):
    xmlreader_command = (
        f'xmlAnaWSBuilder/build/bin/XMLReader -x {topfile} -o "logy integral" --minimizerStrategy 0'
    )
    if not execute_required(
        xmlreader_command,
        "XMLReader workspace generation",
        expected_outputs=[wsfile],
    ):
        raise RuntimeError("XMLReader workspace generation failed")
    if poi:
        print("Now running s+b quickFit")
        _poi = "-p %s" % poi
        # bkgonly_opt = False
    else:
        print("Now running bkg-only quickFit")
        _poi = ""
        # bkgonly_opt = True

    if maskrange:
        _range = "--range SBLo_Run3TLA,SBHi_Run3TLA"
        maskmin = maskrange[0]
        maskmax = maskrange[1]
        print(">>>>>>>>>>>>>>>>>>>>>>>>>> BH mask range: " + str(maskmin) + "," + str(maskmax))
    else:
        _range = ""
        maskmin = -1
        maskmax = -1
        print(
            ">>>>>>>>>>>>>>>>>>>>>>>>>> no BH mask range: setting to -1 both maskmin "
            "and maskmax!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        )

    logfile = fitresultfile.replace("FitResult", "quickFitLog").replace(".root", ".log")
    edmplot = fitresultfile.replace("FitResult", "edm").replace(".root", ".pdf")

    # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! _poi is :"+str(_poi))  # noqa: E501
    quickfit_command = (
        "quickFit/build/quickFit --chi2fit 1 --poissonerror 1 -f %s -d combData %s "
        "--checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 "
        "--minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-6 "
        "%s -o %s > %s 2>&1"
    ) % (
        wsfile,
        _poi,
        _range,
        fitresultfile,
        logfile,
    )
    if not execute_required(
        quickfit_command,
        "quickFit background or signal fit",
        expected_outputs=[fitresultfile, logfile],
    ):
        raise RuntimeError("quickFit failed")

    execute("python plot_edm.py %s %s" % (logfile, edmplot))

    postfitfile = fitresultfile.replace("FitResult", "PostFit")
    parameterfile = fitresultfile.replace("FitResult", "FitParameters")

    # ROOT and the extractor classes are only needed from here on, once
    # both required subprocess steps (XMLReader, quickFit) have already
    # succeeded - deferring the import keeps the rest of this module (and
    # its two failure-path tests, which return before reaching this line)
    # plainly importable with no ROOT/sibling-module stubbing at all.
    import ROOT
    from ExtractFitParameters import FitParameterExtractor
    from ExtractPostfitFromWS import PostfitExtractor

    f = ROOT.TFile(datafile)
    d = f.Get(datahist)
    datafirstbin = d.FindBin(rangelow) - 1
    f.Close()

    # Define resolution binning for BH
    # binningFileName = f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"  # noqa: E501
    binningFileName = f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"

    print(binningFileName)
    if not os.path.exists(binningFileName):
        execute(
            f"python3 python/createBinning.py -s {rangelow} -e {rangehigh} " f"-o {binningFileName}"
        )

    print("EXECUTE: pfe = PostfitExtractor(")
    print("datafile=", datafile)
    print("datahist=", datahist)
    print("datafirstbin=", datafirstbin)
    print("wsfile=", fitresultfile)
    # rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",  # noqa: E501
    print("rebinfile=", f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root")
    print("rebinhist=", "mjjBinning")
    print("maskmin=", maskmin)
    print("bkgonly=", True)
    print(")")

    pfe = PostfitExtractor(
        datafile=datafile,
        datahist=datahist,
        datafirstbin=datafirstbin,
        wsfile=fitresultfile,
        # rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",  # noqa: E501
        rebinfile=f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
        rebinhist="mjjBinning",
        maskmin=maskmin,
        maskmax=maskmax,
        # bkgonly=bkgonly_opt
        bkgonly=True,
    )
    # If we used masking in a b-only fit then we need to calculate the p-val
    # from the correctly normalized postfit distribution
    if maskmin > -1 or maskmax > -1:
        pval = pfe.GetPval("Run3TLA_bkgonly_rebinned")  # should be Run3TLA or Run3TLA_rebinned?
    else:
        pval = pfe.GetPval("Run3TLA_rebinned")  # should be Run3TLA or Run3TLA_rebinned?

    print("pfe.WriteRoot(", postfitfile, ", dirPerCategory=True)")
    pfe.WriteRoot(postfitfile, dirPerCategory=True)
    # pfe.WriteRoot(postfitfile) # this looks problematic

    fpe = FitParameterExtractor(wsfile=fitresultfile)
    fpe.WriteRoot(parameterfile)

    return (pval, postfitfile, parameterfile)
