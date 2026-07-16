#!/usr/bin/env python
import ROOT
import sys, re, os, math, optparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

lumi = 130000

def main(args):
    SetAtlasStyle()
 
    parser = optparse.OptionParser(description='%prog [options] INPUT')
    parser.add_option('--outfile', dest='outfile', type=str, default='limitGraphs.root', help='Output file name')
    
    options, args = parser.parse_args(args)

    paths = args
    sigmeans = set()
    sigwidths = set()
    sigamps = set()
    dict_file = {}

    for p in paths:
        res=re.search(r'mean(\d+)_width(\d+)(:?_amp\d+)?', p)
        m=int(res.group(1))
        w=int(res.group(2))
        
        sigmeans.add(m)
        sigwidths.add(w)

        try:
            a=int(res.group(3)[4:])
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
    sigamps.sort()

    colors = [kBlue, kRed+1, kOrange-3]

    fout = TFile(options.outfile, "RECREATE")

    for i,sigwidth in enumerate(sigwidths):
        
        for j,sigmean in enumerate(sigmeans):
            
            g = TGraph()
            g_exp = TGraph()
            g_exp_2u = TGraph()
            g_exp_1u = TGraph()
            g_exp_1d = TGraph()
            g_exp_2d = TGraph()
            sqrtB = None

            for k,sigamp in enumerate(sigamps):
    
                #find number of injected events:
              
                try:
                    tmp_path_limits = dict_file[(sigmean, sigwidth, sigamp)]
                except:
                    print "WARNING: No limit file for", sigmean, sigwidth, sigamp
                    continue

                if sigamp > 0:
                    tmp_path_injection = tmp_path_limits.replace("Limits", "PD").replace(".txt", ".root")

                    try:
                        f = TFile(tmp_path_injection[0])
                        h = f.Get("pseudodata_0_injection")
                        n_injected = h.Integral(0, h.GetNbinsX()+1)
                        f.Close()
                    except:
                        print "WARNING: Could not find injection file for tmp_path_limits. Using n_injected=0 now."
                        n_injected = 0
                else:
                    n_injected = 0

                if sqrtB == None:
                    sqrtB = (n_injected / sigamp) if sigamp != 0 else 1
                    # print "setting sqrtB to", sqrtB
                
                inj_limit = []
                nans = 0

                for path in tmp_path_limits:
                    with open(path) as f:
                        limits = f.readline().split()
                        limit = float(limits[0])
                        limit_exp = float(limits[1])
                        limit_exp2u = float(limits[2])
                        limit_exp1u = float(limits[3])
                        limit_exp1d = float(limits[4])
                        limit_exp2d = float(limits[5])
                        
                    # print n_injected, limit
                    inj_limit.append((n_injected, limit, limit_exp, limit_exp2u, limit_exp1u, limit_exp1d, limit_exp2d))
                    if math.isnan(limit):
                        nans += 1
                
                print "n_injected: %d,   NaNs: %d" % (n_injected, nans)
                # if float(nans) / len(inj_limit) < 0.02:
                for t in inj_limit:
                    g.SetPoint(g.GetN(), t[0]/sqrtB, t[1]/sqrtB)
                    g_exp.SetPoint(g_exp.GetN(), t[0]/sqrtB, t[2]/sqrtB)
                    g_exp_2u.SetPoint(g_exp_2u.GetN(), t[0]/sqrtB, t[3]/sqrtB)
                    g_exp_1u.SetPoint(g_exp_1u.GetN(), t[0]/sqrtB, t[4]/sqrtB)
                    g_exp_1d.SetPoint(g_exp_1d.GetN(), t[0]/sqrtB, t[5]/sqrtB)
                    g_exp_2d.SetPoint(g_exp_2d.GetN(), t[0]/sqrtB, t[6]/sqrtB)
                # else:
                #     print "skipping", inj_limit[0][0], "due to NaNs"
   
            fout.cd()

            g.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g.Write("g1_limit_gauss_%d_%d" % (sigmean, sigwidth))

            g_exp.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_exp.Write("g1_exp_limit_gauss_%d_%d" % (sigmean, sigwidth))

            g_exp_2u.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_exp_2u.Write("g1_exp_2u_limit_gauss_%d_%d" % (sigmean, sigwidth))

            g_exp_1u.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_exp_1u.Write("g1_exp_1u_limit_gauss_%d_%d" % (sigmean, sigwidth))

            g_exp_1d.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_exp_1d.Write("g1_exp_1d_limit_gauss_%d_%d" % (sigmean, sigwidth))

            g_exp_2d.SetTitle("%d GeV Gauss (%d%%)" % (sigmean, sigwidth))
            g_exp_2d.Write("g1_exp_2d_limit_gauss_%d_%d" % (sigmean, sigwidth))


    fout.Close()

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
