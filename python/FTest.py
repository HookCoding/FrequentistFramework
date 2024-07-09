#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import ROOT
import sys, re, os, math, argparse
from color import getColorSteps, getFillStyle, getColors

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

def calcFpF(chi2_nom, chi2_alt, npars_nom, npars_alt, nbins, zerochi2):
    F_num = (chi2_nom - chi2_alt) / (npars_alt - npars_nom)
    F_den = chi2_alt / (nbins - npars_alt)
    if zerochi2:
        F_den += 1

    F = F_num / F_den
    pF = ROOT.Math.fdistribution_cdf_c( F, npars_alt-npars_nom, nbins-npars_alt)

    return (F, pF)

def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    parser.add_argument('--chi2hist', dest='chi2hist', type=str, default="chi2", help='name of the chi2 hist')
    parser.add_argument('--residualshist', dest='residualshist', type=str, default="residuals", help='name of the residuals hist')
    parser.add_argument('--chi2bin', dest='chi2bin', type=int, default=1, help='bin of the chi2 value in the chi2 histogram')
    parser.add_argument('--nbinsbin', dest='nbinsbin', type=int, default=3, help='bin of the nbins value in the chi2 histogram')
    parser.add_argument('--nparsbin', dest='nparsbin', type=int, default=4, help='bin of the npars value in the chi2 histogram')
    parser.add_argument('--ndofbin', dest='ndofbin', type=int, default=5, help='bin of the npars value in the chi2 histogram')
    parser.add_argument('--pvalbin', dest='pvalbin', type=int, default=6, help='bin of the pval value in the chi2 histogram')
    parser.add_argument('--usendof', dest='usendof', action='store_true', help='use npar=nbins-ndof instead of number in chi2 histogram')
    parser.add_argument('--zerochi2', dest='zerochi2', action='store_true', help='use when fitting unfluctuated data')
    parser.add_argument('--noftest', dest='noftest', action='store_true', help='only plot residuals and dont perform F-Test')
    parser.add_argument('--output', dest='output', type=str, default='FTest',help='name of output plot, extension will be added.')
    parser.add_argument('--legend', dest='legend', type=str, nargs='+', default=None, help='texts to show up in legend')
    parser.add_argument('--doatlaslabel', dest='doatlaslabel', action='store_true', help='add ATLAS label to the plot')

    options, args = parser.parse_known_args(args)

    paths = args

    # l_pf = []
    l_res = []
    l_chi2 = []
    l_npars = []
    l_ndof = []
    l_pval = []
    l_nbins = []

    for p in paths:
        f = ROOT.TFile(p)

        try:
            h_chi2 = f.Get(options.chi2hist)
        except:
            pass
        # h_pf   = f.Get(options.postfithist)
        h_res  = f.Get(options.residualshist)
        
        # h_pf.SetDirectory(0)
        h_res.SetDirectory(0)

        try:
            chi2  = h_chi2.GetBinContent(options.chi2bin)
            nbins = h_chi2.GetBinContent(options.nbinsbin)
            if len(l_nbins) > 0 and nbins != l_nbins[-1]:
                print("WARNING: Change of binning between files: %d, %d ." % (l_nbins[-1], nbins))
            #     return -1
            # else:
                
            if not options.usendof:
                npars = h_chi2.GetBinContent(options.nparsbin)
            else:
                npars = h_chi2.GetBinContent(options.nbinsbin) - h_chi2.GetBinContent(options.ndofbin)

            ndof = h_chi2.GetBinContent(options.ndofbin)
            pval = h_chi2.GetBinContent(options.pvalbin)
        except:
            chi2=0
            npars=0
            ndof=0
            pval=0
            nbins=0

        # l_pf.append(h_pf)
        l_res.append(h_res)
        l_chi2.append(chi2)
        l_npars.append(npars)
        l_ndof.append(ndof)
        l_pval.append(pval)
        l_nbins.append(nbins)

    colors = getColorSteps(len(paths))
    # colors = getColors()
    c = ROOT.TCanvas("c","c",800,600)
    c.SetGridy()

    leg = ROOT.TLegend(0.185,0.75,0.925,0.92)
    leg.SetNColumns(2)
    leg.SetTextSize(20)
    
    l_constr=[]
    l_par=[]

    for i in range(len(l_res)):
        h=l_res[i]

        h.SetMarkerColor(colors[i])
        h.SetLineColor(colors[i])
        h.SetFillColor(colors[i])
        h.SetFillStyle(getFillStyle(i))
        
        h.GetXaxis().SetTitle("m_{jj} [GeV]")
        h.GetXaxis().SetNdivisions(505)
        # h.GetYaxis().SetTitle("Residuals [#sigma]")
        h.GetYaxis().SetTitle("Significance")
        h.GetYaxis().SetTitleOffset(1.0)

        if options.zerochi2:
            h.SetMinimum(-1.1)
            h.SetMaximum(1.1)
            
        else:
            # h.SetMinimum(-4.2)
            # h.SetMaximum(5.9)

            if options.noftest:
                # h.SetMinimum(-3.49)
                h.SetMinimum(-3.99)
                # h.SetMaximum(6.49)
                h.SetMaximum(5.49)
            else:
                # h.SetMinimum(-5.25)
                # h.SetMaximum(6.75)
                h.SetMinimum(-5.0)
                h.SetMaximum(7.0)

        h.Draw("same")

        string_masked = ""
        if "_masked" in paths[i]:
            string_masked = " (masked)"

        if "pileupscale" in paths[i].lower():
            legtext="#splitline{pile-up scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "etajesscale" in paths[i].lower():
            legtext="#splitline{MCJES scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "gscscale_tile0" in paths[i].lower():
            legtext="#splitline{GSC_{Tile0} scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "gscscale_em3" in paths[i].lower():
            legtext="#splitline{GSC_{EM3} scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "gscscale_n90" in paths[i].lower():
            legtext="#splitline{GSC_{N90} scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "gscscale_tilegap3" in paths[i].lower():
            legtext="#splitline{GSC_{TG3} scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "gscscale" in paths[i].lower():
            legtext="#splitline{GSC scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "insituscale" in paths[i].lower():
            legtext="#splitline{in-situ scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
        elif "gencorrscale" in paths[i].lower():
            if "2016" in paths[i].lower():
                legtext="#splitline{on-off scale (2016)}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
            elif "less_smooth_2017" in paths[i].lower():
                legtext="#splitline{on-off scale (2017 LS)}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
            elif "2017" in paths[i].lower():
                legtext="#splitline{on-off scale (2017)}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
            elif "less_smooth_2018" in paths[i].lower():
                legtext="#splitline{on-off scale (2018 LS)}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
            elif "2018" in paths[i].lower():
                legtext="#splitline{on-off scale (2018)}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
            else:
                legtext="#splitline{on-off scale}{#chi^{2}/n = %.1f/%.1f, p = %.2f}" % (l_chi2[i], l_ndof[i], l_pval[i])
            
        elif "nlofit" in paths[i].lower():
            res=re.search(r'constr(\d+)_', paths[i])
            constr=int(res.group(1))
            l_constr.append(constr)

            legtext = "#splitline{NLOFit, #sigma = %d%s}{#chi^{2}/n = %.1f/%.1f, p = %.3f}" % (constr, string_masked, l_chi2[i], l_ndof[i], l_pval[i]) 

        elif "anafit" in paths[i].lower() or "globalfit" in paths[i].lower() or "swift" in paths[i].lower() or "par" in paths[i].lower():
            if "four" in paths[i].lower():
                p=4
            elif "five" in paths[i].lower():
                p=5
            elif "six" in paths[i].lower():
                p=6
            elif "seven" in paths[i].lower():
                p=7
            elif "eight" in paths[i].lower():
                p=8
            elif "nine" in paths[i].lower():
                p=9
            else:
                searchstring =r'(\d+)Par'
                res=re.search(searchstring, paths[i])
                p=int(res.group(1))

            yearstring = ""
            if "data16" in  paths[i].lower():
                yearstring = " (data 16)"
            elif "data17" in  paths[i].lower():
                yearstring = " (data 17)"
            elif "data18" in  paths[i].lower():
                yearstring = " (data 18)"
            elif "dataall" in  paths[i].lower():
                yearstring = " (Full Run-2)"
            
            if l_ndof[i] != 0:
                legtext = "#splitline{%d-par fit%s}{#chi^{2}/n = %.1f/%.0f, p = %.3f}" % (p, string_masked + yearstring, l_chi2[i], l_ndof[i], l_pval[i]) 
                # if options.legend != None:
                #     legtext = "%s, p = %.2f" % (options.legend[i], l_pval[i]) 
                # else:
                #     legtext = "%d-par fit, p = %.2f" % (p, l_pval[i]) 
            else:
                legtext = "%d-par fit" % p
            l_par.append(p)

        leg.AddEntry(h, legtext, "f")

    if not options.noftest:
    
        box1 = ROOT.TPave(0.185,0.18,0.925,0.25,0,"NDC")
        box1.SetFillStyle(1001)
        box1.SetFillColor(ROOT.kWhite)
        box1.SetLineWidth(0)
        box1.Draw()

        leg2 = ROOT.TLegend(0.185,0.18,0.925,0.30)
            
        leg2.SetNColumns(2)
        leg2.SetTextSize(21)
        leg2.SetFillStyle(0)

        print(l_chi2)
        print(l_par)
        for i in range(len(l_chi2)-1):
            
            print("\nF-Test between:", paths[i], paths[i+1])
            print("chi2 values:", l_chi2[i], l_chi2[i+1])
            print("npars:", l_npars[i], l_npars[i+1])
            print("nbins:", l_nbins[i])

            if l_nbins[i] != l_nbins[i+1]:
                F=float("nan")
                pF=float("nan")
            else:
                try:
                    (F, pF) = calcFpF( chi2_nom=l_chi2[i], 
                                       chi2_alt=l_chi2[i+1], 
                                       npars_nom=l_npars[i], 
                                       npars_alt=l_npars[i+1], 
                                       nbins=l_nbins[i], 
                                       zerochi2=options.zerochi2 )
                except:
                    F=float("nan")
                    pF=float("nan")
                
            print("F:", F)
            print("pF:", pF)

            if math.isnan(pF):
                leg2.AddEntry(0, " ", "")
            else:
                if "nlofit" in paths[i].lower():
                    # leg2.AddEntry(0, "p(F_{^{#sigma: %d #rightarrow %d}}) = %.2f" % (l_constr[i], l_constr[i+1], pF), "")
                    leg2.AddEntry(0, "p(F#lower[0.4]{#scale[0.8]{#sigma: %d #rightarrow %d}}) = %.3f" % (l_constr[i], l_constr[i+1], pF), "")
                elif "anafit" in paths[i].lower() or "globalfit" in paths[i].lower() or "swift" in paths[i].lower():
                    # leg2.AddEntry(0, "p(F_{^{%d #rightarrow %d par}}) = %.2f" % (l_par[i], l_par[i+1], pF), "")
                    leg2.AddEntry(0, "p(F#lower[0.4]{#scale[0.8]{%d #rightarrow %d par}}) = %.3f" % (l_par[i], l_par[i+1], pF), "")
                    
        if not options.doatlaslabel:
            if "j50" in paths[i].lower():
                # lumi="J50 data, 15.0 fb^{-1}"
                # lumi="#sqrt{s}=13 TeV, 15.0 fb^{-1} data"
                if "partial" in paths[i].lower():
                    lumi="J50 SR, 1.5 fb^{-1}"
                else:
                    lumi="J50 SR, 15.0 fb^{-1}"
            else:
                # lumi="J100 data, 132 fb^{-1}"
                # lumi="#sqrt{s}=13 TeV, 132 fb^{-1} data"
                if "partial" in paths[i].lower():
                    lumi="J100 SR, 29.5 fb^{-1}"
                else:
                    lumi="J100 SR, 132 fb^{-1}"
            if "nlofit" in paths[i].lower():
                label = "NLOFit, %s" % lumi 
            else:
                label = "Functional form fit, %s" % lumi 
                
            leg2.AddEntry(0, lumi, "")
    
        leg2.Draw()
    else:
        if "partial" in paths[i].lower():
            text1="Partial data, 6-par fit"
        elif "jzw" in paths[i].lower():
            text1="Pythia MC, 6-par fit"
        else:
            text1="Run-2 data, 6-par fit"
        # text2="GSC enabled, original on-off"
        # box = ROOT.TPave(0.60,0.19,0.925,0.29,0,"NDC");
        # text2="GSC disabled, rederived on-off"
        text2="N90 disabled, on-off FW75%max"
        box = ROOT.TPave(0.55,0.19,0.925,0.29,0,"NDC");
        box.SetFillStyle(1001)
        box.SetFillColor(ROOT.kWhite)
        box.SetLineWidth(0)
        box.Draw()

        ROOT.myText(0.92,0.20, 1, text1, 31, 21) # bottom right aligned, same size as legend
        ROOT.myText(0.92,0.25, 1, text2, 31, 21) # bottom right aligned, same size as legend
        

    leg.Draw()
    c.Update()

    if options.doatlaslabel:
        ROOT.ATLASLabel(0.57, 0.19, "Work in progress", 11)
        
    # input("press enter")

    c.Print(options.output + ".svg")
    c.Print(options.output + ".pdf")
        
        
if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))   
