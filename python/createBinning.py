import ROOT
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", type=int, required=True, help="Start of bin range")
parser.add_argument("-e", "--end", type=int, default=1000, help="End of bin range")
parser.add_argument("-o", "--output", type=str, required=True, help="output file path and histogram name")
args = parser.parse_args()

tfile = ROOT.TFile.Open("Input/data/dijetisrTLA/resolutionFits.root", "READ")
 if not tfile or tfile.IsZombie():
     raise OSError("Could not open Input/data/dijetisrTLA/resolutionFits.root")
 reso_fit = tfile.Get("gsc_mjj_reso_fit")
 if not reso_fit:
     raise KeyError("ROOT object gsc_mjj_reso_fit not found in resolutionFits.root")
bin_edge = args.start
bin_edges = [args.start]
while(bin_edge < args.end):
    resolution = reso_fit.Eval(bin_edge)
    up_edge = min(round(bin_edge + bin_edge * resolution), args.end)
    bin_edges.append(up_edge)
    bin_edge = up_edge

from array import array 
bin_edges = array("f", bin_edges)
outhist = ROOT.TH1F("mjjBinning", "", len(bin_edges)-1, bin_edges)
print("creating mjj resolution histogram ", args.output)
outfile = ROOT.TFile.Open(args.output, "RECREATE")
outfile.cd()
outhist.Write()
outfile.Close()
tfile.Close()
