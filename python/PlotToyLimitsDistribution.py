#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
import numpy as np

# Use -b as last cmdline argument to plotLimits.py to activate batch mode and get proper transparent png output

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

lumi = 130000

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

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

    infile = ROOT.TFile(args[0])

    colors = [kBlue, kRed+1, kOrange-3]

    graphs_obs = {}
    graphs_exp = {}
    graphs_exp_2u = {}
    graphs_exp_1u = {}
    graphs_exp_1d = {}
    graphs_exp_2d = {}

    for k in infile.GetListOfKeys():
        name = k.GetName()
        g = infile.Get(name)

        if not isinstance(g, ROOT.TGraph):
            continue

        if "exp" in name:
            if "exp_2u" in name:
                graphs_exp_2u[g.GetTitle()] = g
            elif "exp_1u" in name:
                graphs_exp_1u[g.GetTitle()] = g
            elif "exp_1d" in name:
                graphs_exp_1d[g.GetTitle()] = g
            elif "exp_2d" in name:
                graphs_exp_2d[g.GetTitle()] = g
            else:
                graphs_exp[g.GetTitle()] = g
        else:
            graphs_obs[g.GetTitle()] = g
            print "adding", g.GetTitle()

    masses = natural_sort(graphs_obs.keys())

    g_obs = {}
    g_exp = {}
    g_exp_2u = {}
    g_exp_1u = {}
    g_exp_1d = {}
    g_exp_2d = {}

    for mass in masses:
        graph = graphs_obs[mass]
        nobs_list = []

        for n in range(graph.GetN()):
            ninj = graph.GetX()[n]
            ulim = graph.GetY()[n] / lumi
            if ninj != 0:
                continue
            nobs_list.append(ulim)

        nobs_list.sort()
        med = np.percentile(nobs_list, 50)
        med_2u = np.percentile(nobs_list, 97.72)
        med_1u = np.percentile(nobs_list, 84.13)
        med_1d = np.percentile(nobs_list, 15.87)
        med_2d = np.percentile(nobs_list, 2.28)

        res = re.search(r'^(\d+).*\((\d+)%\)', mass)
        m=int(res.group(1))
        w=int(res.group(2))

        # print m, w, med, med_2u, med_1u, med_1d, med_2d

        if not w in g_obs:
            g_obs[w] = ROOT.TGraphAsymmErrors()
        if not w in g_exp:
            g_exp[w] = ROOT.TGraph()
        if not w in g_exp_2u:
            g_exp_2u[w] = ROOT.TGraph()
        if not w in g_exp_1u:
            g_exp_1u[w] = ROOT.TGraph()
        if not w in g_exp_1d:
            g_exp_1d[w] = ROOT.TGraph()
        if not w in g_exp_2d:
            g_exp_2d[w] = ROOT.TGraph()

        g_obs[w].SetPoint(g_obs[w].GetN(), m, med)
        g_obs[w].SetPointError(g_obs[w].GetN()-1, 0, 0, med-med_1d, med_1u-med)

        g_exp[w].SetPoint(g_exp[w].GetN(), m, graphs_exp[mass].GetY()[0] / lumi)
        g_exp_2u[w].SetPoint(g_exp_2u[w].GetN(), m, graphs_exp_2u[mass].GetY()[0] / lumi)
        g_exp_1u[w].SetPoint(g_exp_1u[w].GetN(), m, graphs_exp_1u[mass].GetY()[0] / lumi)
        g_exp_1d[w].SetPoint(g_exp_1d[w].GetN(), m, graphs_exp_1d[mass].GetY()[0] / lumi)
        g_exp_2d[w].SetPoint(g_exp_2d[w].GetN(), m, graphs_exp_2d[mass].GetY()[0] / lumi)

    for w in g_obs:
        g_exp_1ud = createFillBetweenGraphs(g_exp_1u[w], g_exp_1d[w])
        g_exp_2ud = createFillBetweenGraphs(g_exp_2u[w], g_exp_2d[w])

        g_exp_1ud.SetFillColorAlpha(colors[0], 0.2)
        g_exp_2ud.SetFillColorAlpha(colors[0], 0.2)
        g_exp[w].SetLineColor(colors[0])
        g_exp[w].SetLineStyle(2)
        g_exp[w].SetLineWidth(2)
        g_obs[w].SetLineWidth(2)
        g_obs[w].SetLineColor(colors[0])
        g_obs[w].SetMarkerColor(colors[0])

        c = TCanvas("c1", "c1", 800, 600)
        c.SetLogy()

        g_exp_2ud.Draw("af")

        g_exp_2ud.GetXaxis().SetTitle("M_{G} [GeV]")
        g_exp_2ud.GetYaxis().SetTitle("#sigma #times #it{A} #times #it{BR} [pb]")
        g_exp_2ud.GetHistogram().SetMaximum(80)
        g_exp_2ud.GetXaxis().SetLimits(600, 1800)

        g_exp_2ud.Draw("af")
        c.Modified()

        g_exp_1ud.Draw("f")

        g_exp[w].Draw("l")
        g_obs[w].Draw("lp")

        ATLASLabel(0.20, 0.90, "Work in progress", 13)
        myText(0.20, 0.85, 1, "95% CL_{s} upper limits", 13)
        myText(0.20, 0.80, 1, "#sqrt{s}=13 TeV, %.1f fb^{-1}" % (lumi/1000.), 13)
        # myText(0.20, 0.75, 1, "NLOFit, 10#sigma constraints", 13)
        myText(0.20, 0.75, 1, "5-par fit", 13)
        myText(0.70, 0.90, 1, "%d%% signal width:" % w, 13)

        leg = TLegend(0.70,0.75,0.85,0.85)
        leg.AddEntry(g_obs[w], "Observed", "pl")
        leg.AddEntry(g_exp[w], "Expected", "l")
        leg.Draw()

        c.Print(args[0].replace(".root", "_width%d.png") % w)
        c.Print(args[0].replace(".root", "_width%d.pdf") % w)

    
if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not x.startswith("-")]
   sys.exit(main(args))   
