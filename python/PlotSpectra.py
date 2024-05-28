
#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
from color import getColorSteps, getFillStyle
import json

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

doAtlasLabel = False
doLogX = True

def readBHjson(path):
    with open(path) as f:
        BHresults=json.load(f)

        p = BHresults["pyBHresult"]["global_Pval"]

        # locp = BHresults["pyBHresult"]["min_Pval_ar"][0]

        binmin = BHresults["pyBHresult"]["min_loc_ar"][0]
        binmax = BHresults["pyBHresult"]["min_loc_ar"][0] + BHresults["pyBHresult"]["min_width_ar"][0]
        wmin = BHresults["pyBHresult"]["bins"][binmin]
        wmax = BHresults["pyBHresult"]["bins"][binmax]

        # wmin = BHresults["MaskMin"]
        # wmax = BHresults["MaskMax"]

    return(p,wmin,wmax)

def zeroOutsideRange(h, xmin, xmax):
    for i in range(h.GetNbinsX()):
        if h.GetBinCenter(i+1) < xmin or h.GetBinCenter(i+1) > xmax:
            h.SetBinContent(i+1,0)

def zeroOutsideBins(h, xmin, xmax):
    for i in range(h.GetNbinsX()):
        if i+1 < xmin or i+1 > xmax:
            h.SetBinContent(i+1,0)

