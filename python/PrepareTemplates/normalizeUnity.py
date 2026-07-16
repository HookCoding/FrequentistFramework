import ROOT
import sys, re, os, math, argparse
from array import array

def main(args):

    for path in args:

        f_in = ROOT.TFile(path, "READ")
        f_out = ROOT.TFile(path.replace(".root", "_normalized.root"), "RECREATE")
        
        h_nom = f_in.Get("nominal")
        nEvt = h_nom.Integral() #default excludes over- / underflow

        for histKey in f_in.GetListOfKeys():
            
            histName = histKey.GetName()

            if not ("var" in histName or "nominal" in histName):
                continue
            
            h_in = f_in.Get(histName)

            if not isinstance(h_in, ROOT.TH1):
                continue
        
            h_in.Scale(1./nEvt)
            h_in.Write(histName)
            
        f_out.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
