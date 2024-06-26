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
text="#sqrt{s}=13 TeV, J100 130 fb^{-1} PD"
ymin=-0.49e5
ymax=0.49e5
spacing=20


def main(args):
    SetAtlasStyle()
 
    paths = args

    colors = getColorSteps(len(paths))
    fillstyles = [3245, 3254, 3245, 3254, 3245, 3254]

    hists = {}
    
    for p in paths:
        print(p)
        f = TFile(p)

        for k in f.GetListOfKeys():
            name = k.GetName()
            print(name)
            # d = f.Get(name)
            
            # if not isinstance(d, ROOT.TDirectory):
            #     continue

            res=re.search(r'mean(\d+)_width(\d+)(:?_amp\d+)?', name)
            m=int(res.group(1))
            w=int(res.group(2))
            try:
                a=int(res.group(3)[4:])
            except:
                a=0
            # for k2 in d.GetListOfKeys():
                # name = k2.GetName()

            # if not ("nsig" in name or "nbkg" in name):
            #     continue
            
            h = f.Get(name)
            # h.SetDirectory(0)
            print(h)
            if not m in hists:
                hists[m]={}
            if not w in hists[m]:
                hists[m][w]={}
            if not a in hists[m][w]:
                hists[m][w][a]={}
            if not name in hists[m][w][a]:
                hists[m][w][a][name]=[]

            hists[m][w][a][name].append(h)

            # d.Close()
        f.Close()

    graphs = []
    ratios = []
    for p in paths:
        graphs.append({})
        ratios.append({})

    for m in sorted(hists):
        for w in hists[m]:
            for a in hists[m][w]:
                for name in hists[m][w][a]:

                    list_h = hists[m][w][a][name]
                    print(m, w, a, name)
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
                        h.GetXaxis().SetTitle(name)
                        h.GetYaxis().SetTitle("# toys")
                        
                        mean.append(h.GetMean())
                        rms.append(h.GetRMS())
                        skew.append(h.GetSkewness())
                        kurt.append(h.GetKurtosis())

                        h.Rebin(2)
                        # h.SetMaximum(h.GetMaximum()*5)
                        h.SetMaximum(h.GetMaximum()*1.3)
                        h.Draw("same hist")


                    # leg = TLegend(0.66,0.70,0.89,0.90)
                    # leg.AddEntry(list_h[0], "#splitline{NLOFit:}{#it{S}_{spur}/#sigma_{fit}=%.2f}" % (mean[0]/rms[0]), "f")
                    # leg.AddEntry(list_h[1], "#splitline{5-par:}{#it{S}_{spur}/#sigma_{fit}=%.2f}" % (mean[1]/rms[1]), "f")
                    # leg.Draw()

                    ATLASLabel(0.20, 0.90, "Work in progress", 13)
                    myText(0.20, 0.85, 1, text, 13)

                    c.Print("spuriousSignal_%s.svg" % name)

                    if not ("nsig" in name):
                        continue
                    
                    for i in range(len(list_h)):
                        if not (w,a) in graphs[i]:
                            graphs[i][(w,a)] = ROOT.TGraphErrors()
                            ratios[i][(w,a)] = ROOT.TGraphErrors()

                            if abs(mean[i] / rms[i]) > 0.3:
                                print ("WARNING: mean/rms=%.2f for %s in file %s" % (mean[i]/rms[i], name, paths[i])
)
                        j = graphs[i][(w,a)].GetN()
                        graphs[i][(w,a)].SetPoint(j, m+(w/5-2)*spacing, mean[i])
                        graphs[i][(w,a)].SetPointError(j, 0, rms[i])

                        ratios[i][(w,a)].SetPoint(j, m+(w/5-2)*spacing, mean[i] / rms[i])

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

        leg = ROOT.TLegend(0.66,0.60,0.89,0.90)
        first = True

        for j, (w,a) in enumerate(sorted(graphs[i])):
            g=graphs[i][(w,a)]

            if first:
                g.Draw("ap")

                l = TLine(g.GetXaxis().GetXmin(),0,g.GetXaxis().GetXmax(),0)
                l.SetLineColor(kGray+2)
                l.SetLineStyle(7)
                l.Draw()

                first = False

            g.Draw("p")

            g.SetTitle("#sigma_{G}/m_{G} = %.2f" % (w/100.))
            g.GetXaxis().SetTitle("")
            g.GetYaxis().SetTitle("N_{sig}")
            g.GetYaxis().SetRangeUser(ymin, ymax)
            g.SetLineColor(colors[j])
            g.SetMarkerColor(colors[j])

            leg.AddEntry(g, g.GetTitle())

            g.Write("nsig_width%d_amp%d" % (w,a))

        ATLASLabel(0.20, 0.90, "Work in progress", 13)
        myText(0.20, 0.85, 1, text, 13)
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

                l1 = TLine(g.GetXaxis().GetXmin(),0.5,g.GetXaxis().GetXmax(),0.5)
                l1.SetLineColor(kGray+2)
                l1.SetLineStyle(7)
                l1.Draw()
                l2 = TLine(g.GetXaxis().GetXmin(),-0.5,g.GetXaxis().GetXmax(),-0.5)
                l2.SetLineColor(kGray+2)
                l2.SetLineStyle(7)
                l2.Draw()
                l3 = TLine(g.GetXaxis().GetXmin(),0,g.GetXaxis().GetXmax(),0)
                l3.SetLineColor(kGray+2)
                l3.Draw()

                first = False

            g.Draw("p")

            g.SetTitle("#sigma_{G}/m_{G} = %.2f" % (w/100.))
            g.GetXaxis().SetTitle("m_{G} [GeV]")
            g.GetXaxis().SetTitleOffset(3.5)
            g.GetYaxis().SetTitle("S_{spur} / #sigma_{fit}")
            g.GetYaxis().SetRangeUser(-1.49, 1.49)
            g.SetLineColor(colors[j])
            g.SetMarkerColor(colors[j])

        c.Update()
        c.Print(outname + ".pdf")
        c.Print(outname + ".svg")

        f_out.Close()

    # raw_input("Press enter to continue...")


if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not x.startswith("-")]
   sys.exit(main(args))
