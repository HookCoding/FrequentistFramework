#!/usr/bin/env python
import ROOT
import sys, re, os, math, optparse
from color import getColorSteps

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

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

    parser = optparse.OptionParser(description='%prog [options] INPUT')
    parser.add_option('--chi2hist', dest='chi2hist', type=str, default="chi2", help='name of the chi2 hist')
    parser.add_option('--residualshist', dest='residualshist', type=str, default="residuals", help='name of the residuals hist')
    parser.add_option('--chi2bin', dest='chi2bin', type=int, default=1, help='bin of the chi2 value in the chi2 histogram')
    parser.add_option('--nbinsbin', dest='nbinsbin', type=int, default=3, help='bin of the nbins value in the chi2 histogram')
    parser.add_option('--nparsbin', dest='nparsbin', type=int, default=4, help='bin of the npars value in the chi2 histogram')
    parser.add_option('--ndofbin', dest='ndofbin', type=int, default=5, help='bin of the npars value in the chi2 histogram')
    parser.add_option('--usendof', dest='usendof', action='store_true', help='use npar=nbins-ndof instead of number in chi2 histogram')
    parser.add_option('--zerochi2', dest='zerochi2', action='store_true', help='use when fitting unfluctuated data')
    parser.add_option('--output', dest='output', type=str, default='FTest',help='name of output plot, extension will be added.')

    options, args = parser.parse_args(args)

    paths = args

    # l_pf = []
    l_res = []
    l_chi2 = []
    l_npars = []
    l_ndof = []
    nbins = -1

    for p in paths:
        f = ROOT.TFile(p)

        h_chi2 = f.Get(options.chi2hist)
        # h_pf   = f.Get(options.postfithist)
        h_res  = f.Get(options.residualshist)
        
        # h_pf.SetDirectory(0)
        h_res.SetDirectory(0)

        chi2  = h_chi2.GetBinContent(options.chi2bin)
        _nbins = h_chi2.GetBinContent(options.nbinsbin)
        if nbins > 0 and _nbins != nbins:
            print "ERROR: Change of binning between files: %d, %d . Exiting" % (nbins, _nbins)
            return -1
        else:
            nbins = _nbins

        if not options.usendof:
            npars = h_chi2.GetBinContent(options.nparsbin)
        else:
            npars = h_chi2.GetBinContent(options.nbinsbin) - h_chi2.GetBinContent(options.ndofbin)

        ndof = h_chi2.GetBinContent(options.ndofbin)

        # l_pf.append(h_pf)
        l_res.append(h_res)
        l_chi2.append(chi2)
        l_npars.append(npars)
        l_ndof.append(ndof)


    colors = getColorSteps(len(paths))
    c = ROOT.TCanvas("c","c",800,600)

    leg = ROOT.TLegend(0.18,0.70,0.90,0.90)
    leg.SetNColumns(2)
    leg.SetTextSize(21)
    
    leg2 = ROOT.TLegend(0.18,0.18,0.90,0.30)
    leg2.SetNColumns(2)
    leg2.SetTextSize(21)

    l_constr=[]
    l_par=[]

    for i in range(len(l_res)):
        h=l_res[i]

        h.SetMarkerColor(colors[i])
        h.SetLineColor(colors[i])
        h.SetFillColor(colors[i])
        h.SetFillStyle(3245)
        
        h.GetXaxis().SetTitle("m_{jj} [GeV]")
        # h.GetXaxis().SetNdivisions(505)
        h.GetYaxis().SetTitle("Residuals [#sigma]")

        h.SetMinimum(-4.2)
        h.SetMaximum(5.2)

        h.Draw("same")

        if "nlofit" in paths[i].lower():
            res=re.search(r'constr(\d+)_', paths[i])
            constr=int(res.group(1))
            l_constr.append(constr)

            legtext = "#splitline{%d#sigma}{#chi^{2}/n = %.1f/%.1f}" % (constr, l_chi2[i], l_ndof[i]) 
  
        elif "anafit" in paths[i].lower() or "globalfit" in paths[i].lower() or "swift" in paths[i].lower():
            if "four" in paths[i].lower():
                p=4
            elif "five" in paths[i].lower():
                p=5
            elif "six" in paths[i].lower():
                p=6
            elif "seven" in paths[i].lower():
                p=7
                
            legtext = "#splitline{%d-par fit}{#chi^{2}/n = %.1f/%.0f}" % (p, l_chi2[i], l_ndof[i]) 

            l_par.append(p)

        leg.AddEntry(h, legtext, "f")

    for i in range(len(l_chi2)-1):
        
        (F, pF) = calcFpF( chi2_nom=l_chi2[i], 
                           chi2_alt=l_chi2[i+1], 
                           npars_nom=l_npars[i], 
                           npars_alt=l_npars[i+1], 
                           nbins=nbins, 
                           zerochi2=options.zerochi2 )
        
        print "\nF-Test between:", paths[i], paths[i+1]
        print "chi2 values:", l_chi2[i], l_chi2[i+1]
        print "npars:", l_npars[i], l_npars[i+1]
        print "nbins:", nbins
        print "F:", F
        print "pF:", pF

        if "nlofit" in paths[i].lower():
            leg2.AddEntry(0, "p(F_{^{%d#sigma #rightarrow %d#sigma}}) = %.2f" % (l_constr[i], l_constr[i+1], pF), "")
        elif "anafit" in paths[i].lower() or "globalfit" in paths[i].lower() or "swift" in paths[i].lower():
            leg2.AddEntry(0, "p(F_{^{%d #rightarrow %d par}}) = %.2f" % (l_par[i], l_par[i+1], pF), "")

    leg.Draw()
    leg2.Draw()
    c.Update()

    c.Print(options.output + ".svg")
    c.Print(options.output + ".pdf")
        
    # raw_input("press enter")
        
if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
