#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from ROOT import *

def integrateGaus(mean, sigma, low, high):
    denom = math.sqrt(2) * sigma
    return 0.5 * ( math.erf((high-mean)/denom) - math.erf((low-mean)/denom) )

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
    parser.add_argument('--histname', dest='histname', type=str, default='data', help='Name of hist in infile')
    parser.add_argument('--sigMean', dest='sigMean', type=float, default=-999., help='Mean of signal gaus')
    parser.add_argument('--sigWidth', dest='sigWidth', type=float, default=5, help='Width of signal gaus')
    parser.add_argument('--injectGhost', dest='injectGhost', action='store_true', help='Set empty bins to small number')

    args = parser.parse_args(args)

    # load the histograms
    f_in = ROOT.TFile(args.infile, "READ")

    h_in = f_in.Get(args.histname)
    h_signal = h_in.Clone("signal")
    h_signal.Reset("M")
    h_signal.SetDirectory(0)

    f_in.Close()

    for ibin in range(1, h_signal.GetNbinsX()+1):
        fraction = integrateGaus(args.sigMean, (args.sigWidth*0.01) * args.sigMean, h_signal.GetXaxis().GetBinLowEdge(ibin), h_signal.GetXaxis().GetBinUpEdge(ibin))

        if args.injectGhost and fraction == 0.:
            fraction=1.e-20

        h_signal.SetBinContent(ibin, fraction)

    f_out = ROOT.TFile(args.outfile, "RECREATE")
    h_signal.Write("signal")
    f_out.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
