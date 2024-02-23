#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse, array

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

    opacity = 10./len(args.toyfiles)

    paths=args.toyfiles

    if paths[0].endswith(".txt"):
        print("Assuming file list input.")
        filelists = paths
        paths = []
        for fl in filelists:
            with open(fl, 'r') as f:
                paths += f.read().splitlines()

    print("Reading toy files")
    for path in paths:
        f_in = ROOT.TFile(path, "READ")
        h1 = f_in.Get(args.toyhist)
        h1.SetDirectory(0)
        h_toys.append(h1)
        f_in.Close()

    f_in = ROOT.TFile(args.reffile, "READ")
    h_ref = f_in.Get(args.refhist)
    h_ref.SetDirectory(0)
    f_in.Close()

    # rebin ref to toys:
    binEdges = []
    nBins = h_toys[0].GetNbinsX()
    for i in range(1, nBins+2):
        binEdges.append(h_toys[0].GetBinLowEdge(i))
    oldLow = h_ref.GetBinLowEdge(1)
    oldHigh = h_ref.GetBinLowEdge(h_ref.GetNbinsX()+2)
    _binEdges = [x for x in binEdges if (x >= oldLow and x <= oldHigh)]
    h_ref = h_ref.Rebin(len(_binEdges)-1, h_ref.GetName(), array.array('d', _binEdges))

    h_ratios = []
    h_pulls = []

    print("Building ratios")
    for h in h_toys:
        h_ratio = h.Clone()
        h_ratio.Divide(h_ref)
        h_ratios.append(h_ratio)

    h_sigmas = {}
    
    for i in [-3,-2,-1,1,2,3]:
        h_sigmas[i] = h_ref.Clone()
        
        for j in range(1,h_ref.GetNbinsX()+2):
            try:
                h_sigmas[i].SetBinContent(j, 1+i/math.sqrt(h_ref.GetBinContent(j)))
            except:
                h_sigmas[i].SetBinContent(j, 0.)

    for h in h_toys:
        h_pull = h.Clone()
        
        for i in range(1, h.GetNbinsX()+1):
            pull = (h.GetBinContent(i) - h_ref.GetBinContent(i)) / math.sqrt(h_ref.GetBinContent(i))
            h_pull.SetBinContent(i, pull)
            
        h_pulls.append(h_pull)


    print("Plotting")
    c = ROOT.TCanvas("c1", "c1", 800, 800)

    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
    pad1.SetBottomMargin(0.015) #Upper and lower plot are joined
    pad1.Draw()
    
    pad1.cd()

    # c.SetLogx()
    # xmin=457
    xmin=481
    xmax=2000
    # text1="29.5 fb^{-1} J100 Pseudodata"
    text1="132 fb^{-1} J100 Pseudodata"

    if "J50" in paths[0]:
        xmin=302
        xmax=1000
        text1="15.0 fb^{-1} J50 Pseudodata"

    # text2 = "bkg-component of "
    text2 = ""

    if "fourPar" in paths[0]:
        text2 += "4-par"
    elif "fivePar" in paths[0]:
        text2 += "5-par"
    elif "sixPar" in paths[0]:
        text2 += "6-par"
    elif "sevenPar" in paths[0]:
        text2 += "7-par"
    elif "eightPar" in paths[0]:
        text2 += "8-par"
    # text2 += " s+b fit"
    text2 += " fit"
    
    searchstring =r'mean(\d+)_width(\d+)(:?_amp\d+)?'
    res=re.search(searchstring, paths[0])
    m=int(res.group(1))
    w=int(res.group(2))
    try:
        a=int(res.group(3)[4:])
    except:
        a=0

    if a>0:
        text3="%d#sigma %d%% signal injected at %d GeV" % (a, w, m)
    else:
        text3="no signal injected"
        

    for i,h in enumerate(h_ratios):
        h.SetLineColorAlpha(ROOT.kRed, opacity)
        # h.SetMinimum(0.9948)
        # h.SetMaximum(1.0052)
        h.SetMinimum(0.989)
        h.SetMaximum(1.011)
        h.GetXaxis().SetRangeUser(xmin, xmax)
        h.GetXaxis().SetTitle("m_{jj} [GeV]")
        h.GetYaxis().SetTitle("#frac{toy}{reference}")

        h.GetYaxis().SetTitleOffset(1.8)
        h.GetXaxis().SetTitleOffset(2)
        h.GetXaxis().SetLabelOffset(2)

        # h.Draw("same hist][")
        h.Draw("same hist l")

        if i==0:
            line = ROOT.TLine(xmin, 1., xmax, 1.)
            line.SetLineWidth(2)
            line.SetLineStyle(7)
            line.SetLineColor(ROOT.kGray+1)
            line.Draw()

    for key in h_sigmas:
        h = h_sigmas[key]
        h.SetLineColorAlpha(ROOT.kGray+3-abs(key), 1)
        h.Draw("same hist")

    h_clone = h_ratios[0].Clone()
    h_clone.SetLineColorAlpha(ROOT.kRed, 1)
    
        
    legend = ROOT.TLegend(0.2,0.66,0.45,0.9)
    legend.AddEntry(h_clone, "toy fits", "l")
    legend.AddEntry(h_sigmas[1], "#pm1#sigma stat. unc.", "l")
    legend.AddEntry(h_sigmas[2], "#pm2#sigma stat. unc.", "l")
    legend.AddEntry(h_sigmas[3], "#pm3#sigma stat. unc.", "l")
    legend.Draw()

    ROOT.ATLASLabel(0.20, 0.05, "Work in progress", 11)
    ROOT.myText(0.20, 0.12, 1, text1, 11)
    ROOT.myText(0.20, 0.18, 1, text3, 11)
    ROOT.myText(0.20, 0.24, 1, text2, 11)

    c.Update()

    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.3);
    pad2.SetTopMargin(0.01);
    pad2.SetBottomMargin(0.30)
    pad2.Draw()
    
    pad2.cd()

    for i,h in enumerate(h_pulls):
        h.SetLineColorAlpha(ROOT.kRed, opacity)
        h.SetMinimum(-2.9)
        h.SetMaximum(2.9)
        # h.SetMinimum(-0.99)
        # h.SetMaximum(3.49)
        h.GetXaxis().SetRangeUser(xmin, xmax)
        h.GetXaxis().SetTitle("m_{jj} [GeV]")
        h.GetYaxis().SetTitle("#frac{toy - reference}{stat. unc.}")
        # h.Draw("same hist][")

        h.GetYaxis().SetTitleOffset(1.8)
        h.GetXaxis().SetTitleOffset(3.5)

        h.Draw("same hist l")
        
        if i==0:
            line2 = ROOT.TLine(xmin, 0., xmax, 0.)
            line2.SetLineWidth(2)
            line2.SetLineStyle(7)
            line2.SetLineColor(ROOT.kGray+1)
            line2.Draw()

    c.Print(args.outfile.replace(".pdf", ".svg"))
    c.Print(args.outfile)

    fout = ROOT.TFile(args.outfile.replace(".pdf", ".root"), "RECREATE")
    fout.cd()

    for i,h in enumerate(h_ratios):
        h.Write("h_ratio_%d" % i)
        

    for i in h_sigmas:
        h_sigmas[i].Write("h_sigma_%d" % i)
    
    fout.Close()

    # raw_input("press enter")

if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
