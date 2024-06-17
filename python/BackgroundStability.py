#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

# for -b flag in ROOT 6.26:
# ROOT.PyConfig.IgnoreCommandLineOptions = False

def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--toyfiles', dest='toyfiles', nargs='+', type=str, default='', help='Input file name(s)')
    parser.add_argument('--toyhist', dest='toyhist', type=str, default='', help='Input hist name')
    parser.add_argument('--reffile', dest='reffile', type=str, default='', help='Reference file name')
    parser.add_argument('--refhist', dest='refhist', type=str, default='', help='ReferenceInput hist name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='backgroundStability.pdf', help='Output file name')

    args = parser.parse_args(args)

    h_toys = []
    h_ref = None

    for path in args.toyfiles:
        f_in = ROOT.TFile(path, "READ")
        h1 = f_in.Get(args.toyhist)
        h1.SetDirectory(0)
        h_toys.append(h1)
        f_in.Close()

    f_in = ROOT.TFile(args.reffile, "READ")
    h_ref = f_in.Get(args.refhist)
    h_ref.SetDirectory(0)
    f_in.Close()

    h_ratios = []

    for h in h_toys:
        h_ratio = h.Clone()
        h_ratio.Divide(h_ref)
        h_ratios.append(h_ratio)

    h_sigmas = {}
    
    for i in [-3,-2,-1,1,2,3]:
        h_sigmas[i] = h_ref.Clone()
        
        for j in range(h_ref.GetNbinsX()):
            try:
                h_sigmas[i].SetBinContent(j, 1+i/math.sqrt(h_ref.GetBinContent(j)))
            except:
                h_sigmas[i].SetBinContent(j, 0.)

    c = ROOT.TCanvas("c1", "c1", 800, 600)
    # c.SetLogx()

    for h in h_ratios:
        h.SetLineColorAlpha(ROOT.kRed, 0.1)
        h.SetMinimum(0.997)
        h.SetMaximum(1.003)
        h.GetXaxis().SetRangeUser(500, 2000)
        h.GetXaxis().SetTitle("m_{jj} [GeV]")
        h.GetYaxis().SetTitle("Fit Ratio")
        h.Draw("same hist][")

    for key in h_sigmas:
        h = h_sigmas[key]
        h.SetLineColorAlpha(ROOT.kGray+3-abs(key), 1)
        h.Draw("same hist][")
    

    ROOT.ATLASLabel(0.57, 0.89, "Work in progress", 11)

    c.Update()

    c.Print(args.outfile.replace(".pdf", ".svg"))
    c.Print(args.outfile)

    # raw_input("press enter")

if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
