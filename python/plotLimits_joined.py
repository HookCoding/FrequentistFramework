#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from math import isnan
from glob import glob
from color import getColorSteps, getMarkerStyle
import ctypes

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

###########
# Gaussian:
###########
# paths = ["/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_noGSC_spur0.5_allSyst_additive_20240213/anaFit_gauss_syst_J50_fivePar/output.*/run/Limits_*_mean${MEAN}_width${WIDTH}.root", 
#          "/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_noGSC_spur0.5_allSyst_additive_20240213/anaFit_gauss_syst_J100_fivePar/output.*/run/Limits_*_mean${MEAN}_width${WIDTH}.root",
# ]
# paths = ["/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_noGSC_spur0.5_allSyst_additive_20240419/anaFit_gauss_syst_J50_fivePar/output.*/run/Limits_*_mean${MEAN}_width${WIDTH}.root", 
#          "/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_noGSC_spur0.5_allSyst_additive_20240419/anaFit_gauss_syst_J100_fivePar/output.*/run/Limits_*_mean${MEAN}_width${WIDTH}.root",
# ]
paths = [
    "/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_calibMay2024_noGSC_SpurOld_systOld_noMask_20240607/anaFit_gauss_J50_fivePar_genCorrScale/output.28953.0/run/Limits_*_mean${MEAN}_width-999_amp0.root",
    "/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_calibMay2024_noGSC_SpurOld_systOld_noMask_20240607/anaFit_gauss_J100_sixPar_genCorrScale/output.28953.0/run/Limits_*_mean${MEAN}_width-999_amp0.root",

###########
# Zprime:
###########
# paths = [
#     "/data/field02/users/bartels/FarmOutput/TLA/Fitting/anaFit_fullRun2_zprime_obsLimit_sbFit_allSyst_noGSC_theo0p1_20240310/anaFit_zprime_obsLimit_J50_fivePar/output.*/run/Limits_*_mean${MEAN}_width-999_amp0.root",
#     "/data/field02/users/bartels/FarmOutput/TLA/Fitting/anaFit_fullRun2_zprime_obsLimit_sbFit_allSyst_noGSC_theo0p1_20240310/anaFit_zprime_obsLimit_J100_fivePar/output.*/run/Limits_*_mean${MEAN}_width-999_amp0.root",
# ]
# paths = [
#     "/data/field02/users/bartels/FarmOutput/TLA/Fitting/anaFit_fullRun2_zprime_obsLimit_sbFit_allSyst_noN90_theo0p1_20240310/anaFit_zprime_obsLimit_J50_fivePar/output.*/run/Limits_*_mean${MEAN}_width-999_amp0.root",
#     "/data/field02/users/bartels/FarmOutput/TLA/Fitting/anaFit_fullRun2_zprime_obsLimit_sbFit_allSyst_noN90_theo0p1_20240310/anaFit_zprime_obsLimit_J100_fivePar/output.*/run/Limits_*_mean${MEAN}_width-999_amp0.root",
# ]
# paths = [
#     "/data/field02/users/bartels/FarmOutput/TLA/Fitting/anaFit_fullRun2_zprime_obsLimit_sbFit_allSyst_noGSC_theoMCFM_20240427/anaFit_zprime_obsLimit_J50_fivePar/output.*/run/Limits_*_mean${MEAN}_width-999_amp0.root",
#     "/data/field02/users/bartels/FarmOutput/TLA/Fitting/anaFit_fullRun2_zprime_obsLimit_sbFit_allSyst_noGSC_theoMCFM_20240427/anaFit_zprime_obsLimit_J100_fivePar/output.*/run/Limits_*_mean${MEAN}_width-999_amp0.root",
# ]


path_offline_gauss = ["limits_HEPData/HEPData-ins1759712-v1-Table_15.root"]
graph_offline_gauss = [
    "Table 15/Graph1D_y4", # 5% observed
    # "Table 15/Graph1D_y6", # 10% observed
    # "Table 15/Graph1D_y7", # 15% observed
]

path_offline_gq = ["limits_HEPData/HEPData-ins1759712-v1-Table_10.root"]
graph_offline_gq = [
    "Table 10/Graph1D_y2", # expected
    "Table 10/Graph1D_y1", # observed
]

path_tla_gauss = ["limits_HEPData/HEPData-ins1667040-v1-root.root"]
graph_tla_gauss = [
    "Table 4/Graph1D_y2", # 5% expected J75
    "Table 6/Graph1D_y2", # 5% expected J100
    "Table 3/Graph1D_y2", # 5% observed J75
    "Table 5/Graph1D_y2", # 5% observed J100
]

path_tla_gq = ["limits_HEPData/limits_TLA_g_q.root"]
graph_tla_gq = [
    "g_exp_J75",
    "g_exp_J100",
    "g_obs_J75", 
    "g_obs_J100",
]

path_acceptance = ["acceptance_noGSC/acceptance_and_crosssection_zprime.root",
                   "acceptance_noGSC/acceptance_and_crosssection_zprime.root"]
graph_acceptance = ["g_xsec_times_acc_mjj344",
                    "g_xsec_times_acc_mjj481"]
# graph_acceptance = ["g_xsec_times_acc_mjj0",
#                     "g_xsec_times_acc_mjj0"]

sigmeans  = [ [ 375, 400, 425, 450, 475, 500, 525, 550 ], 
              # [ 550, 575, 600, 625, 650, 675, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, ] ]
              [ 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, ] ]

# sigmeans  = [ list(range(375,551,5)), list(range(550,1801,10)) ]


# lumis = [ 1500, 29500 ]
# lumis_target = [ 14500, 133000 ]

lumis = [ 15000, 132000 ]
lumis_target = lumis

drawObserved = True

doLogX = False
doATLAS = True
doOffline = False
doTLA = False
isZprime = ("zprime" in paths[0].lower())

if isZprime:
    sigwidths = [ [ -999 ], 
                  [ -999 ] ]
else:
    if doOffline or doTLA:
        sigwidths = [ [ 5 ], 
                      [ 5 ] ]
    else:
        sigwidths = [ [ 5, 10, 15 ], 
                      [ 5, 10, 15 ] ]

legentries = len(sigwidths[0]) + doOffline + doTLA # True=1

def xToNDC(x):
    gPad.Update()
    lm = gPad.GetLeftMargin()
    rm = 1.-gPad.GetRightMargin()
    xndc = (rm-lm)*((gPad.XtoPad(x)-gPad.GetUxmin())/(gPad.GetUxmax()-gPad.GetUxmin()))+lm
    return xndc

def xToNDCLog(x):
    gPad.Update()
    return gPad.XtoPad(x)

def yToNDC(y):
    gPad.Update()
    tm = 1.-gPad.GetTopMargin()
    bm = gPad.GetBottomMargin()
    yndc = (tm-bm)*((gPad.YtoPad(y)-gPad.GetUymin())/(gPad.GetUymax()-gPad.GetUymin()))+bm
    return yndc

def createFillBetweenGraphs(g1, g2):
  g_fill = TGraph()
  
  for i in range(g1.GetN()):
      x=ctypes.c_double()
      y=ctypes.c_double()
    
      g1.GetPoint(i, x, y)
    
      x=x.value
      y=y.value

      g_fill.SetPoint(g_fill.GetN(), x, y)

  for i in range(g2.GetN()-1, -1, -1):
      x=ctypes.c_double()
      y=ctypes.c_double()
    
      g2.GetPoint(i, x, y)

      x=x.value
      y=y.value
    
      g_fill.SetPoint(g_fill.GetN(), x, y)

  return g_fill


def main(args):
    SetAtlasStyle()
 
    colors = [kBlue, kOrange-3, kRed+1]
    # colors = getColorSteps(len(sigwidths[0]))

    g_obs_datasets = []
    g_exp_datasets = []
    g_exp1_datasets = []
    g_exp2_datasets = []
    g_exp1u_datasets = []
    g_exp2u_datasets = []
    g_exp1d_datasets = []
    g_exp2d_datasets = []

    if isZprime:
        g_acc = []
        for i,p in enumerate(path_acceptance):
            f = TFile(p)
            g_acc.append(f.Get(graph_acceptance[i]))
            # g_acc[-1].SetDirectory(0)
            f.Close()

    for dataset in range(len(paths)):

        g_obs = []
        g_exp = []
        g_exp1 = []
        g_exp2 = []
        g_exp1u = []
        g_exp2u = []
        g_exp1d = []
        g_exp2d = []
      
        for i,sigwidth in enumerate(sigwidths[dataset]):
    
            g_obs.append( TGraph() )
            g_exp.append( TGraph() )
            g_exp1u.append( TGraph() )
            g_exp2u.append( TGraph() )
            g_exp1d.append( TGraph() )
            g_exp2d.append( TGraph() )
            
            for j,sigmean in enumerate(sigmeans[dataset]):
                
                tmp_path = paths[dataset]
                tmp_path = tmp_path.replace("${MEAN}", str(sigmean))
                tmp_path = tmp_path.replace("${WIDTH}", str(sigwidth))
                try:
                    tmp_path = glob(tmp_path)[0]
                except:
                    print("WARNING: Skipping (%d,%d) because of missing path" % (sigmean, sigwidth))
                    print("WARNING: No file %s" % tmp_path)
                    continue

                f = TFile(tmp_path, "READ")
                if f.IsZombie():
                    print("WARNING: Skipping (%d,%d) because of zombie file" % (sigmean, sigwidth))
                    print("WARNING: Zombie file %s" % tmp_path)
                    continue
                h = f.Get("limit")
                
                # scalefactor = 1. / lumis[dataset] / sqrt(lumis_target[dataset] / lumis[dataset])
                scalefactor = 1. / lumis[dataset]
                if isZprime:
                    scalefactor = scalefactor / g_acc[dataset].Eval(sigmean)
                            
                obs = h.GetBinContent(h.GetXaxis().FindBin("Observed")) * scalefactor
                exp = h.GetBinContent(h.GetXaxis().FindBin("Expected")) * scalefactor
                exp1u = h.GetBinContent(h.GetXaxis().FindBin("+1sigma")) * scalefactor
                exp2u = h.GetBinContent(h.GetXaxis().FindBin("+2sigma")) * scalefactor
                exp1d = h.GetBinContent(h.GetXaxis().FindBin("-1sigma")) * scalefactor
                exp2d = h.GetBinContent(h.GetXaxis().FindBin("-2sigma")) * scalefactor

                if isZprime:
                    obs = 0.1*sqrt(obs)
                    exp = 0.1*sqrt(exp)
                    exp1u = 0.1*sqrt(exp1u)
                    exp2u = 0.1*sqrt(exp2u)
                    exp1d = 0.1*sqrt(exp1d)
                    exp2d = 0.1*sqrt(exp2d)

                # print dataset, "{0:4.0f} GeV, {1:2.0f}%".format(sigmean, sigwidth), 'exp: {0:6.0f} +1sigma: {1:6.0f} +2sigma: {2:6.0f}'.format(exp*lumis[dataset], exp1u*lumis[dataset], exp2u*lumis[dataset])

                g_exp[i].SetPoint(g_exp[i].GetN(), sigmean, exp)
                g_exp1u[i].SetPoint(g_exp1u[i].GetN(), sigmean, exp1u)
                g_exp2u[i].SetPoint(g_exp2u[i].GetN(), sigmean, exp2u)
                g_exp1d[i].SetPoint(g_exp1d[i].GetN(), sigmean, exp1d)
                g_exp2d[i].SetPoint(g_exp2d[i].GetN(), sigmean, exp2d)

                if isnan(obs):
                    continue
                
                g_obs[i].SetPoint(g_obs[i].GetN(), sigmean, obs)

    
            g_exp1.append( createFillBetweenGraphs(g_exp1d[-1], g_exp1u[-1]) )
            g_exp2.append( createFillBetweenGraphs(g_exp2d[-1], g_exp2u[-1]) )
    
            # g_exp1[-1].SetFillColorAlpha(colors[i], 0.2)
            # g_exp2[-1].SetFillColorAlpha(colors[i], 0.2)
            g_exp1[-1].SetFillColor(colors[i]-9)
            g_exp2[-1].SetFillColor(colors[i]-10)
            g_exp[-1].SetLineColor(colors[i])
            g_exp[-1].SetLineStyle(2)
            g_exp[-1].SetLineWidth(2)
            g_obs[-1].SetLineWidth(2)
            g_obs[-1].SetLineColor(colors[i])
            g_obs[-1].SetMarkerColor(colors[i])
            g_obs[-1].SetMarkerStyle(getMarkerStyle(i))
    
        g_obs_datasets.append(g_obs)
        g_exp_datasets.append(g_exp)
        g_exp1_datasets.append(g_exp1)
        g_exp2_datasets.append(g_exp2)
        g_exp1u_datasets.append(g_exp1u)
        g_exp2u_datasets.append(g_exp2u)
        g_exp1d_datasets.append(g_exp1d)
        g_exp2d_datasets.append(g_exp2d)


    c = TCanvas("c1", "c1", 800, 600)
    if not isZprime:
        c.SetLogy()
    
    if doLogX:
        c.SetLogx()

    leg_xmin = 0.48
    leg_xmax = leg_xmin + 0.23
    leg_ymax = 0.78
    leg_ymin = leg_ymax - 0.06*legentries

    leg_obs = TLegend(leg_xmin+0.057,leg_ymin,leg_xmax+0.057,leg_ymax)
    if drawObserved:
        leg_exp = TLegend(leg_xmin-0.005,leg_ymin,leg_xmax-0.005,leg_ymax)
    else:
        leg_exp = TLegend(leg_xmin-0.005,leg_ymin,leg_xmax-0.005,leg_ymax)
    leg_exp.SetFillStyle(0)
    leg_obs.SetFillStyle(1001)
    leg_obs.SetFillColor(kWhite)

    # minY = 0.02
    # maxY = 500
    minY = 0.01
    maxY = 300
    if doATLAS:
        maxY = 1000

    if isZprime:
        minY = 0.02
        maxY = 0.20
        if doATLAS:
            maxY = 0.25
        
    g_exp_datasets[0][0].Draw("af")
    if isZprime:
        g_exp_datasets[0][0].GetXaxis().SetTitle("m_{Z'} [GeV]")
        g_exp_datasets[0][0].GetYaxis().SetTitle("g_{q}")
    else:
        g_exp_datasets[0][0].GetXaxis().SetTitle("m_{G} [GeV]")
        g_exp_datasets[0][0].GetYaxis().SetTitle("#sigma #upoint #it{A} #upoint #it{BR} [pb]")
    g_exp_datasets[0][0].GetYaxis().SetTitleOffset(1.6)
    g_exp_datasets[0][0].GetHistogram().SetMinimum(minY)
    g_exp_datasets[0][0].GetHistogram().SetMaximum(maxY)
    # g_exp_datasets[0][0].GetXaxis().SetLimits(min(sigmeans[0])-49.9, max(sigmeans[-1])+49.9)
    if doLogX:
        g_exp_datasets[0][0].GetXaxis().SetLimits(350,2000)
        g_exp_datasets[0][0].GetXaxis().SetMoreLogLabels()
        g_exp_datasets[0][0].GetXaxis().SetNoExponent()
    else:
        if isZprime:
            g_exp_datasets[0][0].GetXaxis().SetLimits(275,1850)
        else:
            g_exp_datasets[0][0].GetXaxis().SetLimits(min(sigmeans[0])-99.9, max(sigmeans[-1])+49.9)

    c.Modified()

    for dataset in range(len(paths)):

        g_exp2_datasets[dataset][0].Draw("f")
        g_exp1_datasets[dataset][0].Draw("f")

        for i,g in enumerate(g_exp_datasets[dataset]):
            g.Draw("l")
            if (dataset==0):
                # leg_exp.AddEntry(g, "#sigma_{G}/m_{G} = %.2f" % (sigwidths[dataset][i]/100.), "l")
                leg_exp.AddEntry(g, "", "l")

        for i,g in enumerate(g_obs_datasets[dataset]):
            if (dataset==0):
                legentry = " #sigma_{G}/m_{G} = %.2f" % (sigwidths[dataset][i]/100.)
                if isZprime:
                    legentry = "  Leptophobic Z'"
                if doOffline or doTLA:
                    legentry = "  This work"
                if i == 0:
                    legentry += " (#pm 1-2#sigma)"
                # leg_obs.AddEntry(g, legentry, "l")
                leg_obs.AddEntry(g, legentry, "lp")

        if dataset > 0:
            l=TLine()
            l.SetLineStyle(2)
            # l.DrawLineNDC(xToNDC(sigmeans[dataset][0]), gPad.GetBottomMargin(), xToNDC(sigmeans[dataset][0]), 0.77)
            l.DrawLineNDC(xToNDC(sigmeans[dataset][0]), gPad.GetBottomMargin(), xToNDC(sigmeans[dataset][0]), 0.84)


    if doOffline:
        if isZprime:
            f_off = TFile(path_offline_gq[0])
            g_off_exp = f_off.Get(graph_offline_gq[0])
            g_off_obs = f_off.Get(graph_offline_gq[1])

            for i in range(g_off_exp.GetN()):
                g_off_exp.SetPointX(i, g_off_exp.GetPointX(i)*1000)
                g_off_exp.SetPointError(i, 0, 0, 0, 0)
            for i in range(g_off_obs.GetN()):
                g_off_obs.SetPointX(i, g_off_obs.GetPointX(i)*1000)


            g_off_exp.SetLineColor(kBlack)
            g_off_exp.SetLineStyle(2)
            g_off_exp.Draw("l")
            g_off_exp.SetTitle("")
            leg_exp.AddEntry(g_off_exp, "", "l")

            g_off_obs.SetLineColor(kBlack)
            g_off_obs.Draw("l")
            leg_obs.AddEntry(g_off_obs, "  JHEP 03 (2020) 145", "l")

            f_off.Close()
        else:
            f_off = TFile(path_offline_gauss[0])
            g_off_obs = f_off.Get(graph_offline_gauss[0])

            for i in range(g_off_obs.GetN()):
                g_off_obs.SetPointX(i, g_off_obs.GetPointX(i)*1000)

            g_off_obs.SetLineColor(kBlack)
            g_off_obs.Draw("l")
            leg_obs.AddEntry(g_off_obs, "  JHEP 03 (2020) 145", "l")
            leg_exp.AddEntry(0, "", "")

            f_off.Close()
        
            # myText(0.65, 0.48, 1, "JHEP03(2020)145:", 13)
            # leg_off = TLegend(0.65,0.39,0.85,0.44)
            # leg_off.AddEntry(g_off, "#sigma_{G}/m_{G} = %.2f" % 0.05, "l")
            # leg_off.Draw()

    if doTLA:
        if isZprime:
            f_tla = TFile(path_tla_gq[0])
            graphs_tla = []

            firstExp = True
            firstObs = True

            for i_tla, g in enumerate(graph_tla_gq):
                isExp = i_tla < len(graph_tla_gq)/2

                graphs_tla.append(f_tla.Get(g))

                graphs_tla[-1].SetLineColor(kGray+1)
                if isExp:
                    graphs_tla[-1].SetLineStyle(2)
                graphs_tla[-1].Draw("l")

                if isExp:
                    if firstExp:
                        graphs_tla[-1].SetTitle("")
                        leg_exp.AddEntry(graphs_tla[-1], "", "l")
                        firstExp = False
                else:
                    if firstObs:
                        leg_obs.AddEntry(graphs_tla[-1], "  PRL 121 (2018) 081801", "l")
                        firstObs = False

            f_tla.Close()
            
        else:
            f_tla = TFile(path_tla_gauss[0])
            graphs_tla = []

            firstExp = True
            firstObs = True

            for i_tla, g in enumerate(graph_tla_gauss):
                isExp = i_tla < len(graph_tla_gauss)/2

                graphs_tla.append(f_tla.Get(g))

                graphs_tla[-1].SetLineColor(kGray+1)
                if isExp:
                    graphs_tla[-1].SetLineStyle(2)
                graphs_tla[-1].Draw("l")

                if isExp:
                    if firstExp:
                        graphs_tla[-1].SetTitle("")
                        leg_exp.AddEntry(graphs_tla[-1], "", "l")
                        firstExp = False
                else:
                    if firstObs:
                        leg_obs.AddEntry(graphs_tla[-1], "  PRL 121 (2018) 081801", "l")
                        firstObs = False

            f_tla.Close()
            

    for dataset in range(len(paths)):

        for i,g in enumerate(g_obs_datasets[dataset]):
            if drawObserved:
                # g.Draw("l")
                g.Draw("lp")

    offset = 0.
    if doATLAS:
        ATLASLabel(0.20, 0.90, "Work in progress", 13)
        offset = 0.06
    myText(xToNDC(sigmeans[0][-1]), 0.90-offset, 1, "#sqrt{s}=13 TeV", 23)

    if doLogX:
        myText(xToNDC(sigmeans[0][-1]/1.06), 0.84-offset, 1, "%.1f fb^{-1}" % (lumis_target[0]*0.001), 33)
        myText(xToNDC(sigmeans[0][-1]*1.06), 0.84-offset, 1, "%.0f fb^{-1}" % (lumis_target[1]*0.001), 13)
    else:
        # myText(xToNDC(sigmeans[0][-1]-120), 0.84-offset, 1, "%.1f fb^{-1}" % (lumis_target[0]*0.001), 23)
        # myText(xToNDC(sigmeans[0][-1]+110), 0.84-offset, 1, "%.0f fb^{-1}" % (lumis_target[1]*0.001), 23)
        myText(xToNDC(sigmeans[0][-1]-130), 0.84-offset, 1, "%.1f fb^{-1}" % (lumis_target[0]*0.001), 23)
        myText(xToNDC(sigmeans[0][-1]+120), 0.84-offset, 1, "%.0f fb^{-1}" % (lumis_target[1]*0.001), 23)

    
    box = ROOT.TPave(leg_xmin,leg_ymin,0.93,leg_ymax,0,"NDC");
    box.SetFillStyle(1001)
    box.SetFillColor(0)
    box.SetLineWidth(0)
    box.Draw()

    box_xmin = leg_xmin + 0.003
    # box_xmax = leg_xmin + 0.045 # aligns in TCanvas, but not in pdf
    box_xmax = leg_xmin + 0.042

    # print(leg_ymax, leg_ymin, (leg_ymax-leg_ymin)/legentries, leg_ymax - 0.5*(leg_ymax-leg_ymin)/legentries, (leg_ymax-leg_ymin)/legentries/5)

    box_ycenter = leg_ymax - 0.5*(leg_ymax-leg_ymin)/legentries
    box_ywidth1 = (leg_ymax-leg_ymin)/legentries/6
    box_ywidth2 = 2*box_ywidth1
      
    box2 = ROOT.TPave(box_xmin,box_ycenter-box_ywidth2,box_xmax,box_ycenter+box_ywidth2,0,"NDC");
    box2.SetFillStyle(1001)
    box2.SetFillColor(colors[0]-10)
    box2.SetLineWidth(0)
    box2.Draw()

    box1 = ROOT.TPave(box_xmin,box_ycenter-box_ywidth1,box_xmax,box_ycenter+box_ywidth1,0,"NDC");
    box1.SetFillStyle(1001)
    box1.SetFillColor(colors[0]-9)
    box1.SetLineWidth(0)
    box1.Draw()
    
    myText(leg_xmin, 0.9, 1, "95% CL_{s} upper limits", 13)
    leg_exp.Draw()
    if drawObserved:
        text = "exp  obs"
        if doOffline or doTLA:
            if not isZprime:
                text += "  #sigma_{G}/m_{G} = %.2f" % (sigwidths[0][0]/100.)
        myText(leg_xmin, 0.83, 1, text, 13)
        # myText(0.60, 0.84, 1, "exp", 13)
        # myText(0.65, 0.84, 1, "obs", 13)
        leg_obs.Draw()
    else:
        myText(leg_xmin, 0.83, 1, "Expected:", 13)

    c.Update()
        
    # input("Press enter to continue...")

    c.Print("../run/limitPlot_joined.svg")
    c.Print("../run/limitPlot_joined.pdf")


if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
