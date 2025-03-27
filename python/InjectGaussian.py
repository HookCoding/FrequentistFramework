#!/usr/bin/env python
from __future__ import print_function

import ROOT
import sys, re, os, math, argparse

def GetNsig(histbkg, sigmean, sigwidth, sigamp, xmin=0, xmax=1e100):
    # determine the gaussian amplitude (ntimes * sqrt(n) in FWHW range)
    rangeLow = max(sigmean  - 1.18*(sigwidth*0.01) * sigmean, xmin)
    rangeHigh = min(sigmean + 1.18*(sigwidth*0.01) * sigmean, xmax)
    binLow = histbkg.FindBin(rangeLow)
    binHigh = histbkg.FindBin(rangeHigh)
    nBkg = histbkg.Integral(binLow, binHigh)
    nSig = 0.

    mygaus = ROOT.TF1( 'mygaus', 'gaus', 0, 10000) 
    sigma = (sigwidth*0.01) * sigmean 
    mygaus.SetParameters(1.0, sigmean, sigma) 
    gaus_integral = mygaus.Integral(mygaus.GetXmin(), mygaus.GetXmax())

    if nBkg > 0.:
        # fSig = 0.762 #integral from -1.18 sigma to +1.18 sigma
        fSig = mygaus.Integral(rangeLow, rangeHigh) / gaus_integral
        nSig = int(math.sqrt(nBkg)*sigamp / fSig)

    print("rangeLow:", rangeLow, "rangeHigh:", rangeHigh, "nBkg:", nBkg, "fSig:", fSig)
    # print(histbkg.GetBinCenter(binLow), histbkg.GetBinCenter(binHigh), nBkg, fSig)

    return nSig

def InjectGaussian(infile, histname, sigmean, sigwidth, sigamp, outfile, firsttoy=None, lasttoy=None, xmin=0, xmax=1e100):
    f_in = ROOT.TFile(infile, "READ")
    f_out = ROOT.TFile(outfile, "RECREATE")
    f_out.cd()

    gRand = ROOT.TRandom3()
    seed = 0

    for histKey in f_in.GetListOfKeys():
        histName = histKey.GetName()
        
        if not histname in histName:
            continue
        if firsttoy != None and lasttoy != None and re.search(r'.*_(\d+)', histName):
            #reduce size by omitting all other toys
            toy = int(re.search(r'.*_(\d+)', histName).group(1))
            if toy < firsttoy or toy > lasttoy:
                seed += 1
                continue

        hist = f_in.Get(histName).Clone()
        hinj = hist.Clone()
        hgaus = hist.Clone("injectedSignal") 
        hgaus.Reset("M")

        # define the parameters of the gaussian and fill it
        if sigmean > 0.0:
            nSig = GetNsig(hist, sigmean, sigwidth, sigamp, xmin, xmax)
            if nSig > 0.:
                print('Injecting Signal with mean = ', sigmean, ' Number of events = ', nSig, end=' ') 
                print(' (ntimes = ', sigamp, ') Width = ', sigwidth)

                sigma = (sigwidth*0.01) * sigmean 
                mygaus = ROOT.TF1( 'mygaus', 'gaus', 0, 10000) 
                mygaus.SetParameters(1.0, sigmean, sigma) 

                gRand.SetSeed(seed)
                hgaus.FillRandom('mygaus', nSig) 
                hinj.Add(hgaus)

        hinj.Write(histName)
        hist.Write(histName+"_beforeInjection")
        hgaus.Write(histName+"_injection")

        seed += 1
            
    f_out.Close()


def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='../Input/data/dijetTLAnlo/data_J75yStar03_range400_2079.root', help='original data file name')
    parser.add_argument('--histname', dest='histname', type=str, default='data', help='original data hist name')
    parser.add_argument('--sigmean', dest='sigmean', type=float, default=600, help='mean of injected Gaussian')
    parser.add_argument('--sigwidth', dest='sigwidth', type=float, default=5, help='width of injected Gaussian (in %)')
    parser.add_argument('--sigamp', dest='sigamp', type=float, default=5, help='number of injected events (in sigmas of central bin)')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
    parser.add_argument('--firsttoy', dest='firsttoy', type=int, help='Only consider toys larger than this number')
    parser.add_argument('--lasttoy', dest='lasttoy', type=int, help='Only consider toys lower than this number')

    args = parser.parse_args(args)

    if args.outfile == "":
        #args.outfile = os.path.split(args.infile)[-1].replace(".root", "_mean%.0f_width%.0f_amp%.0f.root" % (args.sigmean, args.sigwidth, args.sigamp))
        args.outfile = args.infile.replace(".root", "_mean%.0f_width%.0f_amp%.0f.root" % (args.sigmean, args.sigwidth, args.sigamp)).replace("/run_fivePar/", "/run_fivePar/injected/")
        print(args.outfile)

    InjectGaussian(infile=args.infile,
                   histname=args.histname,
                   sigmean=args.sigmean,
                   sigwidth=args.sigwidth,
                   sigamp=args.sigamp,
                   outfile=args.outfile,
                   firsttoy=args.firsttoy,
                   lasttoy=args.lasttoy)

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
