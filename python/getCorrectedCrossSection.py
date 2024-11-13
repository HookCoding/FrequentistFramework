#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse
import json
from glob import glob
from InjectZprime import doubleSidedCrystalBall

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

mjj_thresholds = [344, 481]

def getMjjCorrection(f1, xmin):
    f1_integral = f1.Integral(f1.GetXmin(), f1.GetXmax())
    return f1.Integral(xmin, f1.GetXmax()) / f1_integral

def main(args):

    acceptance_files = [
        "../run/signal_etaVetos/acceptance_zprime_inclusive.root",
        "../run/signal_etaVetos/acceptance_zprime_rejectEta_09_11_and_15_17.root",
        "../run/signal_etaVetos/acceptance_zprime_rejectEta_10_11_and_15_16.root",
        "../run/signal_etaVetos/acceptance_zprime_rejectEta_10_14.root",
        "../run/signal_etaVetos/acceptance_zprime_rejectEta_10_16.root",
        "../run/signal_etaVetos/acceptance_zprime_rejectEta_10_24.root",
    ]

    output_files = [
        "../run/signal_etaVetos/acceptance_and_crosssection_zprime_inclusive.root",
        "../run/signal_etaVetos/acceptance_and_crosssection_zprime_rejectEta_09_11_and_15_17.root",
        "../run/signal_etaVetos/acceptance_and_crosssection_zprime_rejectEta_10_11_and_15_16.root",
        "../run/signal_etaVetos/acceptance_and_crosssection_zprime_rejectEta_10_14.root",
        "../run/signal_etaVetos/acceptance_and_crosssection_zprime_rejectEta_10_16.root",
        "../run/signal_etaVetos/acceptance_and_crosssection_zprime_rejectEta_10_24.root",
    ]

    crosssection_file = "../run/acceptance/crosssection_Zprime.root"

    signal_file = "../run/signalUncertainty/signalUncertainty_adjustedNoGSC_interpolated.json"

    for k,a in enumerate(acceptance_files):
    
        f_cross_section = ROOT.TFile(crosssection_file)
        f1_cross_section = f_cross_section.Get("f1_xsec")
    
        # f_acceptance = ROOT.TFile("thesis_acceptance_noGSC/acceptance_zprime.root")
        f_acceptance = ROOT.TFile(a)
        g_acceptance = f_acceptance.Get("g_acc_mjj0")
    
        f_dscb = signal_file
        with open(f_dscb) as f:
            dict_dscb = json.load(f)
    
        g_acceptance_mjj_corr = []
        g_xsec_times_acc = []
    
        for t in mjj_thresholds:
            g_acceptance_mjj_corr.append(ROOT.TGraph())
            g_xsec_times_acc.append(ROOT.TGraph())
        g_xsec_times_acc.append(ROOT.TGraph())
    
        for m_str in dict_dscb:
            systdict=dict_dscb[m_str]
            m = int(m_str)
    
            pars = []
            pars.append(systdict["nominal_alpha_l"])
            pars.append(systdict["nominal_alpha_h"])
            pars.append(systdict["nominal_n_l"])
            pars.append(systdict["nominal_n_h"])
            pars.append(systdict["nominal_mean"])
            pars.append(systdict["nominal_sigma"])
            pars.append(1)
    
            dscb = ROOT.TF1("dscb", doubleSidedCrystalBall, 0, 3000, 7)
            dscb.SetParameters(pars[0], pars[1], pars[2], pars[3], pars[4], pars[5], pars[6]) 
    
            acc = g_acceptance.Eval(m)
            xsec = f1_cross_section.Eval(m)
    
            for i,t in enumerate(mjj_thresholds):
                corr = getMjjCorrection(dscb, t)
                g_acceptance_mjj_corr[i].SetPoint(g_acceptance_mjj_corr[i].GetN(), m, corr*acc)
                g_xsec_times_acc[i].SetPoint(g_acceptance_mjj_corr[i].GetN(), m, xsec*acc*corr)
            g_xsec_times_acc[-1].SetPoint(g_acceptance_mjj_corr[-1].GetN(), m, xsec*acc)
    
        print("Writing to", output_files[k])
        fout = ROOT.TFile(output_files[k], "RECREATE")
        f1_cross_section.Write("f1_xsec")
        g_acceptance.Write("g_acc_mjj0")
        
        for i,t in enumerate(mjj_thresholds):
            g_acceptance_mjj_corr[i].Write("g_acc_mjj%d" % t)
            g_xsec_times_acc[i].Write("g_xsec_times_acc_mjj%d" % t)
        g_xsec_times_acc[-1].Write("g_xsec_times_acc_mjj0")
    
        fout.Close()
    

if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
