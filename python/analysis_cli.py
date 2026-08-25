from __future__ import annotations

import argparse
import json
import os
from typing import Callable, Sequence


def main(args: Sequence[str], run_fn: Callable) -> int:
    parser = argparse.ArgumentParser(description="%prog [options]")
    parser.add_argument(
        "--datafile", dest="datafile", type=str, required=True, help="Input data file"
    )
    parser.add_argument(
        "--datahist",
        dest="datahist",
        type=str,
        required=True,
        help="Input finebinned data histogram name",
    )
    parser.add_argument(
        "--topfile", dest="topfile", type=str, required=True, help="Input top-level xml card"
    )
    parser.add_argument(
        "--categoryfile",
        dest="categoryfile",
        type=str,
        required=True,
        help="Input category xml card",
    )
    parser.add_argument(
        "--backgroundfile", dest="backgroundfile", type=str, help="Input background xml card"
    )
    parser.add_argument(
        "--signalfile", dest="signalfile", default=None, type=str, help="Input signal xml card"
    )
    parser.add_argument(
        "--wsfile", dest="wsfile", type=str, required=True, help="Output workspace file"
    )
    parser.add_argument(
        "--outputfile", dest="outputfile", type=str, required=True, help="Output fitresult file"
    )
    parser.add_argument(
        "--nbkg",
        dest="nbkg",
        type=str,
        required=True,
        help='Initial value and range of nbkg par (e.g. "2E8,0,3E8")',
    )
    parser.add_argument(
        "--nsig",
        dest="nsig",
        type=str,
        default="0,-1E6,1E6",
        help='Initial value and range of nsig par (e.g. "0,-1E6,1E6")',
    )
    parser.add_argument("--rangelow", dest="rangelow", type=int, help="Start of fit range (in GeV)")
    parser.add_argument(
        "--rangehigh", dest="rangehigh", type=int, help="End Start of fit range (in GeV)"
    )
    parser.add_argument(
        "--dosignal",
        dest="dosignal",
        action="store_true",
        help="Perform s+b fit (default: bkg-only)",
    )
    parser.add_argument(
        "--dolimit", dest="dolimit", action="store_true", help="Perform limit setting"
    )
    parser.add_argument("--signame", dest="signame", type=str, help="Name of the signal parameter")
    parser.add_argument(
        "--sigmean",
        dest="sigmean",
        type=int,
        default=1000,
        help="Mean of signal Gaussian for s+b fit (in GeV)",
    )
    parser.add_argument(
        "--sigwidth",
        dest="sigwidth",
        type=float,
        default=7.0,
        help="Width of signal Gaussian for s+b fit (in %). If -999 dealing with Zprime samples.",
    )
    parser.add_argument(
        "--maskthreshold",
        dest="maskthreshold",
        type=float,
        default=0.01,
        help="Threshold of p(chi2) below which to run BH and mask the most significant window",
    )
    parser.add_argument(
        "--doprefit",
        dest="doprefit",
        action="store_true",
        help="Perform ROOT prefit before quickFit",
    )
    parser.add_argument(
        "--folder",
        dest="folder",
        type=str,
        default="run",
        help="Output folder to store configs and results (default: run)",
    )
    parser.add_argument(
        "--sysfile",
        dest="sysfile",
        type=str,
        help="Path to json file containing signal systematics dict",
    )

    parsed_args = parser.parse_args(args)
    if not parsed_args.signame:
        if parsed_args.sigwidth == -999:
            parsed_args.signame = "mR%s" % parsed_args.sigmean
        else:
            parsed_args.signame = "mean%s_width%s" % (
                parsed_args.sigmean,
                parsed_args.sigwidth,
            )

    try:
        os.makedirs(parsed_args.folder)
    except OSError:
        if not os.path.isdir(parsed_args.folder):
            raise
    print("current working directory", os.getcwd())

    systdict = None
    if parsed_args.sysfile:
        with open(parsed_args.sysfile) as file:
            systdict = json.load(file)[str(parsed_args.sigmean)]

    print(
        parsed_args.nbkg,
        parsed_args.nsig,
        parsed_args.dosignal,
        parsed_args.dolimit,
        parsed_args.sigmean,
        parsed_args.sigwidth,
        parsed_args.signame,
        parsed_args.maskthreshold,
        parsed_args.doprefit,
    )
    return run_fn(
        datafile=parsed_args.datafile,
        datahist=parsed_args.datahist,
        topfile=parsed_args.topfile,
        categoryfile=parsed_args.categoryfile,
        backgroundfile=parsed_args.backgroundfile,
        signalfile=parsed_args.signalfile,
        wsfile=parsed_args.wsfile,
        outputfile=parsed_args.outputfile,
        nbkg=parsed_args.nbkg,
        nsig=parsed_args.nsig,
        rangelow=parsed_args.rangelow,
        rangehigh=parsed_args.rangehigh,
        dosignal=parsed_args.dosignal,
        dolimit=parsed_args.dolimit,
        sigmean=parsed_args.sigmean,
        sigwidth=parsed_args.sigwidth,
        folder=parsed_args.folder,
        signame=parsed_args.signame,
        maskthreshold=parsed_args.maskthreshold,
        doprefit=parsed_args.doprefit,
        systdict=systdict,
    )
