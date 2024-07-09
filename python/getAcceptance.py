#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse
from glob import glob

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def main(args):
    signals = glob("/data/silo02/users/bartels/gridResults/signalsNoGSC/*/*.root")

    print("Signal\t\tAcc\t>344GeV\t>481GeV")

    g_acc_mjj0 = ROOT.TGraph()
    g_acc_mjj344 = ROOT.TGraph()
    g_acc_mjj481 = ROOT.TGraph()

    for s in signals:
    
        searchstring =r'mR(\d+)p(\d+).*_gSM(\d+)p(\d+)'
        res=re.search(searchstring, s)
        name=res.group(0)

        f = ROOT.TFile(s)
        h_cutflow = f.Get("hists_yStar06_massCut/cutflow_weighted")
        h_mjj = f.Get("hists_yStar06_massCut/afterSelection/nominal/h_mjj")

        N_tot = h_cutflow.GetBinContent(1)
        N_sel = h_mjj.Integral()
        N_344 = h_mjj.Integral(h_mjj.FindBin(344),-1)
        N_481 = h_mjj.Integral(h_mjj.FindBin(481),-1)

        print("%s & %.3f & %.3f & %.3f \\\\" % (name, N_sel/N_tot, N_344/N_tot, N_481/N_tot))

        m = None
        if name == "mR0p35_mDM10_gSM0p10":
            m = 350
        elif name == "mR0p6_gSM0p1":
            m = 600
        elif name == "mR1p0_gSM0p1":
            m = 1000
        elif name == "mR2p0_gSM0p1":
            m = 2000

        if m != None:
            g_acc_mjj0.SetPoint(g_acc_mjj0.GetN(), m, N_sel/N_tot)
            g_acc_mjj344.SetPoint(g_acc_mjj344.GetN(), m, N_344/N_tot)
            g_acc_mjj481.SetPoint(g_acc_mjj481.GetN(), m, N_481/N_tot)
            
    fout = ROOT.TFile("acceptance_zprime.root", "RECREATE")

    g_acc_mjj0.Write("g_acc_mjj0")
    g_acc_mjj344.Write("g_acc_mjj344")
    g_acc_mjj481.Write("g_acc_mjj481")

    fout.Close()


if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
