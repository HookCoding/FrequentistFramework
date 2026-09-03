import argparse


def build_arg_parser():
    parser = argparse.ArgumentParser(description="%(prog)s [options]")
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
    parser.add_argument("--rangehigh", dest="rangehigh", type=int, help="End of fit range (in GeV)")
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
        help="Width of signal Gaussian for s+b fit (in %%). If -999 dealing with Zprime samples.",
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
    return parser


def normalize_signal_name(sigmean, sigwidth, signame):
    if not signame:
        if sigwidth == -999:
            signame = "mR%s" % (sigmean)
        else:
            signame = "mean%s_width%s" % (sigmean, sigwidth)
    return signame
