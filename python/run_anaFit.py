#!/usr/bin/env python

from __future__ import print_function

import json
import os
import shutil
import sys

from run_cli import build_arg_parser, normalize_signal_name
from run_execution import execute
from run_fit import build_fit_extract
from run_manifest import write_analysis_results
from run_masking import run_bumphunter, should_mask
from run_provenance import build_analysis_provenance
from run_templates import prepare_run_templates, replaceinfile


def run_anaFit(
    datafile,
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
    sigwidth=7.0,
    maskthreshold=0.01,
    doprefit=False,
    folder="run/",
    systdict=None,
    covariancedict=None,
):

    nbins = rangehigh - rangelow
    print("Fitting", nbins, "bins in range", rangelow, "-", rangehigh)

    args_names = locals()
    for key, value in args_names.items():
        print(f"{key}: {value}")

    provenance = build_analysis_provenance(
        datafile=datafile,
        datahist=datahist,
        topfile=topfile,
        categoryfile=categoryfile,
        backgroundfile=backgroundfile,
        signalfile=signalfile,
        rangelow=rangelow,
        rangehigh=rangehigh,
        dosignal=dosignal,
        dolimit=dolimit,
        doprefit=doprefit,
        maskthreshold=maskthreshold,
    )

    # Copies/edits the top/category/signal/background XML templates and,
    # when doprefit is set, seeds initial parameter values via PreFitter.
    # See python/run_templates.py for the extracted logic (Tier 3 Chunk 5).
    tmptopfile, tmpcategoryfile, xml_categoryfile, xml_wsfile = prepare_run_templates(
        folder=folder,
        topfile=topfile,
        categoryfile=categoryfile,
        backgroundfile=backgroundfile,
        signalfile=signalfile,
        signame=signame,
        wsfile=wsfile,
        sigmean=sigmean,
        sigwidth=sigwidth,
        datafile=datafile,
        datahist=datahist,
        rangelow=rangelow,
        rangehigh=rangehigh,
        nbkg=nbkg,
        nsig=nsig,
        doprefit=doprefit,
        systdict=systdict,
    )

    if dosignal:
        poi = "nsig_%s" % signame
        if sigwidth == -999:
            # poi="nsig_mR{}_gq0p1".format(sigmean)
            poi = "nsig_mR{}".format(sigmean)
    else:
        poi = None

    print(
        "##################################################################################################    do signal is ",  # noqa: E501
        dosignal,
    )
    print(
        "##################################################################################################    poi is  ",  # noqa: E501
        poi,
    )

    # shutil.copy2('/afs/cern.ch/work/t/tofitsch/tlafits/tomas/background_dijetTLA_fromTemplate.xml', tmpbackgroundfile) #XXX  # noqa: E501
    # shutil.copy2('/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/background_dijetTLA_fromTemplate.xml', tmpbackgroundfile) #XXX  # noqa: E501
    pval_global, postfitfile, parameterfile = build_fit_extract(
        topfile=tmptopfile,
        datafile=datafile,
        datahist=datahist,
        rangelow=rangelow,
        rangehigh=rangehigh,
        wsfile=wsfile,
        fitresultfile=outputfile,
        poi=poi,
    )

    print("Global fit p(chi2)=%.3f" % pval_global)

    final_p_chi2 = pval_global
    fit_was_masked = False

    if not should_mask(pval_global, maskthreshold):  # or True:
        print("p(chi2) threshold passed. Exiting with succesful fit.")
    else:
        print("p(chi2) threshold not passed.")

        #   if True:
        print("Now running BH for masking.")

        tmpcategoryfilemasked = tmpcategoryfile.replace(".xml", "_masked.xml")

        # need to unset pythonpath in order to not use cvmfs numpy
        # execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "J100yStar06_rebinned/postfit", "J100yStar06_rebinned/data", "{}/BHresults.json".format(folder)))  # noqa: E501
        BHresults = run_bumphunter(postfitfile, folder)

        # blind_min = 135
        # blind_max = 136

        # cmd = [
        #    "sed",
        #    "-i",
        #    "-E",
        #    f's/"MaskMin": [0-9.]+, "MaskMax": [0-9.]+, "BlindRange": "[0-9]+,[0-9]+"/'
        #    f'"MaskMin": {blind_min}, "MaskMax": {blind_max}, "BlindRange": "{blind_min},{blind_max}"/',  # noqa: E501
        #    "{}/BHresults.json".format(folder)
        # ]
        #
        # subprocess.run(cmd, check=True)

        tmptopfilemasked = tmptopfile.replace(".xml", "_masked.xml")
        wsfilemasked = wsfile.replace(".root", "_masked.root")
        outfilemasked = outputfile.replace(".root", "_masked.root")
        xml_categoryfilemasked = os.path.relpath(tmpcategoryfilemasked, os.getcwd())
        xml_wsfilemasked = os.path.relpath(wsfilemasked, os.getcwd())

        shutil.copy2(tmptopfile, tmptopfilemasked)
        shutil.copy2(tmpcategoryfile, tmpcategoryfilemasked)

        replaceinfile(
            tmptopfilemasked,
            [
                (xml_categoryfile, xml_categoryfilemasked),
                (r'(OutputFile="[A-Za-z0-9_/.-]*")', r'\1 Blind="true"'),
                (xml_wsfile, xml_wsfilemasked),
            ],
        )
        replaceinfile(
            tmpcategoryfilemasked,
            [(r'(Binning="\d+")', r'\1 BlindRange="%s"' % BHresults["BlindRange"])],
        )

        pval_masked, _, _ = build_fit_extract(
            tmptopfilemasked,
            datafile=datafile,
            datahist=datahist,
            rangelow=rangelow,
            rangehigh=rangehigh,
            wsfile=wsfilemasked,
            fitresultfile=outfilemasked,
            poi=poi,
            maskrange=(
                int(BHresults["MaskMin"]),
                int(BHresults["MaskMax"]),
            ),
        )

        print("Masked fit p(chi2)=%.3f" % pval_masked)

        if not should_mask(pval_masked, maskthreshold):
            print("p(chi2) threshold passed. Continuing with successful (window-excluded) fit.")
            wsfile = wsfilemasked
            final_p_chi2 = pval_masked
            fit_was_masked = True
        else:
            print("p(chi2) threshold still not passed.")
            print("Exiting with failed fit status.")
            return -1

    print()

    # blindrange not yet implemented with quickLimit
    if dolimit and dosignal and not should_mask(pval_global, maskthreshold):
        print("Now running quickLimit")
        # rtv=execute("timeout --foreground 1800 quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-8 --muScanPoints 20 --minStrat 1 --nllOffset 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")))  # noqa: E501
        rtv = execute(
            "quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 "
            "--minTolerance 1E-06 --muScanPoints 20 --minStrat 2 --nllOffset 0 "
            "--GKIntegrator 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult", "Limits"))
        )
        if rtv != 0:
            print("ERROR: quickLimit failed with exit code {}".format(rtv))
            return -1

    write_analysis_results(
        folder=folder,
        p_chi2=final_p_chi2,
        masked=fit_was_masked,
        provenance=provenance,
    )

    return 0


