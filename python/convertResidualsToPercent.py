#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse, array

def main(args):
    global gRand

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
#    parser.add_argument('--outhist', dest='outhist', type=str, default='', help='Output hist name')
    parser.add_argument('--indir', dest='indir', type=str, default='J100yStar06', help='input TDirectory name')
    parser.add_argument('--indirrebinned', dest='indirrebinned', type=str, default='J100yStar06_rebinned', help='input rebinned TDirectory name')
    parser.add_argument('--datahist', dest='datahist', type=str, default='data', help='data hist name')
    parser.add_argument('--postfithist', dest='postfithist', type=str, default='postfit', help='postfit hist name')
    
    args = parser.parse_args(args)

    f_in = ROOT.TFile(args.infile, "READ")

    d_in = f_in.Get(args.indir)
    d_in_rebinned = f_in.Get(args.indirrebinned)

    h_data = d_in.Get(args.datahist)
    h_postfit = d_in.Get(args.postfithist)

    h_data_rebinned = d_in_rebinned.Get(args.datahist)
    h_postfit_rebinned = d_in_rebinned.Get(args.postfithist)

    h_data.SetDirectory(0)
    h_postfit.SetDirectory(0)
    h_data_rebinned.SetDirectory(0)
    h_postfit_rebinned.SetDirectory(0)

    f_in.Close()

    a = array.array('d', range(100, 1500, 20))
    
    h_data = h_data.Rebin(len(a)-1,"h_data_20GeV", a)
    h_postfit = h_postfit.Rebin(len(a)-1,"h_postfit_20GeV", a)
    
    h_out = h_data.Clone()
    h_out_rebinned = h_data_rebinned.Clone()

    h_out.Add(h_postfit, -1)
    h_out.Divide(h_postfit)

    h_out_rebinned.Add(h_postfit_rebinned, -1)
    h_out_rebinned.Divide(h_postfit_rebinned)
        
    f_out = ROOT.TFile(args.outfile, "RECREATE")
    f_out.cd()

    h_out.Write("residuals")
    h_out_rebinned.Write("residuals_rebinned")

    f_out.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
