#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
from color import getColorSteps

gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

# J50:
# text="#sqrt{s}=13 TeV, J50 15 fb^{-1} PD"
# ymin=-1.99e5
# ymax=1.99e5
# spacing=8

# J100:
#text="#sqrt{s}=13 TeV, 29.6 fb^{-1}" #old lumi calc
#text="#sqrt{s}=13 TeV, 25.29 fb^{-1}"
text="#sqrt{s}=13.6 TeV, 1 fb^{-1}"
xmin=80#-0.49e5
xmax=1000#0.49e5
ymin=-1999#-0.49e5
ymax=2000#0.49e5
spacing=20


def main(args):
    SetAtlasStyle()
    ROOT.gROOT.SetBatch(True)
    paths = args
    print(args)
    colors = getColorSteps(len(paths))
    fillstyles = [3245, 3254, 3245, 3254, 3245, 3254]

    hists = {}
    
    for p in paths:
        f = TFile(p)

        for k in f.GetListOfKeys():

            name = k.GetName()
            print(name)
            if not ("hists_" in name):
                continue
            if ("percentile" in name):
                continue
            #d = f.Get(name)
            #if not isinstance(d, ROOT.TDirectory):
            #    continue
            

            
            try:
              res=re.search(r'mean(\d+)_width(\d+)(:?_amp\d+)?', name)
              print(res)
              print(res.group(1))
              print(res.group(2))
              m=int(res.group(1))
              w=int(res.group(2))
            except:
              res=re.search(r'mean(\d+)_width(-\d+)(:?_amp\d+)?', name)
              m=int(res.group(1))
              w=-1


            try:
                a=int(res.group(3)[4:])
            except:
                a=0
            # for k2 in d.GetListOfKeys():
                # name = k2.GetName()

            # if not ("nsig" in name or "nbkg" in name):
            #     continue
            h_folder = f.Get(name)
            #print(h_folder.ls())

            for key in h_folder.GetListOfKeys():
                obj_name = key.GetName()
                if obj_name.startswith("nsig_"):
                    h = h_folder.Get(obj_name)

            #h = h_folder.Get("nsig_mean"+res.group(1)+"_width"+"%.1f" % w)
            h_clone = h.Clone()
            # h.SetDirectory(0)
            if not m in hists:
                hists[m]={}
            if not w in hists[m]:
                hists[m][w]={}
            if not a in hists[m][w]:
                hists[m][w][a]={}
            if not name in hists[m][w][a]:
                hists[m][w][a][name]=[]
            hists[m][w][a][name].append(h_clone)
            # d.Close()
        outname = p.replace("extractionGraphs", "spuriousSignal").replace(".root", "")
    if "tenPar" in outname:
        npar="10"
    elif "ninePar" in outname:
        npar="9"
    elif "eightPar" in outname:
        npar="8"
    elif "sevenPar" in outname:
        npar="7"
    elif "sixPar" in outname:
        npar="6"
    elif "fivePar" in outname:
        npar="5"
    elif "fourPar" in outname:
        npar="4"
    graphs = []
    ratios = []
    for p in paths:
        graphs.append({})
        ratios.append({})
    print("now I will analize the histograms:")
    print(hists)
    for m in sorted(hists):
        
        for w in hists[m]:
            for a in hists[m][w]:
                for name in hists[m][w][a]:
                    list_h = hists[m][w][a][name]
                    c = TCanvas("c1", "c1", 800, 600)
                    # c.SetLogy()

                    mean = []
                    rms =  []
                    skew = []
                    kurt = []
                    for i, h in enumerate(list_h):
                        h.SetFillStyle(fillstyles[i])
                        h.SetLineColor(colors[i])
                        h.SetFillColor(colors[i])
                        h.SetMarkerColor(colors[i])
                        h.GetXaxis().SetTitle("nsig_"+name.split("hists_")[1].split("_amp")[0])
                        h.GetYaxis().SetTitle("# toys")
                        
                        mean.append(h.GetMean())
                        rms.append(h.GetRMS())
                        #skew.append(h.GetSkewness())
                        #kurt.append(h.GetKurtosis())

                        #h.Rebin(4)
                        h.Rebin(8)
                        # h.SetMaximum(h.GetMaximum()*5)
                        h.SetMaximum(h.GetMaximum()*1.3)
                        h.Draw("same hist")

                    #print(mean,rms)
                    #leg = TLegend(0.66,0.70,0.89,0.90)
                    #leg.AddEntry(list_h[0], "#splitline{NLOFit:}{#it{S}_{spur}/#sigma_{fit}=%.2f}" % (mean[0]/rms[0]), "f")
                    #leg.AddEntry(list_h[1], "#splitline{5-par:}{#it{S}_{spur}/#sigma_{fit}=%.2f}" % (mean[1]/rms[1]), "f")
                    #leg.Draw()

                    ATLASLabel(0.20, 0.90, "Work in progress", 13)
                    myText(0.20, 0.84, 1, text, 13)
                    myText(0.20, 0.77, 1, npar+"-par fit", 13)

                    #c.Print("spuriousSignal_%s.png" % name)
                    c.SaveAs(outname+"_%s.pdf" % name)

                    #if not ("nsig" in name):
                    #    continue
                    print(len(list_h))
                    for i in range(len(list_h)):
                        if not (w,a) in graphs[i]:
                            graphs[i][(w,a)] = ROOT.TGraphErrors()
                            ratios[i][(w,a)] = ROOT.TGraphErrors()

                            if abs(mean[i] / rms[i]) > 0.3:
                                print ("WARNING: mean/rms=%.2f for %s in file %s" % (mean[i]/rms[i], name, paths[i]))
                        j = graphs[i][(w,a)].GetN()
                        graphs[i][(w,a)].SetPoint(j, m+0*(w/5-2)*spacing, mean[i])
                        graphs[i][(w,a)].SetPointError(j, 0, rms[i])
                        ratios[i][(w,a)].SetPoint(j, m+0*(w/5-2)*spacing, mean[i] / rms[i])
    print(graphs[0])
    for i,p in enumerate(paths):

        outname = "SpuriousSignal_%d" % i
        if "extractionGraphs" in p:
            outname = p.replace("extractionGraphs", "spuriousSignal").replace(".root", "")

        f_out = ROOT.TFile(outname + ".root", "RECREATE")

        colors = getColorSteps(len(graphs[i]))
        
        c = ROOT.TCanvas("c1", "c1", 800, 600)
        pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
        pad1.SetBottomMargin(0.005) #Upper and lower plot are joined
        pad1.Draw()
        pad1.cd()

        leg = ROOT.TLegend(0.66,0.55,0.89,0.90)
        leg.SetTextSize(20);
        first = True

        for j, (w,a) in enumerate(sorted(graphs[i])):
            g=graphs[i][(w,a)]
            if first:
                g.Draw("ap")

                l = TLine(xmin,0,xmax,0)
                l.SetLineColor(kGray+2)
                l.SetLineStyle(7)
                l.Draw()

                first = False

            g.Draw("p")

            if w > 0:
              g.SetTitle("#sigma_{jj}/m_{jj} = %.2f" % (w/100.))
            else:
              g.SetTitle("DSCB (nominal Z')")
            g.GetXaxis().SetTitle("m_{jj} [GeV]")
            g.GetXaxis().SetLimits(xmin,xmax)
            g.GetYaxis().SetTitle("N_{sig}")
            g.GetYaxis().SetTitleOffset(2)
            g.GetYaxis().SetRangeUser(ymin, ymax)
            g.SetLineColor(colors[j])
            g.SetMarkerColor(colors[j])

            leg.AddEntry(g, g.GetTitle())

            g.Write("nsig_width%d_amp%d" % (w,a))

        #ATLASLabel(0.20, 0.90, "Work in progress", 13)
        #myText(0.20, 0.84, 1, text, 13)
        #myText(0.20, 0.77, 1, npar+"-par fit", 13)
        ATLASLabel(0.57, 0.10, "Work in progress", 13)
        myText(0.91, 0.20, 1, text, 33)
        myText(0.905, 0.26, 1,npar+"-par fit", 33)
        leg.Draw()

        c.cd()
        pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.3);
        pad2.SetTopMargin(0.01);
        pad2.SetBottomMargin(0.35)
        pad2.Draw()

        pad2.cd()

        first = True

        for j, (w,a) in enumerate(sorted(ratios[i])):
            g=ratios[i][(w,a)]

            if first:
                g.Draw("ap")

                l1 = TLine(xmin,0.5,xmax,0.5)
                l1.SetLineColor(kGray+2)
                l1.SetLineStyle(7)
                l1.Draw()
                l2 = TLine(xmin,-0.5,xmax,-0.5)
                l2.SetLineColor(kGray+2)
                l2.SetLineStyle(7)
                l2.Draw()
                l3 = TLine(xmin,0,xmax,0)
                l3.SetLineColor(kGray+2)
                l3.Draw()

                first = False

            g.Draw("p")

            g.SetTitle("#sigma_{jj}/m_{jj} = %.2f" % (w/100.))
            g.GetXaxis().SetTitle("m_{jj} [GeV]")
            g.GetXaxis().SetTitleOffset(1)#3.5)
            g.GetYaxis().SetTitle("S_{spur} / #sigma_{fit}")
            g.GetYaxis().SetTitleOffset(2)
            g.GetYaxis().SetRangeUser(-1.49, 1.49)
            g.GetXaxis().SetLimits(xmin,xmax)
            g.SetLineColor(colors[j])
            g.SetMarkerColor(colors[j])

        c.Update()
        c.SaveAs(outname + ".pdf")
        #c.Print(outname + ".png")

        f_out.Close()
        f.Close()
    # raw_input("Press enter to continue...")


if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not x.startswith("-")]
   print(args)
   sys.exit(main(args))
