import ROOT
import sys, re, os, math, argparse
from array import array

def rebinDir(dir_in, dir_out):
    dir_out.cd()

    for key in dir_in.GetListOfKeys():
        name = key.GetName()
        h_in = dir_in.Get(name)

        if isinstance(h_in, ROOT.TDirectory):
            new_dir_out = dir_out.mkdir(name)
            rebinDir(h_in, new_dir_out)
            dir_out.cd()
            
        elif isinstance(h_in, ROOT.TH1):
            h_out = ROOT.TH1D(name, h_in.GetTitle(), h_in.GetNbinsX(), 0, h_in.GetNbinsX())

            for ibin in range(1, h_out.GetNbinsX()+1):
                h_out.SetBinContent(ibin, h_in.GetBinContent(ibin))
                h_out.SetBinError(ibin, h_in.GetBinError(ibin))

            h_out.Write(name)
    

def main(args):

    for path in args:

        f_in = ROOT.TFile(path, "READ")
        f_out = ROOT.TFile(path.replace(".root", "_fixedBins.root"), "RECREATE")
        
        rebinDir(f_in, f_out)

        f_out.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
