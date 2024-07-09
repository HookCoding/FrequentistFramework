#!/usr/bin/env python
from __future__ import print_function

import ROOT
import sys, re, os, math, optparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
import ExtractFitParameters as efp
from InjectGaussian import GetNsig
import numpy
import json
from color import getColorSteps

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")



def main(args):
    SetAtlasStyle()

    parser = optparse.OptionParser(description='%prog [options] INPUT')
    parser.add_option('--outfile', dest='outfile', type=str, default='BHGraphs.root', help='Output file name')
    # parser.add_option('--pdhist', dest='pdhist', type=str, default='unfluctuated_injection', help='Data hist name in Pseudodata file')
    # parser.add_option('--postfithist', dest='postfithist', type=str, default='J100yStar06/data', help='Data hist name in PostFit file')
    parser.add_option('--notoys', dest='notoys', action='store_true', help='Use one fit instead of many toys')
    parser.add_option('--maxN', dest='maxN', type=int, default=1e100, help='Only consider first N toys.')

    
    options, args = parser.parse_args(args)

    paths = args
    sigmeans = set()
    sigwidths = set()
    sigamps = set()
    dict_file = {}
    
    if paths[0].endswith(".txt"):
        print("Assuming file list input.")
        filelists = paths
        paths = []
        for fl in filelists:
            with open(fl, 'r') as f:
                paths += f.read().splitlines()

    for p in paths:
        res=re.findall(r'mean(\d+)_width(\d+)(:?_amp\d+)?', p)[-1]
        m=int(res[0])
        w=int(res[1])
        
        sigmeans.add(m)
        sigwidths.add(w)

        try:
            a=int(res[2][4:])
        except:
            a=0
        sigamps.add(a)
            
        if (m, w, a) in dict_file:
            dict_file[(m, w, a)].append(p)
        else:
            dict_file[(m, w, a)]=[p]
            
    sigmeans = list(sigmeans)
    sigwidths = list(sigwidths)
    sigamps = list(sigamps)

    sigmeans.sort()
    sigwidths.sort()
    sigamps.sort(reverse=True)

    colors = getColorSteps(len(sigmeans)*len(sigwidths))

    fout = TFile(options.outfile, "RECREATE")
    fouthists = TFile(options.outfile.replace(".root", "hists.root"), "RECREATE")

    profile_list = []
    allPoints_list = []

    for j,sigmean in enumerate(sigmeans):
        
        for i,sigwidth in enumerate(sigwidths):

            g_allPvals = TGraph()
            g_profilePvals   = TGraphErrors()
            g_allLocPvals = TGraph()
            g_profileLocPvals   = TGraphErrors()
            g_allWinMin = TGraph()
            g_allWinMax = TGraph()
            sqrtB = None

            h1_pvals = ROOT.TH1D("h1_pvals_mean%d_width%d" % (sigmean, sigwidth), "h1_pvals_mean%d_width%d" % (sigmean, sigwidth), 100, 0,1)

            for k,sigamp in enumerate(sigamps):
    
                try:
                    tmp_path_fitresult = dict_file[(sigmean, sigwidth, sigamp)]
                except:
                    print("WARNING: No fitresult file for", sigmean, sigwidth, sigamp)
                    continue

                #find number of injected events:
                # if sigamp > 0:
                #     # tmp_path_injection = tmp_path_fitresult[0].replace("FitResult", "PD")
                #     try:
                #         tmp_path_injection = glob(os.path.join(os.path.dirname(tmp_path_fitresult[0]),"*_injected_mean*_width*_amp*.root"))[0]
                #         # print("PD path:", tmp_path_injection)
                #         f = TFile(tmp_path_injection)
                #         h = f.Get(options.pdhist)
                #         n_injected = h.Integral(0, h.GetNbinsX()+1)
                #         f.Close()
                #     except:
                #         try:
                #             tmp_path_postfit = dict_file[(sigmean, sigwidth, sigamp)][0].replace("BHResult", "PostFit").replace(".json", ".root")
                #             # print("Postfit path:", tmp_path_injection)
                #             f = TFile(tmp_path_postfit)
                #             h = f.Get(options.postfithist)
                #             n_injected = GetNsig(h, sigmean, sigwidth, sigamp)
                #             f.Close()
                #         except Exception as e:
                #             print("WARNING: Could not find injection file for %s. Using n_injected=0 now." % dict_file[(m, w, a)][0])
                #             print(e)
                #             n_injected = 0
                # else:
                #     n_injected = 0
                
                nans = 0

                pvals = []
                locpvals = []
                win_min = []
                win_max = []
        
                for l,path in enumerate(tmp_path_fitresult):
                    if l>=options.maxN:
                        break
                    try:
                        with open(path) as f:
                            BHresults=json.load(f)

                            p = BHresults["pyBHresult"]["global_Pval"]
                            pvals.append(p)

                            locp = BHresults["pyBHresult"]["min_Pval_ar"][0]
                            locpvals.append(locp)

                            wmin = BHresults["MaskMin"]
                            wmax = BHresults["MaskMax"]
                            win_min.append(wmin)
                            win_max.append(wmax)
                    except Exception as e:
                        print("Couldn't read BH pval from", path)
                        print(e)
                        # return -1
                        continue

                for p in pvals:
                    g_allPvals.SetPoint(g_allPvals.GetN(), sigamp, p)
                    if sigamp == 0:
                        h1_pvals.Fill(p)

                for p in locpvals:
                    g_allLocPvals.SetPoint(g_allPvals.GetN(), sigamp, p)

                for w in win_min:
                    g_allWinMin.SetPoint(g_allWinMin.GetN(), sigamp, w)

                for w in win_max:
                    g_allWinMax.SetPoint(g_allWinMax.GetN(), sigamp, w)

                # if sqrtB == None:
                #     try:
                #         sqrtB = (n_injected / sigamp) if sigamp != 0 else 1
                #     except:
                #         sqrtB = 1
                    
                if not options.notoys:
                    arr = numpy.array([p for p in pvals])
                    nFit = numpy.mean(arr)
                    nFitErr = numpy.std(arr, ddof=1) #1/N-1 corrected
                                        
                    g_profilePvals.SetPoint(g_profilePvals.GetN(), sigamp, nFit)
                    g_profilePvals.SetPointError(g_profilePvals.GetN()-1, 0, nFitErr)

                    arr = numpy.array([p for p in locpvals])
                    nFit = numpy.mean(arr)
                    nFitErr = numpy.std(arr, ddof=1) #1/N-1 corrected
                                        
                    g_profileLocPvals.SetPoint(g_profileLocPvals.GetN(), sigamp, nFit)
                    g_profileLocPvals.SetPointError(g_profileLocPvals.GetN()-1, 0, nFitErr)
    
                else:
                    g_profilePvals.SetPoint(g_profilePvals.GetN(), sigamp, p)
                    g_profilePvals.SetPointError(g_profilePvals.GetN()-1, 0, 0.)

            fouthists.cd()
            h1_pvals.Write()
                        
            fout.cd()
            g_allPvals.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_allPvals.Write("g1_BHpval_gauss_%d_%d" % (sigmean, sigwidth))
            
            g_profilePvals.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_profilePvals.Write("g1_profile_gauss_%d_%d" % (sigmean, sigwidth))

            g_allLocPvals.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_allLocPvals.Write("g1_BHlocalpval_gauss_%d_%d" % (sigmean, sigwidth))

            g_allWinMin.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_allWinMin.Write("g1_BHWinMin_gauss_%d_%d" % (sigmean, sigwidth))

            g_allWinMax.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_allWinMax.Write("g1_BHWinMax_gauss_%d_%d" % (sigmean, sigwidth))

            allPoints_list.append(g_allPvals)
            profile_list.append(g_profilePvals)

    fout.Close()

    # Plotting:
    c = TCanvas()
    c.SetLogy()
    mg = TMultiGraph()

    for i,g in enumerate(profile_list):
        g.SetLineWidth(2)
        g.SetLineColor(colors[i])
        g.SetMarkerColor(colors[i])
        mg.Add(g, "")

    mg.Draw("APL")
    mg.GetXaxis().SetTitle("Injected N_{sig} / #sqrt{N_{bkg}}")
    mg.GetYaxis().SetTitle("Global p(BH)")
    mg.GetXaxis().SetLimits(-0.5, 6)
    # mg.GetYaxis().SetLimits(-0.5, 15)
    mg.SetMinimum(1.e-4)
    mg.SetMaximum(1)
    c.Update()

    c.BuildLegend(0.2,0.54,0.5,0.78)

    l = TLine(-0.5,-0.5,6,6)
    l.SetLineColor(kGray+2)
    l.SetLineStyle(7)
    l.Draw()

    lumi = 29.5
    # if "lumi" in dict_file.values()[0]:
    if "lumi" in list(next(iter(list(dict_file.items()))))[0]:
        try:
            # lumi=int(dict_file.values()[0].split("lumi")[-1].split("_")[0])
            lumi=int(list(next(iter(list(dict_file.items()))))[0].split("lumi")[-1].split("_")[0])
        except:
            pass
    text1 = "Pseudodata %d fb^{-1}" % lumi

    text2 = "global fit"
    # if "four" in  dict_file.values()[0]:
    #     text2 += " 4 par"
    # if "five" in  dict_file.values()[0]:
    #     text2 += " 5 par"
    # if "nloFit" in dict_file.values()[0]:
    #     text2 = "NLOFit"
    # text2="NLOFit"

    text = text1 + ", " + text2

    ATLASLabel(0.2, 0.9, "   Work in progress", 13)
    myText(0.2, 0.82, 1, text)

    # raw_input("enter")

    c.Print(options.outfile.replace(".root", ".png"))
    
if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))   

