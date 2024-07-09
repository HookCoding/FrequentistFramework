#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse

gRand = ROOT.TRandom3()

def fluctuatePoisson(hist):
    global gRand

    result = hist.Clone("fluctuated hist")
    result.Reset("M")

    nBinsX = hist.GetNbinsX()
    nBinsY = hist.GetNbinsY()

    for i in range(0, nBinsX+2):
        for j in range(0, nBinsY+2):
            ibin = hist.GetBin(i, j)
            fluc = gRand.Poisson(hist.GetBinContent(ibin))
            if fluc >= 0:
                result.SetBinContent(ibin, fluc)
                result.SetBinError(ibin, math.sqrt(fluc))

    return result


def main(args):
    global gRand

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
    parser.add_argument('--inhist', dest='inhist', type=str, default='', help='Input hist name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
    parser.add_argument('--outhist', dest='outhist', type=str, default='', help='Output hist name')
    parser.add_argument('--nreplicas', dest='nreplicas', type=int, default=50, help='Number of replicas to generate')
    parser.add_argument('--scaling', dest='scaling', type=float, default=1., help='factor to scale the lumi by')
    
    args = parser.parse_args(args)

    f_in = ROOT.TFile(args.infile, "READ")
    h_in = f_in.Get(args.inhist)
    h_in.SetDirectory(0)
    f_in.Close()

    h_in.Scale(args.scaling)

    f_out = ROOT.TFile(args.outfile, "RECREATE")
    f_out.cd()

    # Set sqrt(N) errors in upscaled hist and write to file
    nBinsX = h_in.GetNbinsX()
    nBinsY = h_in.GetNbinsY()
    for i in range(0, nBinsX+2):
        for j in range(0, nBinsY+2):
            ibin = h_in.GetBin(i, j)
            h_in.SetBinError(ibin, math.sqrt(h_in.GetBinContent(ibin)))

    h_in.Write("unfluctuated")

    steps = max(1, args.nreplicas/20)
    
    for i in range(0, args.nreplicas):
        if (i%steps == 0):
            print(i,"/",args.nreplicas)

        gRand.SetSeed(i)
        h_out = fluctuatePoisson(h_in)
        h_out.Write("%s_%d" % (args.outhist, i))
   
    f_out.Close()


if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