def main(args):

    parser = build_arg_parser()

    args = parser.parse_args(args)
    args.signame = normalize_signal_name(args.sigmean, args.sigwidth, args.signame)

    # create dir if not exists: https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    try:
        os.makedirs(args.folder)
    except OSError:
        if not os.path.isdir(args.folder):
            raise
    print("current working directory", os.getcwd())

    systdict = None
    if args.sysfile:
        with open(args.sysfile) as f:
            systdict = json.load(f)[str(args.sigmean)]
    # covariancedict is never assembled here today: no --covariancefile CLI
    # flag exists (see run_cli.py), and run_anaFit()'s own covariancedict
    # parameter is unused - this stub is left as-is (Tier 3 scope is
    # limited to moving existing code between files, not building out
    # unimplemented features). Kept commented, matching the un-added
    # --covariancefile flag it would depend on.
    # if args.covariancefile:
    #    with open(args.covariancefile) as f:
    #        covariancedict = json.load(f)[str(args.sigmean)]

    print(
        args.nbkg,
        args.nsig,
        args.dosignal,
        args.dolimit,
        args.sigmean,
        args.sigwidth,
        args.signame,
        args.maskthreshold,
        args.doprefit,
    )
    return run_anaFit(
        datafile=args.datafile,
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
        systdict=systdict,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
