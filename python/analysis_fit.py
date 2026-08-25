from __future__ import annotations

import os
from typing import Callable

import ROOT
from ExtractFitParameters import FitParameterExtractor
from ExtractPostfitFromWS import PostfitExtractor

try:
    from python.analysis_commands import build_quickfit_command, build_xmlreader_command
except ModuleNotFoundError:
    from analysis_commands import build_quickfit_command, build_xmlreader_command


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
    *,
    execute_required_fn: Callable = None,
    execute_fn: Callable = None,
    root_module=ROOT,
    postfit_extractor=PostfitExtractor,
    fit_parameter_extractor=FitParameterExtractor,
):
    if execute_required_fn is None or execute_fn is None:
        raise ValueError("Command execution functions are required")

    xmlreader_command = build_xmlreader_command(topfile, wsfile)
    if not execute_required_fn(
        xmlreader_command,
        "XMLReader workspace generation",
        expected_outputs=[wsfile],
    ):
        raise RuntimeError("XMLReader workspace generation failed")

    if poi:
        print("Now running s+b quickFit")
    else:
        print("Now running bkg-only quickFit")

    if maskrange:
        maskmin = maskrange[0]
        maskmax = maskrange[1]
        print(">>>>>>>>>>>>>>>>>>>>>>>> BH mask range: " + str(maskmin) + "," + str(maskmax))
    else:
        maskmin = -1
        maskmax = -1
        print(
            ">>>>>>>>>>>>>>>>>>>>>>>> no BH mask range: setting to -1 both maskmin and "
            "maskmax!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        )

    quickfit_command, logfile = build_quickfit_command(wsfile, poi, maskrange, fitresultfile)
    edmplot = fitresultfile.replace("FitResult", "edm").replace(".root", ".pdf")
    if not execute_required_fn(
        quickfit_command,
        "quickFit background or signal fit",
        expected_outputs=[fitresultfile, logfile],
    ):
        raise RuntimeError("quickFit failed")

    execute_fn("python plot_edm.py %s %s" % (logfile, edmplot))

    postfitfile = fitresultfile.replace("FitResult", "PostFit")
    parameterfile = fitresultfile.replace("FitResult", "FitParameters")

    root_file = root_module.TFile(datafile)
    data_histogram = root_file.Get(datahist)
    datafirstbin = data_histogram.FindBin(rangelow) - 1
    root_file.Close()

    binning_file = f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"
    print(binning_file)
    if not os.path.exists(binning_file):
        execute_fn(
            f"python3 python/createBinning.py -s {rangelow} -e {rangehigh} " f"-o {binning_file}"
        )

    print("EXECUTE: pfe = PostfitExtractor(")
    print("datafile=", datafile)
    print("datahist=", datahist)
    print("datafirstbin=", datafirstbin)
    print("wsfile=", fitresultfile)
    print("rebinfile=", binning_file)
    print("rebinhist=", "mjjBinning")
    print("maskmin=", maskmin)
    print("bkgonly=", True)
    print(")")

    postfit = postfit_extractor(
        datafile=datafile,
        datahist=datahist,
        datafirstbin=datafirstbin,
        wsfile=fitresultfile,
        rebinfile=binning_file,
        rebinhist="mjjBinning",
        maskmin=maskmin,
        maskmax=maskmax,
        bkgonly=True,
    )
    if maskmin > -1 or maskmax > -1:
        pval = postfit.GetPval("Run3TLA_bkgonly_rebinned")
    else:
        pval = postfit.GetPval("Run3TLA_rebinned")

    print("pfe.WriteRoot(", postfitfile, ", dirPerCategory=True)")
    postfit.WriteRoot(postfitfile, dirPerCategory=True)

    fit_parameters = fit_parameter_extractor(wsfile=fitresultfile)
    fit_parameters.WriteRoot(parameterfile)
    return (pval, postfitfile, parameterfile)
