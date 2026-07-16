#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infiles', dest='infiles', nargs='+', type=str, default='', help='Input file name')
    parser.add_argument('--inhist', dest='inhist', type=str, default='chi2', help='Input hist name')
    parser.add_argument('--chi2bin', dest='histbin', type=int, default=1, help='Bin of chi2')
    parser.add_argument('--ndofbin', dest='ndofbin', type=int, default=5, help='Bin of ndof')
    parser.add_argument('--pvalbin', dest='pvalbin', type=int, default=6, help='Bin of pval')
    parser.add_argument('--outfile', dest='outfile', type=str, default='pvals.root', help='Output file name')

    args = parser.parse_args(args)

    dict_chi2 = {}
    dict_ndof = {}
    dict_pval = {}

    chi2 = []
    bins = None

    for path in args.infiles:
        f_in = ROOT.TFile(path, "READ")
        
        if "constr" in path:
            x=re.findall(r'constr\d+', path)[0]
            x=int(x[6:])
        else:
            print "ERROR: Cannot extract constraint from file name %s" % path
            return 1
        
        h_in = f_in.Get(args.inhist)

        dict_chi2[x] = h_in.GetBinContent(args.histbin)
        dict_ndof[x] = h_in.GetBinContent(args.ndofbin)
        dict_pval[x] = h_in.GetBinContent(args.pvalbin)

        f_in.Close()

    g_chi2 = ROOT.TGraph()
    g_ndof = ROOT.TGraph()
    g_pval = ROOT.TGraph()

    for x in sorted(dict_chi2):
        y=dict_chi2[x]
        g_chi2.SetPoint(g_chi2.GetN(),x,y)

    for x in sorted(dict_ndof):
        y=dict_ndof[x]
        g_ndof.SetPoint(g_ndof.GetN(),x,y)

    c = ROOT.TCanvas("c1", "c1", 800, 600)
    c.SetLogx()
    c.SetRightMargin(0.10)
    c.SetLeftMargin(0.10)
    c.SetTickx(1)
    c.SetTicky(0)

    g_chi2.Draw("APL")
    g_ndof.Draw("PL")

    g_chi2.GetXaxis().SetTitle("NP constraint term")
    g_ndof.SetMarkerStyle(21)

    # Scale g_pval to plot in same canvas
    # rightmax = 1.1*max(dict_pval.values())
    # rightmin = 0.9*min(dict_pval.values())
    rightmin = 1.E-5
    rightmax = 1.
    leftmin = 0.
    leftmax = 90.
    logx = True
    logyright = True

    g_chi2.GetYaxis().SetRangeUser(leftmin,leftmax)

    c.Update()

    if logyright:
        # log:
        scale = (leftmax-leftmin)/(ROOT.TMath.Log10(rightmax)-ROOT.TMath.Log10(rightmin))
        offset = leftmax - scale*ROOT.TMath.Log10(rightmax)
    else:
        # linear:
        scale = (leftmax-leftmin)/(rightmax-rightmin)
        offset = leftmax - scale*rightmax

    g_pval.SetLineColor(ROOT.kRed)
    g_pval.SetMarkerColor(ROOT.kRed)

    for x in sorted(dict_pval):
        if logyright:
            y=ROOT.TMath.Log10(dict_pval[x])*scale + offset
        else:
            y=dict_pval[x]*scale + offset
        g_pval.SetPoint(g_pval.GetN(),x,y)

    c.Update()

    g_pval.Draw("PL")
    
    if logyright:
        axis = ROOT.TGaxis(10**ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin(),
                           10**ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax(),rightmin,rightmax,510,"+LG")
    else:
        axis = ROOT.TGaxis(ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin(),
                           ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax(),0,rightmax,510,"+L")

    axis.SetLineColor(ROOT.kRed)
    axis.SetLabelColor(ROOT.kRed)
    axis.SetLabelSize(ROOT.gStyle.GetLabelSize("y"))
    axis.SetLabelFont(ROOT.gStyle.GetLabelFont("y"))
    axis.SetTitleFont(ROOT.gStyle.GetTitleFont("y"))
    axis.SetTitleSize(ROOT.gStyle.GetTitleSize("y"))
    axis.Draw()
    
    c.Update()

    ROOT.ATLASLabel(0.53, 0.20, "Work in progress", 11)
    ROOT.myText(0.86, 0.26, 1, "NLOFit", 31)
    ROOT.myText(0.86, 0.32, 1, "29.3 fb^{-1}, 2016 J100", 31)

    # l=ROOT.TLegend(0.65, 0.60, 0.88, 0.78)
    l=ROOT.TLegend(0.25, 0.185, 0.40, 0.365)
    l.AddEntry(g_chi2, "#chi^{2}", "lp")
    l.AddEntry(g_ndof, "n.d.f.", "lp")
    l.AddEntry(g_pval, "#chi^{2} #it{p}-value", "lp")
    l.Draw()

    c.Update()

    raw_input("press enter")

    c.Print(args.outfile.replace(".root", ".png"))
    c.Print(args.outfile.replace(".root", ".pdf"))

    f_out = ROOT.TFile(args.outfile, "RECREATE")
    f_out.cd()
    
    g_chi2.Write("g_chi2")
    g_ndof.Write("g_ndof")
    g_pval.Write("g_pval")

    f_out.Close()


if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
