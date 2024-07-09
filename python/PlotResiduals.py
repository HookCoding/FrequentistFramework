#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
from color import getColorSteps, getFillStyle

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

def main(args):
    SetAtlasStyle()
 
    paths = args[0:]

    colors = getColorSteps(len(paths)-1)
    # fillstyles = [3245, 3254, 3295, 3205]
    # fillstyles = [3245, 3245, 3245, 3245, 3245, 3245, 3245]

    do1GeV = False
    
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
                if do1GeV:
                    h_chi2 = f.Get("J100yStar06/chi2")
                else:
                    h_chi2 = f.Get("J100yStar06_rebinned/chi2")
                chi2.append(h_chi2.GetBinContent(1))
                ndof.append(h_chi2.GetBinContent(5))
                pval.append(h_chi2.GetBinContent(6))
            except:
                chi2.append(float("NaN"))
                ndof.append(float("NaN"))
                pval.append(float("NaN"))
        
        # h = TH1D()
        try:
            h = f.GetObject("residuals")
        except:
            try: 
                if do1GeV:
                    h = f.Get("J100yStar06/residuals")
                else:
                    h = f.Get("J100yStar06_rebinned/residuals")
            except:
                # h = TH1F()
                h = f.Get("swiftResiduals_rebinned_resolution")

        h.SetDirectory(0)
        f.Close()
        hists.append(h)

    c = TCanvas("c1", "c1", 800, 600)
    c.SetGridy()

    for i, h in enumerate(hists):
        h.SetFillStyle(getFillStyle(i))
        h.SetLineColor(colors[i])
        h.SetFillColor(colors[i])
        h.SetMarkerColor(colors[i])
        # h.SetMinimum(min(-3.2, h.GetMinimum()))
        # h.SetMaximum(max( 3.2, h.GetMaximum()))
        # h.SetMinimum(min(-4.2, h.GetMinimum()))
        # h.SetMaximum(max( 5.6, h.GetMaximum()))
        h.SetMinimum(-4.2)
        h.SetMaximum( 6.2)
        # h.SetMinimum(-1.5)
        # h.SetMaximum( 1.5)
        h.GetXaxis().SetTitle("m_{jj} [GeV]")
        # h.GetYaxis().SetTitle("Residuals [#sigma]")
        h.GetYaxis().SetTitle("Significance")
        h.SetNdivisions(505)
        if do1GeV:
             h.GetXaxis().SetRangeUser(302,350)
        h.Draw("same hist][")

    leg = TLegend(0.18,0.70,0.90,0.90)
    leg.SetNColumns(2)
    leg.SetTextSize(21)
    leg.SetFillStyle(0)

    for i, p in enumerate(paths[:-1]):
    #     # entry = ""
    #     entry = "NLOFit"
    #     #entry = "#splitline{"
    #     # if "CT14" in p:
    #     #     entry += "CT14"
    #     # if "MMHT" in p:
    #     #     entry += "MMHT14"
    #     # if "ABMP" in p:
    #     #     entry += "ABMP16"
    #     if "fivePar" in p:
    #         entry += "analytic 5-par"
    #     elif "threePar" in p:
    #         entry += "analytic 3-par"
    #     elif "sixPar" in p:
    #         entry += "analytic 6-par"
    #     elif "sevenPar" in p:
    #         entry += "analytic 7-par"
    #     elif "fourPar" in p:
    #         entry += "analytic 4-par"
    #     if "UA2" in p:
    #         entry = entry.replace("analytic","UA2")
    #     if "WHW" in p:
    #         entry += ", WHW:{}".format(p.split("WHW")[1].split("_")[0])
    #     if "reweightedData" in p or "rewData" in p:
    #         entry += ", rew."
    #     if "inflated" in p:
    #         idx = p.find("inflated")
    #         s = p[idx+8:]
    #         s = re.search('\d+', s ).group()
    #         entry += ", %s#sigma" % s
    #     if "constr" in p:
    #         idx = p.find("constr")
    #         s = p[idx+6:]
    #         s = re.search('\d+', s ).group()
    #         entry += ", %s#sigma" % s

    #     if "noConstr" in p:
    #         entry += ", free"

    #     if not "WHW" in p:  # n.d.f in SWiFt?
    #         entry = "#splitline{" + entry + "}{#chi^{2}/n.d.f. = %.1f/%.1f}" % (chi2[i], ndof[i])

    #     entry="#chi^{2}-based fit"

        # if i==0:
        #     # entry="uncorr, #it{p} = %.2f" % pval[i]
        #     entry="p_{T} > 85 GeV, #it{p} = %.2f" % pval[i]
        # elif i==1:
        #     # entry="corr, #it{p} = %.2f" % pval[i]
        #     entry="p_{T} > 75 GeV, #it{p} = %.2f" % pval[i]
        # else:
        #     entry="corr (+%dGeV), #it{p} = %.2f" % (4*(i-1), pval[i])

        if "pileupScale" in p:
            entry="pileup scale, #it{p} = %.3f" % pval[i]
        elif "etaJESScale" in p:
            entry="etaJES scale, #it{p} = %.3f" % pval[i]
        elif "gscScale_Tile0" in p:
            entry="GSC_{Tile0} scale, #it{p} = %.3f" % pval[i]
        elif "gscScale_EM3" in p:
            entry="GSC_{EM3} scale, #it{p} = %.3f" % pval[i]
        elif "gscScale_N90" in p:
            entry="GSC_{N90} scale, #it{p} = %.3f" % pval[i]
        elif "gscScale_TileGap3" in p:
            entry="GSC_{TG3} scale, #it{p} = %.3f" % pval[i]
        elif "gscScale" in p:
            entry="GSC scale, #it{p} = %.3f" % pval[i]
        elif "insituScale" in p:
            entry="insitu scale, #it{p} = %.3f" % pval[i]
        elif "genCorrScale" in p:
            entry="on/off scale, #it{p} = %.3f" % pval[i]
        else:
            entry="344-1516 GeV, #it{p} = %.3f" % pval[i]
            
        # if i==0:
        #     entry="TG3 last, w/ N_{90}, #it{p} = %.2f" % pval[i]
        # if i==1:
        #     entry="TG3 last, w/o N_{90}, #it{p} = %.2f" % pval[i]
        # if i==2:
        #     entry="TG3 first, w/ N_{90}, #it{p} = %.2f" % pval[i]
        # if i==3:
        #     entry="TG3 first, w/o N_{90}, #it{p} = %.2f" % pval[i]

        leg.AddEntry(hists[i], entry, "f")

    # leg.AddEntry(hists[0], "#splitline{NLOFit (20#sigma)}{#splitline{#chi^{2}/n.d.f. = %.1f/%.1f}{#it{p}(#chi^{2}) = %.3f}}" % (chi2[0], ndof[0], pval[0]), "f")
    # leg.AddEntry(hists[1], "#splitline{analytic fit (5-par)}{#splitline{#chi^{2}/n.d.f. = %.1f/%.1f}{#it{p}(#chi^{2}) = %.3f}}" % (chi2[1], ndof[1], pval[1]), "f")

    leg.Draw()

    ATLASLabel(0.60, 0.30, "Work in progress", 13)
    trig = "J100"
    # lumi = "19.6"
    lumi = "133"
    if "J50" in paths[0]:
        trig = "J50"
        lumi = "1.5"

    # text="%s, #sqrt{s}=13 TeV, %s fb^{-1}" % (trig, lumi)
    if "singleJet_data17" in paths[0]:
        text="J50 singleJet data17"
    elif "singleJet_data18" in paths[0]:
        text="J50 singleJet data18"
    elif "DETA20" in paths[0]:
        text="J50_DETA20 data18 (post TS1)"
    elif "merged" in paths[1]:
        text="J50 + J50_DETA20 Run-2"
    else:
        text=""

    myText(0.60, 0.25, 1, text, 13)

    # c.Print("residuals_J100.svg")
    # c.Print("residuals_J100.pdf")
    if not paths[-1].endswith(".root"):
        c.Print(paths[-1])
    else:
        c.Print("residuals_J100.svg")
        c.Print("residuals_J100.pdf")

    # raw_input("Press enter to continue...")


if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not x.startswith("-")]
   sys.exit(main(args))   

