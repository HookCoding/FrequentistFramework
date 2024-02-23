#!/usr/bin/env python
from __future__ import print_function
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

# paths = ["../run/Limits_nloFit_J50CombyStar06_templates2021_CT14nnlo_scaledOnly_constr5_mean${MEAN}_width${WIDTH}.root", 
#          "../run/Limits_nloFit_J100yStar06_templates2021_CT14nnlo_scaledOnly_constr5_mean${MEAN}_width${WIDTH}.root",
# ]

# paths = ["/data/field01/users/bartels/FarmOutput/TLA/Fitting/globalFit_expectedLimits_20220825/anaFit_J50Comb_fourPar/output.*.0/run/Limits_*_mean${MEAN}_width${WIDTH}.root", 
#          "/data/field01/users/bartels/FarmOutput/TLA/Fitting/globalFit_expectedLimits_start457_20220825/anaFit_J100_sixPar/output.*.0/run/Limits_*_mean${MEAN}_width${WIDTH}.root",
# ]

paths = ["/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_noGSC_spur0.5_allSyst_additive_20240213/anaFit_gauss_syst_J50_fivePar/output.*/run/Limits_*_mean${MEAN}_width${WIDTH}.root", 
         "/data/field01/users/bartels/FarmOutput/TLA/Fitting/anaFit_obsLimits_noGSC_spur0.5_allSyst_additive_20240213/anaFit_gauss_syst_J100_fivePar/output.*/run/Limits_*_mean${MEAN}_width${WIDTH}.root",
]


# sigmeans  = [ [ 375, 400, 425, 450, 500, 525, 550, 575, 600 ], 
#               [ 600, 625, 650, 675, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, ] ]
sigmeans  = [ [ 375, 400, 425, 450, 475, 500, 525, 550 ], 
              [ 550, 575, 600, 625, 650, 675, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, ] ]
sigwidths = [ [ 5, 10, 15], 
              [ 5, 10, 15] ]

# lumis = [ 1500, 29500 ]
# lumis_target = [ 14500, 133000 ]

lumis = [ 15000, 132000 ]
lumis_target = lumis

drawObserved = True

doLogX = False

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
                    continue

                f = TFile(tmp_path, "READ")
                if f.IsZombie():
                    continue
                h = f.Get("limit")
                
                scalefactor = 1. / lumis[dataset] / sqrt(lumis_target[dataset] / lumis[dataset])
                obs = h.GetBinContent(h.GetXaxis().FindBin("Observed")) * scalefactor
                exp = h.GetBinContent(h.GetXaxis().FindBin("Expected")) * scalefactor
                exp1u = h.GetBinContent(h.GetXaxis().FindBin("+1sigma")) * scalefactor
                exp2u = h.GetBinContent(h.GetXaxis().FindBin("+2sigma")) * scalefactor
                exp1d = h.GetBinContent(h.GetXaxis().FindBin("-1sigma")) * scalefactor
                exp2d = h.GetBinContent(h.GetXaxis().FindBin("-2sigma")) * scalefactor
                
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
    
            g_exp1[-1].SetFillColorAlpha(colors[i], 0.2)
            g_exp2[-1].SetFillColorAlpha(colors[i], 0.2)
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
    c.SetLogy()
    if doLogX:
        c.SetLogx()

    leg_obs = TLegend(0.65,0.70,0.85,0.85)
    if drawObserved:
        leg_exp = TLegend(0.65,0.47,0.85,0.62)
    else:
        leg_exp = TLegend(0.65,0.70,0.85,0.85)

    # minY = 0.02
    # maxY = 500
    minY = 0.01
    maxY = 2000

    g_exp_datasets[0][0].Draw("af")
    g_exp_datasets[0][0].GetXaxis().SetTitle("m_{G} [GeV]")
    g_exp_datasets[0][0].GetYaxis().SetTitle("#sigma #times #it{A} #times #it{BR} [pb]")
    g_exp_datasets[0][0].GetYaxis().SetTitleOffset(1.2)
    g_exp_datasets[0][0].GetHistogram().SetMinimum(minY)
    g_exp_datasets[0][0].GetHistogram().SetMaximum(maxY)
    # g_exp_datasets[0][0].GetXaxis().SetLimits(min(sigmeans[0])-49.9, max(sigmeans[-1])+49.9)
    if doLogX:
        g_exp_datasets[0][0].GetXaxis().SetLimits(350,2000)
        g_exp_datasets[0][0].GetXaxis().SetMoreLogLabels()
        g_exp_datasets[0][0].GetXaxis().SetNoExponent()
    else:
        g_exp_datasets[0][0].GetXaxis().SetLimits(min(sigmeans[0])-99.9, max(sigmeans[-1])+49.9)

    c.Modified()
    
    for dataset in range(len(paths)):

        if dataset != len(paths)-1:

            l=TLine()
            l.SetLineStyle(2)
            if doLogX:
                l.DrawLineNDC(xToNDC(sigmeans[dataset][-1]), gPad.GetBottomMargin(), xToNDC(sigmeans[dataset][-1]), 0.73)
            else:
                l.DrawLineNDC(xToNDC(sigmeans[dataset][-1]), gPad.GetBottomMargin(), xToNDC(sigmeans[dataset][-1]), 0.73)

        g_exp2_datasets[dataset][0].Draw("f")
        g_exp1_datasets[dataset][0].Draw("f")

        for i,g in enumerate(g_exp_datasets[dataset]):
            g.Draw("l")
            if (dataset==0):
                leg_exp.AddEntry(g, "#sigma_{G}/m_{G} = %.2f" % (sigwidths[dataset][i]/100.), "l")
        for i,g in enumerate(g_obs_datasets[dataset]):
            if drawObserved:
                g.Draw("lp")
            if (dataset==0):
                leg_obs.AddEntry(g, "#sigma_{G}/m_{G} = %.2f" % (sigwidths[dataset][i]/100.), "lp")

        
    ATLASLabel(0.20, 0.90, "Work in progress", 13)
    myText(0.20, 0.84, 1, "95% CL_{s} upper limits", 13)
    myText(xToNDC(sigmeans[0][-1]), 0.78, 1, "#sqrt{s}=13 TeV", 23)

    if doLogX:
        myText(xToNDC(sigmeans[0][-1]/1.05), 0.72, 1, "%.1f fb^{-1}" % (lumis_target[0]*0.001), 33)
        myText(xToNDC(sigmeans[0][-1]*1.05), 0.72, 1, "%.0f fb^{-1}" % (lumis_target[1]*0.001), 13)
    else:
        myText(xToNDC(sigmeans[0][-1]-120), 0.72, 1, "%.1f fb^{-1}" % (lumis_target[0]*0.001), 23)
        myText(xToNDC(sigmeans[0][-1]+110), 0.72, 1, "%.0f fb^{-1}" % (lumis_target[1]*0.001), 23)

    if drawObserved:
        myText(0.65, 0.90, 1, "Observed:", 13)
        myText(0.65, 0.67, 1, "Expected:", 13)
        leg_obs.Draw()
    else:
        myText(0.65, 0.90, 1, "Expected:", 13)
    leg_exp.Draw()

    c.Print("../run/limitPlot_joined.svg")
    c.Print("../run/limitPlot_joined.pdf")

    # input("Press enter to continue...")

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
