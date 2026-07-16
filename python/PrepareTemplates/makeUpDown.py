import ROOT
import sys, re, os, math, argparse
from array import array

def main(args):

    for path in args:

        f_in = ROOT.TFile(path, "READ")
        f_out = ROOT.TFile(path.replace(".root", "_upDown.root"), "RECREATE")

        h_nom = f_in.Get("nominal")
        
        for histKey in f_in.GetListOfKeys():
            
            histName = histKey.GetName()
            
            h_in = f_in.Get(histName)
        
            if not "var" in histName or histName.endswith("_1u") or histName.endswith("_1d"):
                h_in.Write()
                continue
          
            if not isinstance(h_in, ROOT.TH1):
                continue
        
            h_1u = h_in.Clone(histName+"_1u")
            h_1d = h_in.Clone(histName+"_1d")

            for ibin in range(1, h_1u.GetNbinsX()+1):

                delta = h_1u.GetBinContent(ibin) - h_nom.GetBinContent(ibin)
                h_1d.SetBinContent(ibin, h_nom.GetBinContent(ibin) - delta)

            h_1u.Write()
            h_1d.Write()
            
        f_out.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
