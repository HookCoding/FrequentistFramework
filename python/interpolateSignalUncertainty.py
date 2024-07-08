#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import ROOT
import sys, re, os, math, argparse
import color
import array
import json
from collections import OrderedDict

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")
ROOT.gROOT.SetBatch(True)

parnames = ["alpha_l", "alpha_h", "n_l", "n_h", "mean", "sigma"]

def main(args):
    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    parser.add_argument('--folder', dest='folder', type=str, default='signalUncertainty', help='Output folder to store results (default: signalUncertainty)')
    parser.add_argument('--infile', dest='infile', type=str, default='signalUncertainty.json', help='input json (default: signalUncertainty.json)')
    parser.add_argument('--doAtlasLabel', action="store_true", help='')
    parser.add_argument('--minmass', dest='minmass', type=float, default=350., help='Minimal signal mass to provide uncertainty for')
    parser.add_argument('--maxmass', dest='maxmass', type=float, default=1800., help='Maximal signal mass to provide uncertainty for')
    parser.add_argument('--spacing', dest='spacing', type=float, default=5., help='Spacing of output signal masses')
    args, paths = parser.parse_known_args(args)

    inname = os.path.join(args.folder,args.infile)
    outname_pulls = os.path.join(args.folder,args.infile.replace(".json","_overview"))
    outname_summed = os.path.join(args.folder,args.infile.replace(".json","_interpolated"))

    dict_pars = json.load(open(inname), object_pairs_hook=OrderedDict)
    # print(dict_pars)
    
    ROOT.SetAtlasStyle()

    # hists = [
    #    ["mjj_mR200_gSM0p1"],
    #    ["mjj_mR350_gSM0p1"],
    #    ["mjj_mR600_gSM0p1"],
    #    ["mjj_mR1000_gSM0p1"],
    #    ["mjj_mR2000_gSM0p1"],
    # ]

    hists = [
       ["mjj_mR200_gSM0p1_Scaled_1fb"],
       ["mjj_mR350_gSM0p1_Scaled_1fb"],
       ["mjj_mR600_gSM0p1_Scaled_1fb"],
       ["mjj_mR1000_gSM0p1_Scaled_1fb"],
       ["mjj_mR2000_gSM0p1_Scaled_1fb"],
    ]

    # Strong reduced JES, Simple JER:
    variations = [
       ["JET_OnlineOffline_NonClosure__1down"],
       ["JET_Flavor_Response__1down"],
       ["JET_Flavor_Composition__1down"],
       ["JET_EtaIntercalibration_TotalStat__1down"],
       ["JET_EtaIntercalibration_NonClosure_negEta__1down"],
       ["JET_EtaIntercalibration_NonClosure_posEta__1down"],
       ["JET_EtaIntercalibration_Modelling__1down"],
       ["JET_EtaIntercalibration_NonClosure_2018data__1down"],
       ["JET_EtaIntercalibration_NonClosure_highE__1down"],
       ["JET_EffectiveNP_1__1down"],
       ["JET_EffectiveNP_2__1down"],
       ["JET_EffectiveNP_3__1down"],
       ["JET_EffectiveNP_4__1down"],
       ["JET_EffectiveNP_5__1down"],
       ["JET_EffectiveNP_6__1down"],
       ["JET_EffectiveNP_7__1down"],
       ["JET_EffectiveNP_8restTerm__1down"],
       ["JET_Pileup_OffsetMu__1down"],
       ["JET_Pileup_RhoTopology__1down"],
       # ["JET_Pileup_OffsetNPV__1down"],
       ["JET_Pileup_PtTerm__1down"],
       ["JET_JER_EffectiveNP_1__1down"],
       ["JET_JER_EffectiveNP_2__1down"],
       ["JET_JER_EffectiveNP_3__1down"],
       ["JET_JER_EffectiveNP_4__1down"],
       ["JET_JER_EffectiveNP_5__1down"],
       ["JET_JER_EffectiveNP_6__1down"],
       ["JET_JER_EffectiveNP_7restTerm__1down"],
       # ["JET_JER_EffectiveNP_8__1down"],
       # ["JET_JER_EffectiveNP_9__1down"],
       # ["JET_JER_EffectiveNP_10__1down"],
       # ["JET_JER_EffectiveNP_11__1down"],
       # ["JET_JER_EffectiveNP_12restTerm__1down"],
       # ["JET_JER_DataVsMC_MC16__1down"],
       # ["JET_SingleParticle_HighPt__1down"],
       ["nominal"],
    ]

    variations.reverse()

    # c = ROOT.TCanvas("c", "c", 500, 800)
    c = ROOT.TCanvas("c", "c", 500, 600)
    # c.SetLogy()
    # c.Print(outname_pulls + ".pdf[")
    # ROOT.gPad.SetLeftMargin(0.52)
    ROOT.gPad.SetLeftMargin(0.62)
    ROOT.gPad.SetBottomMargin(0.08)

    g1_pars = {}
    g1_pars_sources = {}
    h1_sources_down = {}
    h1_sources_up = {}

    for p in parnames:
        g1_pars[p] = ROOT.TGraph()
        g1_pars_sources[p] = {}
        axistitle = p
        axistitle = axistitle.replace("mean", "#mu")
        axistitle = axistitle.replace("sigma", "#sigma")
        axistitle = axistitle.replace("alpha", "#alpha")
        axistitle = axistitle.replace("_l", "_{l}")
        axistitle = axistitle.replace("_h", "_{h}")

        h1_sources_down[p] = ROOT.TH1D("h1_sources_%s_down" % p, "-1#sigma;;Shift of %s [GeV]" % axistitle, len(variations)-1, 0, len(variations)-1)
        h1_sources_up[p]   = ROOT.TH1D("h1_sources_%s_up" % p,   "+1#sigma;;Shift of %s [GeV]" % axistitle, len(variations)-1, 0, len(variations)-1)

        for j,variation in enumerate(variations):
            if j==0:
                continue
            h1_sources_down[p].GetXaxis().SetBinLabel(j, variation[0].replace("__1down", ""))
            h1_sources_up[p].GetXaxis().SetBinLabel(j, variation[0].replace("__1down", ""))

        h1_sources_up[p].GetXaxis().SetLabelSize(15)
        h1_sources_up[p].GetXaxis().SetLabelOffset(0.01)
        h1_sources_up[p].GetYaxis().SetLabelSize(15)
        h1_sources_up[p].GetYaxis().SetTitleSize(15)
        h1_sources_up[p].GetYaxis().SetNdivisions(505)
        h1_sources_up[p].SetLineColor(ROOT.kBlue)
        h1_sources_up[p].SetFillColor(ROOT.kBlue)
        h1_sources_up[p].SetFillStyle(3245)
        h1_sources_down[p].GetXaxis().SetLabelSize(15)
        h1_sources_down[p].GetXaxis().SetLabelOffset(1.1)
        h1_sources_down[p].SetLineColor(ROOT.kRed)
        h1_sources_down[p].SetFillColor(ROOT.kRed)
        h1_sources_down[p].SetFillStyle(3254)

    for i,hist in enumerate(hists):
        dict_pars1 = dict_pars[hist[0]]
        diff_par = {}

        searchstring =r'_mR(\d+)_'
        res=re.search(searchstring, hist[0])
        m=int(res.group(1))

        for ip,parname in enumerate(parnames):
            h1_sources_up[parname].Reset("M")
            h1_sources_down[parname].Reset("M")
            for j,variation in enumerate(variations):
                pars = dict_pars1[variation[0]]
                par_val = pars[ip]
                if j == 0:
                    par_nominal = par_val
                    if not variation[0] in g1_pars_sources[parname]:
                        g1_pars_sources[parname][variation[0]] = ROOT.TGraph()
                    g1_pars_sources[parname][variation[0]].SetPoint(g1_pars_sources[parname][variation[0]].GetN(), m, par_nominal)
                else:
                    par_down = par_val

                    pars_up = dict_pars1[variation[0].replace("1down", "1up")]
                    par_up = pars_up[ip]
                    
                    diff_par_up = par_up - par_nominal
                    diff_par_down = par_down - par_nominal

                    # diff_par_avg = 0.5*(abs(diff_par_up) + abs(diff_par_down))
                    # diff_width_avg = 0.5*(abs(diff_width_up) + abs(diff_width_down))
                    sign = 1.
                    if abs(diff_par_up) > abs(diff_par_down):
                        # take sign of diff_par_up
                        sign = 1. if diff_par_up > 0 else -1.
                    else:
                        # take sign of diff_par_down
                        sign = -1. if diff_par_down > 0 else 1.

                    diff_par_avg = sign*max(abs(diff_par_up), abs(diff_par_down))
                    
                    if not variation[0] in g1_pars_sources[parname]:
                        g1_pars_sources[parname][variation[0]] = ROOT.TGraph()
                    g1_pars_sources[parname][variation[0]].SetPoint(g1_pars_sources[parname][variation[0]].GetN(), m, diff_par_avg)
                    # print(g1_pars_sources[p])

                    if not parname in diff_par:
                        diff_par[parname] = []
                    diff_par[parname].append(diff_par_avg)

                    h1_sources_up[parname].SetBinContent(j, diff_par_up)
                    h1_sources_down[parname].SetBinContent(j, diff_par_down)

                    # print(hist, variation)
                    # print("%s:" % parname, par_nominal, par_up, par_down, diff_par_up, diff_par_down, diff_par_avg)
                    
        c.Print(outname_pulls + "_mR%d.pdf[" % m)
        for ip,parname in enumerate(parnames):
            ROOT.gStyle.SetHistMinimumZero()
            ymin=min(h1_sources_up[parname].GetMinimum(),h1_sources_down[parname].GetMinimum())
            ymax=max(h1_sources_up[parname].GetMaximum(),h1_sources_down[parname].GetMaximum())
            h1_sources_up[parname].Draw("hbar")
            h1_sources_up[parname].GetYaxis().SetRangeUser(ymin - 0.1*(ymax-ymin), ymax + 0.1*(ymax-ymin))
            h1_sources_down[parname].Draw("hbar same")

            # leg = ROOT.gPad.BuildLegend(0.83,0.86,0.98,0.92, "", "f")
            leg = ROOT.gPad.BuildLegend(0.82,0.10,1.0,0.16, "", "f")
            leg.SetFillStyle(0)
            
            ROOT.gStyle.SetTextSize(15)
            ROOT.gStyle.SetLegendTextSize(15)

            if args.doAtlasLabel:
                ROOT.ATLASLabel(0.317, 0.125, "Work in progress", 13)
                ROOT.myText(0.59, 0.150, 1, "m_{Z'} = %d GeV, g_{q} = 0.1" % m, 33)
            else:
                # ROOT.myText(0.59, 0.125, 1, "m_{Z'} = %d GeV, g_{q} = 0.1" % m, 33)
                ROOT.myText(0.606, 0.045, 1, "m_{Z'} = %d GeV, g_{q} = 0.1" % m, 33)

            c.Print(outname_pulls + "_mR%d.pdf" % m)
        
            if len(diff_par) > 0:
                unc_par = math.sqrt(sum([x*x for x in diff_par[parname]]))
                g1_pars[parname].SetPoint(i, m, unc_par)

        # input("wait")
        c.Print(outname_pulls+"_mR%d.pdf]" % m)
    # c.Print(outname_pulls+".pdf]")

    fout = ROOT.TFile(outname_summed+".root","RECREATE")
    c2 = ROOT.TCanvas("c2", "c2", 800, 600)
    c2.Print(outname_summed+".pdf[")

    for parname in parnames:
        axistitle = parname
        axistitle = axistitle.replace("mean", "#mu")
        axistitle = axistitle.replace("sigma", "#sigma")
        axistitle = axistitle.replace("alpha", "#alpha")
        axistitle = axistitle.replace("_l", "_{l}")
        axistitle = axistitle.replace("_h", "_{h}")

        g1_pars[parname].Draw("ALP")
        g1_pars[parname].GetXaxis().SetTitle("m_{R} [GeV]")
        g1_pars[parname].GetYaxis().SetTitle("Uncertainty on %s [GeV]" % axistitle)
        ROOT.gPad.Update()
        c2.Print(outname_summed+".pdf")

        g1_pars[parname].Write("g1_uncertainty_on_%s" % parname)

    c2.Print(outname_summed+".pdf]")
    fout.Close()

    dict_out = OrderedDict()
    for m in range(args.minmass, args.maxmass, args.spacing):
        dict_tmp = OrderedDict()
        for parname in parnames:
            par_interp = g1_pars[parname].Eval(m)
            
            dict_tmp["unc_%s" % parname] = par_interp
            dict_tmp_tmp = OrderedDict()
            # print(g1_pars_sources[parname])
            for variation in variations:
                par_source_interp = g1_pars_sources[parname][variation[0]].Eval(m)
                if "nominal" in variation:
                    dict_tmp["nominal_%s" % parname] = par_source_interp
                else:
                    dict_tmp_tmp[variation[0].replace("__1down", "")] = par_source_interp
            dict_tmp["unc_%s_sources" % parname] = dict_tmp_tmp

        dict_out[m] = dict_tmp
        
    with open(outname_summed+".json", 'w') as f:
        json.dump(dict_out, f, indent=2)


if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
