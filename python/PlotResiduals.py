#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
from color import getColorSteps

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def main(args):
    SetAtlasStyle()
 

    paths = args[0:]

    colors = getColorSteps(len(paths))
    # fillstyles = [3245, 3254, 3295, 3205]
    fillstyles = [3245, 3245, 3245, 3245, 3245, 3245, 3245]

    hists = []
    chi2 = []
    pval = []
    ndof = []

    for p in paths[:-1]:
        f = TFile(p)

        try:
            h_chi2 = f.Get("chi2")
            chi2.append(h_chi2.GetBinContent(1))
            ndof.append(h_chi2.GetBinContent(5))
            pval.append(h_chi2.GetBinContent(6))
        except:
            try:
                h_chi2 = f.Get("J100yStar06_rebinned/chi2")
                chi2.append(h_chi2.GetBinContent(1))
                ndof.append(h_chi2.GetBinContent(5))
                pval.append(h_chi2.GetBinContent(6))
            except:
                chi2.append(float("NaN"))
                ndof.append(float("NaN"))
                pval.append(float("NaN"))

	h = TH1D()
	try:
	  f.GetObject("residuals",h)
	except:
	  try: 
	    f.GetObject("J100yStar06/residuals",h)
	  except:
	    h = TH1F()
	    f.GetObject("swiftResiduals_rebinned_resolution",h)

        h.SetDirectory(0)
        f.Close()
        hists.append(h)

    c = TCanvas("c1", "c1", 800, 600)
    c.SetGridy()

    for i, h in enumerate(hists):
        h.SetFillStyle(fillstyles[i])
        h.SetLineColor(colors[i])
        h.SetFillColor(colors[i])
        h.SetMarkerColor(colors[i])
        h.SetMinimum(min(-4.2, h.GetMinimum()))
        h.SetMaximum(max( 5.2, h.GetMaximum()))
	h.GetXaxis().SetTitle("m_{jj} [GeV]")
        h.GetYaxis().SetTitle("Residuals [#sigma]")
        h.SetNdivisions(505)
	h.GetXaxis().SetRangeUser(457,2997)
        h.Draw("same hist")

    leg = TLegend(0.18,0.80,0.90,0.90)
    leg.SetNColumns(2)
    leg.SetTextSize(21)
    leg.SetFillStyle(0)

    for i, p in enumerate(paths[:-1]):
        entry = ""
        #entry = "#splitline{"
        if "CT14" in p:
            entry += "CT14"
        if "MMHT" in p:
            entry += "MMHT14"
        if "ABMP" in p:
            entry += "ABMP16"
        if "fivePar" in p:
            entry += "analytic 5-par"
	elif "threePar" in p:
	    entry += "analytic 3-par"
	else:
	    entry += "analytic 4-par"
	if "UA2" in p:
	    entry = entry.replace("analytic","UA2")
	if "WHW" in p:
	    entry += ", WHW:{}".format(p.split("WHW")[1].split("_")[0])
        if "reweightedData" in p or "rewData" in p:
            entry += ", rew."
        if "inflated" in p:
            idx = p.find("inflated")
            s = p[idx+8:]
            s = re.search('\d+', s ).group()
            entry += ", %s#sigma" % s
        if "constr" in p:
            idx = p.find("constr")
            s = p[idx+6:]
            s = re.search('\d+', s ).group()
            entry += ", %s#sigma" % s

        if "noConstr" in p:
            entry += ", free"

	if not "WHW" in p:  # n.d.f in SWiFt?
	  entry = "#splitline{" + entry + "}{#chi^{2}/n.d.f. = %.1f/%.1f}" % (chi2[i], ndof[i])

        leg.AddEntry(hists[i], entry)

    # leg.AddEntry(hists[0], "#splitline{NLOFit (20#sigma)}{#splitline{#chi^{2}/n.d.f. = %.1f/%.1f}{#it{p}(#chi^{2}) = %.3f}}" % (chi2[0], ndof[0], pval[0]), "f")
    # leg.AddEntry(hists[1], "#splitline{analytic fit (5-par)}{#splitline{#chi^{2}/n.d.f. = %.1f/%.1f}{#it{p}(#chi^{2}) = %.3f}}" % (chi2[1], ndof[1], pval[1]), "f")

    leg.Draw()

    ATLASLabel(0.60, 0.30, "Work in progress", 13)
    myText(0.60, 0.25, 1, "J100, #sqrt{s}=13 TeV, 3.6 fb^{-1}", 13)

    c1.Print("residuals_J100.svg")
    c1.Print("residuals_J100.png")
    c1.Print(paths[-1])
    raw_input("Press enter to continue...")


if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   

