#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

path_limits = "../run/Limits_swift_J100yStar06_mean700_width5_amp3_0_tol*.txt"
# path_limits = "../run/Limits_nlofit_J100yStar06_mean700_width5_amp3_0_tol*.txt"
# n_injected = 20260
# n_injected = 23520
# n_injected = 58240
n_injected = 47090

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
 
    # colors = [kBlue, kMagenta+2, kRed+1, kGreen+2]
    colors = [kBlue, kRed+1, kOrange-3]

    g_obs = TGraph()
    g_exp = TGraph()
    g_exp1u = TGraph()
    g_exp2u = TGraph()
    g_exp1d = TGraph()
    g_exp2d = TGraph()
                
    tol_limits = dict()
    
    for path in glob(path_limits):

        with open(path) as f:
            limits = [float(x) for x in f.readline().split()]
            limits = [0 if math.isnan(x) else x for x in limits]

            tol = path.split("_tol")[-1]
            tol = tol.split(".txt")[0]
            tol = float(tol)

            print tol, limits

            tol_limits[tol] = limits

    for tol in sorted(tol_limits):

        limits = tol_limits[tol]

        g_obs.SetPoint(g_obs.GetN(), tol, limits[0])
        g_exp.SetPoint(g_exp.GetN(), tol, limits[1])
        g_exp2u.SetPoint(g_exp2u.GetN(), tol, limits[2])
        g_exp1u.SetPoint(g_exp1u.GetN(), tol, limits[3])
        g_exp2d.SetPoint(g_exp2d.GetN(), tol, limits[4])
        g_exp1d.SetPoint(g_exp1d.GetN(), tol, limits[5])

    g_exp1 = createFillBetweenGraphs(g_exp1d, g_exp1u)
    g_exp2 = createFillBetweenGraphs(g_exp2d, g_exp2u)
        
    g_exp1.SetFillColorAlpha(colors[0], 0.2)
    g_exp2.SetFillColorAlpha(colors[0], 0.2)
    g_exp.SetLineColor(colors[0])
    g_exp.SetLineStyle(2)
    g_exp.SetLineWidth(2)
    g_obs.SetLineWidth(2)
    g_obs.SetLineColor(colors[0])
    g_obs.SetMarkerColor(colors[0])

    c = TCanvas("c1", "c1", 800, 600)
    c.SetLogx()


    g_exp2.Draw("af")
    g_exp2.GetXaxis().SetTitle("minTolerance")
    g_exp2.GetYaxis().SetTitle("N_{sig} 95% CLs limit")
    g_exp2.GetYaxis().SetTitleOffset(1.5)
    g_exp2.GetHistogram().SetMinimum(0.)
    g_exp2.GetHistogram().SetMaximum(max(g_exp2.GetHistogram().GetMaximum(), g_obs.GetHistogram().GetMaximum()))
    # g_exp2.GetXaxis().SetLimits()

    g_exp2.Draw("af")
    c.Modified()

    g_exp1.Draw("f")
    g_exp.Draw("l")
    g_obs.Draw("lp")

    ATLASLabel(0.58, 0.90, "Work in progress", 13)
    myText(0.90, 0.85, 1, "5% Gaussian at 700 GeV", 33)
    myText(0.900, 0.80, 1, "%d injected events" % n_injected, 33)
    myText(0.900, 0.75, 1, "WiFt (whw=9)", 33)
    # myText(0.900, 0.75, 1, "NLOFit", 33)
        
    c1.Print("../run/tolerancePlot_swift_700.png")
    # c1.Print("../run/tolerancePlot_nlofit_700.png")

#    raw_input("Press enter to continue...")

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
