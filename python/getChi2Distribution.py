#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
import numpy as np

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def ChiSquareDistr(x, par):
    return ROOT.Math.chisquared_pdf(x[0], par[0])

def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infiles', dest='infiles', nargs='+', type=str, required=True, help='Input file names')
    parser.add_argument('--inhist', dest='inhist', type=str, default='chi2', help='Input hist name')
    parser.add_argument('--chi2bin', dest='chi2bin', type=int, default=1, help='Hist bin with chi2')
    parser.add_argument('--pvalbin', dest='pvalbin', type=int, help='Hist bin with pval')
    parser.add_argument('--outfile', dest='outfile', type=str, default='chi2.root', help='Output file name')
    parser.add_argument('--outhist', dest='outhist', type=str, default='chi2', help='Output hist name')
    parser.add_argument('--nofit', dest='nofit', action='store_true', help='Do not fit the chi2 distribution')

    args = parser.parse_args(args)

    chi2 = []
    pval = []
    bins = None

    for path in args.infiles:
        f_in = ROOT.TFile(path, "READ")
        h_in = f_in.Get(args.inhist)

        chi2.append(h_in.GetBinContent(args.chi2bin))
        if not bins:
            bins = h_in.GetBinContent(3)

        if args.pvalbin:
            pval.append(h_in.GetBinContent(args.pvalbin))

        f_in.Close()
        
    # mean = sum(chi2) / len(chi2)
    mean = np.percentile(chi2,50)
    # boundary = np.percentile(chi2,95)
    boundary = 2*mean
    print mean, boundary

    f_out = ROOT.TFile(args.outfile, "RECREATE")
    f_out.cd()

    h_out = ROOT.TH1D("chi2", "chi2;#chi^{2};# toys, normalised", 250, 0, 3*mean)
    h_pval_out = ROOT.TH1D("pval", "pval;#chi^{2} #it{p}-value;# toys, normalised", 100, 0, 1)

    for c in chi2:
        h_out.Fill(c)

    for p in pval:
        h_pval_out.Fill(p)

    h_out.Scale(1./h_out.Integral("width"))
    h_out.Write("chi2")

    if args.pvalbin:
        h_pval_out.Scale(1./h_pval_out.Integral("width"))
        h_pval_out.Write("pval")

    c = ROOT.TCanvas("c1", "c1", 800, 600)
    
    # h_out.GetXaxis().SetRangeUser(1250, 1950)
    h_out.Draw("hist")
    
    if not args.nofit:
        print "Fitting with chi2 distribution"
        f1 = ROOT.TF1("chi-square distribution",ChiSquareDistr,0.,boundary,1);
        f1.SetNpx(2000)
        f1.SetParameter(0,h_out.GetMean())
        
        f1.SetLineColor(ROOT.kRed)
        f1.Draw("same")

        h_out.Fit(f1,"MERN")

        f1.Write("fit")

    print "hist integral:", h_out.Integral("width")
    if not args.nofit:
        print "fct  integral:", f1.Integral(0,2000)

    ROOT.ATLASLabel(0.59, 0.90, "Work in progress", 13)

    text=""
    if "four" in args.infiles[0]:
        text="4-par global fit"
    elif "five" in args.infiles[0]:
        text="5-par global fit"
    elif "nlo" in  args.infiles[0]:
        text="NLOFit"
        if "constrSigma" in args.infiles[0]:
            s=re.findall(r'constrSigma\d+', args.infiles[0])[0]
            s=int(s[11:])
            text="NLOFit, #sigma=%d constraint" % s
        elif "constr" in args.infiles[0]:
            s=re.findall(r'constr\d+', args.infiles[0])[0]
            s=int(s[6:])
            text="NLOFit, #sigma=%d constraint" % s

    ROOT.myText(0.92, 0.84, 1, text, 33)

    l=ROOT.TLegend(0.65,0.66, 0.92, 0.78)
    l.AddEntry(h_out, "%d toys" % len(chi2), "l")
    if not args.nofit:
        ROOT.myText(0.75, 0.57, 1, "ndf:", 33)
        ROOT.myText(0.92, 0.57, 1, "%.1f #pm %.1f" % (f1.GetParameter(0), f1.GetParError(0)), 33)
        l.AddEntry(f1, "#chi^{2} distribution fit", "l")
    l.Draw()

    ROOT.myText(0.75, 0.63, 1, "bins:", 33)
    ROOT.myText(0.92, 0.63, 1, "%d" % bins, 33)

    c.Update()

    c.Print(args.outfile.replace(".root", ".png"))
    c.Print(args.outfile.replace(".root", ".pdf"))

    f_out.Close()


if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not x == "-b"]
   sys.exit(main(args))   