def main(args):
    SetAtlasStyle()

    gStyle.SetHatchesLineWidth(2)
 
    paths = args[0:]

    # colors = getColorSteps(len(paths))
    colors = [kBlue, kRed]
    # fillstyles = [3245, 3254, 3295, 3205]
    # fillstyles = [3245, 3245, 3245, 3245, 3245, 3245, 3245]

    h_data_unrebinned = []
    h_data = []
    h_fit = []
    h_res = []
    h_bump = []
    chi2 = []
    pval = []
    ndof = []
    pBH = []
    BHmin = []
    BHmax = []

    for p in paths:
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

        try:
            _h_res = f.Get("residuals")
            _h_res.SetDirectory(0)
            _h_data = f.Get("data")
            _h_data.SetDirectory(0)
            _h_fit = f.Get("postfit")
            _h_fit.SetDirectory(0)
        except:
            _h_res = f.Get("J100yStar06_rebinned/residuals")
            _h_res.SetDirectory(0)
            _h_data = f.Get("J100yStar06_rebinned/data")
            _h_data.SetDirectory(0)
            _h_fit = f.Get("J100yStar06_rebinned/postfit")
            _h_fit.SetDirectory(0)

        try:
            _h_data_unrebinned = f.Get("data")
            _h_data_unrebinned.SetDirectory(0)
        except:
            _h_data_unrebinned = f.Get("J100yStar06/data")
            _h_data_unrebinned.SetDirectory(0)

        f.Close()
        h_res.append(_h_res)
        h_data.append(_h_data)
        h_data_unrebinned.append(_h_data)
        h_fit.append(_h_fit)

        bhpath = p.replace("PostFit", "BHResult").replace(".root", ".json")

        try:
            (_pBH,_BHmin,_BHmax) = readBHjson(bhpath)

            pBH.append(_pBH)
            BHmin.append(_BHmin)
            BHmax.append(_BHmax)
        except Exception as e:
            print("Couldn't read BH pval from", bhpath)
            print(e)
            # return -1
            continue

    # xmin = 262
    if doLogX:
        xmin = 323
        xmax = 3069
    else:
        xmin = 282
        xmax = 3450
    ymin = 5e3
    ymax = 5e8

    # xmin_triggers = [344,481]
    # xmax_triggers = [1516,2997]
    xmin_triggers = [481,344]
    xmax_triggers = [2997,1516]

    c = TCanvas("c1", "c1", 800, 800)
    c.cd()
    p1 = TPad("p1", "p1", 0.,0.4,1.,1.)
    p1.SetBottomMargin(0.005)
    p1.SetLogy()
    if doLogX:
        p1.SetLogx()
    p1.Draw()
    p1.cd()

    h_ghostrange = TH1D("h_ghostrange", "h_ghostrange", 1, xmin, xmax)
    h_ghostrange.SetMinimum(ymin)
    h_ghostrange.SetMaximum(ymax)

    h_ghostrange.Draw("hist")
    h_ghostrange.GetYaxis().SetTitle("Events / Bin")

    for i, h in enumerate(h_data):
        h.SetMarkerStyle(20+i)
        h.SetMarkerSize(0.9)
        zeroOutsideRange(h, xmin_triggers[i], xmax_triggers[i])
        h.Draw("p same")

    for i, h in enumerate(h_fit):
        h.SetLineColor(colors[i])
        h.SetMarkerColor(colors[i])
        h.Draw("same hist][")

    c.cd()
    p2 = TPad("p2", "p2", 0.,0.25,1.,0.4)
    p2.SetTopMargin(0.01)
    p2.SetBottomMargin(0.01)
    if doLogX:
        p2.SetLogx()
    p2.Draw()
    p2.cd()

    h_ghostrange1=h_ghostrange.Clone()
    h_ghostrange1.SetLineWidth(1)
    h_ghostrange1.GetYaxis().SetTickLength(0.029)
    
    h_ghostrange1.Draw("hist")
    h_ghostrange1.SetMinimum(-3.49)
    h_ghostrange1.SetMaximum(3.49)
    # h_ghostrange1.SetMinimum(-2.99)
    # h_ghostrange1.SetMaximum(2.99)
    for v in [-3, -1, 1, 3]:
        h_ghostrange1.GetYaxis().ChangeLabelByValue(v,-1,-1,-1,-1,-1," ")
    h_ghostrange1.GetYaxis().SetTitle("")

    h_res[0].SetLineColor(colors[0])
    h_res[0].SetLineWidth(2)
    h_res[0].SetFillColor(colors[0])
    h_res[0].SetFillStyle(getFillStyle(0))
    # h_res[0].GetXaxis().SetRangeUser(xmin, xmax)
    # h_res[0].GetXaxis().SetLimits(xmin, xmax)
    h_res[0].Draw("same hist")

    h_bump.append(h_res[0].Clone())
    print("Identified bins:", BHmin[0], BHmax[0])
    # win_min = h_data_unrebinned[0].GetBinLowEdge(round(BHmin[0]))
    # win_max = h_data_unrebinned[0].GetBinLowEdge(round(BHmax[0]))
    # zeroOutsideRange(h_bump[-1], win_min, win_max)
    zeroOutsideRange(h_bump[-1], BHmin[0], BHmax[0])
    h_bump[-1].SetFillStyle(1001)
    # print("Identified window:", win_min, win_max)
    h_bump[-1].Draw("same hist][")
    

    c.cd()
    p3 = TPad("p3", "p3", 0.,0.0,1.,0.25)
    p3.SetTopMargin(0.01)
    p3.SetBottomMargin(0.4)
    if doLogX:
        p3.SetLogx()
    p3.Draw()
    p3.cd()
    
    h_ghostrange2=h_ghostrange1.Clone()
    h_ghostrange2.Draw("hist")
    h_ghostrange2.GetXaxis().SetTitle("m_{jj} [GeV]")
    # h_ghostrange2.GetYaxis().SetTitle("Significance")
    if doLogX:
        h_ghostrange2.GetXaxis().SetTitleOffset(1.2)
        h_ghostrange2.GetXaxis().SetMoreLogLabels()
        h_ghostrange2.GetXaxis().SetNoExponent()
    else:
        h_ghostrange2.GetXaxis().SetTitleOffset(5)
    h_ghostrange2.GetYaxis().SetTickLength(0.048)

    h_res[1].SetLineColor(colors[1])
    h_res[1].SetLineWidth(2)
    h_res[1].SetFillColor(colors[1])
    h_res[1].SetFillStyle(getFillStyle(1))
    # h_res[1].GetXaxis().SetRangeUser(xmin, xmax)
    # h_res[1].GetXaxis().SetLimits(xmin, xmax)
    h_res[1].Draw("same hist")

    h_bump.append(h_res[1].Clone())
    print("Identified bins:", BHmin[1], BHmax[1])
    # win_min = h_data_unrebinned[1].GetBinLowEdge(round(BHmin[1]))
    # win_max = h_data_unrebinned[1].GetBinLowEdge(round(BHmax[1]))
    # zeroOutsideRange(h_bump[-1], win_min, win_max)
    zeroOutsideRange(h_bump[-1], BHmin[1], BHmax[1])
    h_bump[-1].SetFillStyle(1001)
    # print("Identified window:", win_min, win_max)
    h_bump[-1].Draw("same hist][")

    p1.cd()
    
    if doAtlasLabel:
        ATLASLabel(0.58, 0.90, "Work in progress", 13)
        leg1 = TLegend(0.65,0.65,0.90,0.80)
    else:
        leg1 = TLegend(0.65,0.65,0.90,0.90)

    leg1.SetTextSize(21)
    # leg1.AddEntry(h_data[0], "J100 Pseudodata, 133 fb^{-1}")
    leg1.AddEntry(h_data[0], "Data, 132 fb^{-1}", "p")
    if "nlofit" in paths[0].lower():
        leg1.AddEntry(h_fit[0], "NLOFit", "l")
    else:
        leg1.AddEntry(h_fit[0], "Functional form fit", "l")
    leg1.AddEntry(0,"p(#chi^{2}) = %.2f" % pval[0], "")
    leg1.AddEntry(0,"p(BH) = %.2f" % pBH[0], "")
    leg1.Draw()

    # leg2 = TLegend(0.2,0.05,0.45,0.2)
    leg2 = TLegend(0.2,0.05,0.45,0.3)
    leg2.SetTextSize(21)
    # leg2.AddEntry(h_data[1], "J50 Pseudodata, 15.0 fb^{-1}")
    leg2.AddEntry(h_data[1], "Data, 15.0 fb^{-1}", "p")
    if "nlofit" in paths[1].lower():
        leg2.AddEntry(h_fit[1], "NLOFit", "l")
    else:
        leg2.AddEntry(h_fit[1], "Functional form fit", "l")
    leg2.AddEntry(0,"p(#chi^{2}) = %.2f" % pval[1], "")
    leg2.AddEntry(0,"p(BH) = %.2f" % pBH[1], "")
    leg2.Draw()
    
    c.cd()
    p4 = TPad("p4", "p4", 0.,0.,0.11,0.4)
    p4.SetTopMargin(0.)
    p4.SetBottomMargin(0.)
    p4.SetLeftMargin(0.)
    p4.SetRightMargin(0.)
    p4.Draw()
    p4.cd()

    # myText(0.60, 0.45, 1, "J100 Pseudodata, 133 fb^{-1}", 13)
    p4.cd()
    l=TLatex()
    l.SetTextAlign(13)
    l.SetNDC()
    l.SetTextColor(kBlack)
    l.SetTextAngle(90)
    l.DrawLatex(0.7,0.42,"Significance")

    c.Print("spectra_PD.svg")
    c.Print("spectra_PD.pdf")
    # raw_input("Press enter to continue...")


if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   

