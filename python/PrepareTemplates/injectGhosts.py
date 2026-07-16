#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')

    args = parser.parse_args(args)
    ghost = 1e-20
    
    # load the histograms
    f_in = ROOT.TFile(args.infile, "READ")
    keys = f_in.GetListOfKeys()

    histograms = []

    for k in keys:
      histo  = f_in.Get(k.GetName())
      new_histo = histo.Clone()
      new_histo.Reset()
      new_histo.SetDirectory(0)
      new_histo.SetNameTitle(histo.GetName(), histo.GetTitle())
      for ibin in range(1, histo.GetNbinsX()+1):
	val = histo.GetBinContent(ibin)
	val_err = histo.GetBinError(ibin)
	if val == 0. or val_err == 0.: # it's an empty bin
	  new_histo.SetBinContent(ibin, ghost)
	  new_histo.SetBinError(ibin, math.sqrt(ghost))
	else:
	  new_histo.SetBinContent(ibin, val)
	  new_histo.SetBinError(ibin, val_err)
      histograms.append(new_histo)
    

    f_in.Close()

    f_out = ROOT.TFile(args.outfile, 'recreate')
    f_out.cd()
    for h in histograms:
      h.Write()
    f_out.Close()

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))

