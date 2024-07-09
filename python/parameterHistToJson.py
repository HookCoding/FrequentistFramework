#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
import ROOT

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, required=True, help='Input root file')
    parser.add_argument('--inhist', dest='inhist', type=str, default="postfit_params", help='Input parameter histogram name')
    parser.add_argument('--outfile', dest='outfile', type=str, help='Output json file')
    args = parser.parse_args(args)

    if not args.outfile:
        args.outfile = args.infile.replace(".root", ".json")

    d = {}

    fin = ROOT.TFile(args.infile, "READ")
    h = fin.Get(args.inhist)

    for i in range(1,h.GetNbinsX()+1):
        name = h.GetXaxis().GetBinLabel(i)
        val  = h.GetBinContent(i)
        d[name] = val
        
    fin.Close()

    with open(args.outfile, 'w') as fout:
        json.dump(d, fout)
        

if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
