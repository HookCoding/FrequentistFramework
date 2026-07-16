#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
import array

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
    parser.add_argument('--inhist', dest='inhist', type=str, help='Input history name')
    parser.add_argument('--templatefile', dest='templatefile', type=str, default='', help='File with template hist')
    parser.add_argument('--templatehist', dest='templatehist', type=str, default='', help='Name of template hist')
    parser.add_argument('--outfile', dest='outfile', type=str, default='rebinned.root', help='Output file name')
    
    args = parser.parse_args(args)

    f_temp = ROOT.TFile(args.templatefile, "READ")
    h_temp = f_temp.Get(args.templatehist)
    h_temp.SetDirectory(0)

    binEdges = []
    nBins = h_temp.GetNbinsX()
    for i in range(1, nBins+2):
        binEdges.append(h_temp.GetBinLowEdge(i))
    f_temp.Close()

    print "Rebinning to %d bins:\n" % nBins, binEdges

    f_in = ROOT.TFile(args.infile, "READ")
    f_out = ROOT.TFile(args.outfile, "RECREATE")
    f_out.cd()

    for histKey in f_in.GetListOfKeys():
        histName = histKey.GetName()
        hist = f_in.Get(histName).Clone()
        
        if args.inhist and args.inhist != histName:
            continue

        if not isinstance(hist, ROOT.TH1):
            continue
            
        oldLow = hist.GetBinLowEdge(1)
        oldHigh = hist.GetBinLowEdge(hist.GetNbinsX()+1)
        tmp_binEdges = [x for x in binEdges if (x >= oldLow and x <= oldHigh)]

        tmp_newHist = hist.Rebin(len(tmp_binEdges)-1, histName, array.array('d', tmp_binEdges))
        name = tmp_newHist.GetName()

        if tmp_binEdges != binEdges:
            newHist = ROOT.TH1D(name+"_padded", tmp_newHist.GetTitle(), len(binEdges)-1, array.array('d', binEdges))

            for i in range(1, newHist.GetNbinsX()+1):
                if binEdges[i-1] in tmp_binEdges:
                    oldBin = tmp_newHist.FindBin(newHist.GetBinCenter(i))
                    binc = tmp_newHist.GetBinContent(oldBin)
                    bine = tmp_newHist.GetBinError(oldBin)
                else:
                    binc = 0.
                    bine = 0.

                newHist.SetBinContent(i, binc)
                newHist.SetBinError(i, bine)
        else:
            newHist = tmp_newHist
            
        newHist.Write(name)

    f_out.Close()
    f_in.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
