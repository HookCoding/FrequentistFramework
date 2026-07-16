#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from math import isnan
from glob import glob
from color import getColorSteps

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

paths = ["../run/Limits_nloFit_J50CombyStar06_templates2021_CT14nnlo_scaledOnly_constr5_mean${MEAN}_width${WIDTH}.root", 
         "../run/Limits_nloFit_J100yStar06_templates2021_CT14nnlo_scaledOnly_constr5_mean${MEAN}_width${WIDTH}.root",
]


sigmeans  = [ [ 300, 350, 375, 400, 450, 500, ], 
              [ 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1300, 1400, 1500, 1600, 1700, 1800, ] ]
sigwidths = [ [ 5, 10, 15], 
              [ 5, 10, 15] ]

# lumis = [ 3600, 29300 ]
lumis = [ 15000, 133000 ]

def xToNDC(x):
    gPad.Update()
    lm = gPad.GetLeftMargin()
    rm = 1.-gPad.GetRightMargin()
    xndc = (rm-lm)*((gPad.XtoPad(x)-gPad.GetUxmin())/(gPad.GetUxmax()-gPad.GetUxmin()))+lm
    return xndc

def yToNDC(y):
    gPad.Update()
    tm = 1.-gPad.GetTopMargin()
    bm = gPad.GetBottomMargin()
    yndc = (tm-bm)*((gPad.YtoPad(y)-gPad.GetUymin())/(gPad.GetUymax()-gPad.GetUymin()))+bm
    return yndc

def createFillBetweenGraphs(g1, g2):
  g_fill = TGraph()
  
  for i in range(g1.GetN()):
      x=ROOT.Double()
      y=ROOT.Double()
    
      g1.GetPoint(i, x, y)
    
      g_fill.SetPoint(g_fill.GetN(), x, y)

  for i in range(g2.GetN()-1, -1, -1):
      x=ROOT.Double()
      y=ROOT.Double()
    
      g2.GetPoint(i, x, y)
    
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
            
                f = TFile(tmp_path, "READ")
                if f.IsZombie():
                    continue
                h = f.Get("limit")
                
                obs = h.GetBinContent(h.GetXaxis().FindBin("Observed")) / lumis[dataset]
                exp = h.GetBinContent(h.GetXaxis().FindBin("Expected")) / lumis[dataset]
                exp1u = h.GetBinContent(h.GetXaxis().FindBin("+1sigma")) / lumis[dataset]
                exp2u = h.GetBinContent(h.GetXaxis().FindBin("+2sigma")) / lumis[dataset]
                exp1d = h.GetBinContent(h.GetXaxis().FindBin("-1sigma")) / lumis[dataset]
                exp2d = h.GetBinContent(h.GetXaxis().FindBin("-2sigma")) / lumis[dataset]
                
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

    # leg_obs = TLegend(0.65,0.70,0.85,0.85)
    # leg_exp = TLegend(0.65,0.47,0.85,0.62)
    leg_obs = TLegend(0.65,0.70,0.85,0.85)
    leg_exp = TLegend(0.65,0.70,0.85,0.85)

    # minY = 0.02
    # maxY = 500
    minY = 0.01
    maxY = 1000

    g_exp_datasets[0][0].Draw("af")
    g_exp_datasets[0][0].GetXaxis().SetTitle("M_{G} [GeV]")
    g_exp_datasets[0][0].GetYaxis().SetTitle("#sigma #times #it{A} #times #it{BR} [pb]")
    g_exp_datasets[0][0].GetYaxis().SetTitleOffset(1.0)
    g_exp_datasets[0][0].GetHistogram().SetMinimum(minY)
    g_exp_datasets[0][0].GetHistogram().SetMaximum(maxY)
    g_exp_datasets[0][0].GetXaxis().SetLimits(min(sigmeans[0])-49.9, max(sigmeans[-1])+49.9)

    c.Modified()
    
    for dataset in range(len(paths)):

        if dataset != len(paths)-1:

            l=TLine()
            l.DrawLineNDC(xToNDC(sigmeans[dataset][-1]), gPad.GetBottomMargin(), xToNDC(sigmeans[dataset][-1]), 0.72)

        g_exp2_datasets[dataset][0].Draw("f")
        g_exp1_datasets[dataset][0].Draw("f")

        for i,g in enumerate(g_exp_datasets[dataset]):
            g.Draw("l")
            if (dataset==0):
                leg_exp.AddEntry(g, "#sigma_{G}/M_{G} = %.2f" % (sigwidths[dataset][i]/100.), "l")
        for i,g in enumerate(g_obs_datasets[dataset]):
            # g.Draw("pl")
            if (dataset==0):
                leg_obs.AddEntry(g, "#sigma_{G}/M_{G} = %.2f" % (sigwidths[dataset][i]/100.), "lp")

        
    ATLASLabel(0.20, 0.90, "Work in progress", 13)
    myText(0.20, 0.84, 1, "95% CL_{s} upper limits", 13)
    # myText(0.20, 0.80, 1, "#sqrt{s}=13 TeV, 3.6 fb^{-1}", 13)
    myText(xToNDC(500), 0.78, 1, "#sqrt{s}=13 TeV", 23)

    # myText(xToNDC(575), 0.72, 1, "%.1f fb^{-1}" % (lumis[0]*0.001), 23)
    # myText(xToNDC(825), 0.72, 1, "%.1f fb^{-1}" % (lumis[1]*0.001), 23)

    myText(xToNDC(390), 0.72, 1, "%.0f fb^{-1}" % (lumis[0]*0.001), 23)
    myText(xToNDC(610), 0.72, 1, "%.0f fb^{-1}" % (lumis[1]*0.001), 23)

    # myText(0.65, 0.90, 1, "Observed:", 13)
    # myText(0.65, 0.67, 1, "Expected:", 13)
    myText(0.65, 0.90, 1, "Expected:", 13)
    leg_exp.Draw()
    # leg_obs.Draw()

    c1.Print("../run/limitPlot_joined.svg")
    c1.Print("../run/limitPlot_joined.pdf")

    # raw_input("Press enter to continue...")

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
