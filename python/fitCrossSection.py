#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import ROOT
import sys, re, os, math, argparse
from glob import glob

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def main(args):
    ROOT.SetAtlasStyle()

    # in pb from AMI:
    x_secs = {
        #350: 117.5, # wrong xsec, has m_chi=10 GeV, g_chi=1.5
        350: 6.0568*25,
        # 450: 189.05/4,
        600: 20.269,
        1000: 2.7415,
        2000: 0.11192}

    g = ROOT.TGraphErrors()

    for i,x in enumerate(x_secs):
        g.SetPoint(i, x, x_secs[x])
        g.SetPointError(i, 0, 0.1*x_secs[x])
        
    f1 = ROOT.TF1("f1", "[0]*(x/13000)^[1]*(1-x/13000)^[2]",200,3000)

    f1.SetParameter(0, 0.00634)
    f1.SetParameter(1, -2.83)
    f1.SetParameter(2, 14.60)

    f1.SetLineColor(ROOT.kRed)
    f1.SetNpx(1000)
    
    c = ROOT.TCanvas("c1", "c1", 800, 600)
    c.SetLogx()
    c.SetLogy()
    # c.SetRightMargin(0.10)
    # c.SetLeftMargin(0.10)
    # c.SetTickx(1)
    # c.SetTicky(0)


    fitresult = g.Fit(f1, "SQME0")
    pars = list(fitresult.Parameters())
    pars.append(fitresult.Chi2())
    f1.Draw()
    # print(pars)

    parerrs = []
    parerrs.append(fitresult.ParError(0))
    parerrs.append(fitresult.ParError(1))
    parerrs.append(fitresult.ParError(2))

    for i in range(3):
        print("p%d: %.5f #pm %.5f" % (i+1, pars[i], parerrs[i]))

    print("chi2: %.2f" %  pars[-1])

    f1.GetXaxis().SetTitle("m_{Z'} [GeV]")
    f1.GetYaxis().SetTitle("Total cross section [pb]")
    f1.GetYaxis().SetTitleOffset(1.5)
    f1.GetXaxis().SetRangeUser(300, 2500)
    f1.GetYaxis().SetRangeUser(1e-2,5e2)
    f1.GetXaxis().SetMoreLogLabels()
    f1.GetXaxis().SetNoExponent()

    ROOT.gPad.Update()

    g.Draw("p same")

    leg = ROOT.TLegend(0.2,0.2,0.5,0.32)
    leg.AddEntry(g,"MC total cross section","ep")
    leg.AddEntry(f1,"p_{1}#upoint x^{p_{2}}#upoint (1-x)^{p_{3}}", "l")
    leg.Draw()

    ROOT.myText(0.90, 0.90, 1, "MadGraph5_aMC@NLO", 33)
    ROOT.myText(0.90, 0.84, 1, "leptophobic Z', g_{q}=0.1", 33)

    ROOT.gPad.Update()
  
    # input("wait")
    
    c.Print("crosssection_Zprime.pdf")

    fout = ROOT.TFile("crosssection_Zprime.root", "RECREATE")
    fout.cd()
    g.Write("g_xsec")
    f1.Write("f1_xsec")
    fout.Close()


if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
