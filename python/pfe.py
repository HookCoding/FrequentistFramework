import argparse
from ExtractPostfitFromWS import PostfitExtractor
from ExtractFitParameters import FitParameterExtractor

parser = argparse.ArgumentParser(description="Run PostfitExtractor with custom parameters.")
parser.add_argument("--params", type=str, required=True,
                    help="Number of parameters string, e.g., 'seven'")
parser.add_argument("--maskstr", type=str, required=True,
                    help="'' or '_masked'")
parser.add_argument("--firstbin", type=int, required=True,
                    help="First bin number, e.g., 135")
args = parser.parse_args()

params_str = args.params
first_bin = args.firstbin
maskstr = args.maskstr

pfe = PostfitExtractor(
    datafile="/afs/cern.ch/work/t/tofitsch/tlafits/data23_histos.root",
    datahist="mjj",
    datafirstbin=first_bin,
    wsfile="/eos/home-t/tofitsch/tlafits/run_{0}_1000_{1}Par/FitResult_anaFit_{1}Par_bkgOnly{2}.root".format(first_bin, params_str, maskstr),
    rebinfile="/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_135.root",
    rebinhist="mjjBinning",
    maskmin=-1,
    bkgonly=True
)

fpe = FitParameterExtractor(wsfile="/eos/home-t/tofitsch/tlafits/run_{0}_1000_{1}Par/FitResult_anaFit_{1}Par_bkgOnly{2}.root".format(first_bin, params_str, maskstr))
fpe.WriteRoot("/eos/home-t/tofitsch/tlafits/run_{0}_1000_{1}Par/FitParameters_anaFit_{1}Par_bkgOnly{2}.root".format(first_bin, params_str, maskstr))

pfe.WriteRoot(
    "/eos/home-t/tofitsch/tlafits/run_{0}_1000_{1}Par/PostFit_anaFit_{1}Par_bkgOnly{2}.root".format(first_bin, params_str, maskstr),
    dirPerCategory=True
)
