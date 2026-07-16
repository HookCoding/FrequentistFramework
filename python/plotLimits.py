#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob

# Use -b as last cmdline argument to plotLimits.py to activate batch mode and get proper transparent png output

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

# lumi = 29300
# lumi = 30000
lumi = 133000

def createFillBetweenGraphs(g1, g2):
  g_fill = TGraph()
  
  for i in range(g1.GetN()):
      x=ROOT.Double()
      y=ROOT.Double()
    
      g1.GetPoint(i, x, y)
      if math.isnan(y) or math.isinf(y):
        continue

      g_fill.SetPoint(g_fill.GetN(), x, y)

  for i in range(g2.GetN()-1, -1, -1):
      x=ROOT.Double()
      y=ROOT.Double()
    
      g2.GetPoint(i, x, y)
      if math.isnan(y) or math.isinf(y):
        continue
    
      g_fill.SetPoint(g_fill.GetN(), x, y)

  return g_fill


def main(args):
    SetAtlasStyle()

    paths = args
    sigmeans = set()
    sigwidths = set()

    dict_file = {}

    for p in paths:

      if isZprime:
	res=re.search(r'mR(\d+)', p)
	w = 999 # dummy
	xAxisTitle = "M_{Z'} [GeV]"
	yMax = 100.
	yMin = 1e-4
      else:
	res=re.search(r'mean(\d+)_width(\d+)', p)
	w=int(res.group(2))
	xAxisTitle = "M_{G} [GeV]"
	yMax = 50.
	yMin = 1e-2
      
      m=int(res.group(1))
      sigmeans.add(m)
      sigwidths.add(w)

      dict_file[(m, w)] = p

    sigmeans = list(sigmeans)
    sigwidths = list(sigwidths)

    sigmeans.sort()
    sigwidths.sort()

    colors = [kBlue, kRed+1, kOrange-3, kGreen, kPink]

    g_obs = []
    g_exp = []
    g_exp1 = []
    g_exp2 = []
    g_exp1u = []
    g_exp2u = []
    g_exp1d = []
    g_exp2d = []

    for i,sigwidth in enumerate(sigwidths):

        g_obs.append( TGraph() )
        g_exp.append( TGraph() )
        g_exp1u.append( TGraph() )
        g_exp2u.append( TGraph() )
        g_exp1d.append( TGraph() )
        g_exp2d.append( TGraph() )
        
        for j,sigmean in enumerate(sigmeans):
            
            try:
                tmp_path=dict_file[(sigmean, sigwidth)]

                f = TFile(tmp_path, "READ")
                if f.IsZombie():
                    print "WARNING: Missing point (%d,%d)" % (sigmean, sigwidth)
                    continue
                h = f.Get("limit")

                obs = h.GetBinContent(h.GetXaxis().FindBin("Observed")) / lumi
                exp = h.GetBinContent(h.GetXaxis().FindBin("Expected")) / lumi
                exp1u = h.GetBinContent(h.GetXaxis().FindBin("+1sigma")) / lumi
                exp2u = h.GetBinContent(h.GetXaxis().FindBin("+2sigma")) / lumi
                exp1d = h.GetBinContent(h.GetXaxis().FindBin("-1sigma")) / lumi
                exp2d = h.GetBinContent(h.GetXaxis().FindBin("-2sigma")) / lumi

                if math.isnan(obs) or math.isinf(obs):
                  raise ValueError('observed limit not finite for point (%s, %w)' % (sigmean, sigwidth))
                
                g_obs[i].SetPoint(g_obs[i].GetN(), sigmean, obs)
                g_exp[i].SetPoint(g_exp[i].GetN(), sigmean, exp)
                g_exp1u[i].SetPoint(g_exp1u[i].GetN(), sigmean, exp1u)
                g_exp2u[i].SetPoint(g_exp2u[i].GetN(), sigmean, exp2u)
                g_exp1d[i].SetPoint(g_exp1d[i].GetN(), sigmean, exp1d)
                g_exp2d[i].SetPoint(g_exp2d[i].GetN(), sigmean, exp2d)
            except Exception as e:
                print e
                print "WARNING: Missing point (%d,%d)" % (sigmean, sigwidth)


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


    c = TCanvas("c1", "c1", 800, 600)
    c.SetLogy()

    if isZprime:
      leg_obs = TLegend(0.65,0.85,0.85,0.9)
      leg_exp = TLegend(0.65,0.78,0.85,0.83)
    else:
      leg_obs = TLegend(0.65,0.70,0.85,0.85)
      leg_exp = TLegend(0.65,0.49,0.85,0.64)
     

    g_exp2[0].Draw("af")
    g_exp2[0].GetXaxis().SetTitle(xAxisTitle)
    g_exp2[0].GetYaxis().SetTitle("#sigma #times #it{A} #times #it{BR} [pb]")
    g_exp2[0].GetHistogram().SetMaximum(yMax)
    g_exp2[0].GetHistogram().SetMinimum(yMin)
    g_exp2[0].GetXaxis().SetLimits(min(sigmeans), max(sigmeans))

    g_exp2[0].Draw("af")
    c.Modified()

    g_exp1[0].Draw("f")

    for i,g in enumerate(g_exp):
        g.Draw("l")
	if isZprime:
	  leg_exp.AddEntry(g, "Expected", "l")
	else:
	  leg_exp.AddEntry(g, "#sigma_{G}/M_{G} = %.2f" % (sigwidths[i]/100.), "l")
    for i,g in enumerate(g_obs):
        g.Draw("pl")
	if isZprime:
	  leg_obs.AddEntry(g, "Observed","lp")
	else:
	  leg_obs.AddEntry(g, "#sigma_{G}/M_{G} = %.2f" % (sigwidths[i]/100.), "lp")
        
    ATLASLabel(0.20, 0.90, "Work in progress", 13)
    myText(0.20, 0.85, 1, "95% CL_{s} upper limits", 13)
    myText(0.20, 0.80, 1, "#sqrt{s}=13 TeV, %.1f fb^{-1}" % (lumi/1000.), 13)

    if not isZprime:
      myText(0.65, 0.90, 1, "Observed:", 13)
      myText(0.65, 0.69, 1, "Expected:", 13)

    leg_exp.Draw()
    leg_obs.Draw()

    c1.Print("../run/limitPlot.svg")
    c1.Print("../run/limitPlot.pdf")

    fout=TFile("../run/limits.root", "RECREATE")
    for i,g in enumerate(g_exp):
        g.Write("g_exp_width%d" % sigwidths[i])
    for i,g in enumerate(g_exp1):
        g.Write("g_exp_1sigma_width%d" % sigwidths[i])
    for i,g in enumerate(g_exp2):
        g.Write("g_exp_2sigma_width%d" % sigwidths[i])

    for i,g in enumerate(g_obs):
        g.Write("g_obs_width%d" % sigwidths[i])

    fout.Close()
    
if __name__ == "__main__":  
   
   isZprime = False
   if "--zprime" in sys.argv[1:]:
      isZprime = True
   
   args=[x for x in sys.argv[1:] if not x.startswith("-")]
   sys.exit(main(args))   
