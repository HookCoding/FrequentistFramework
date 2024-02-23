#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
from color import getColorSteps, getMarkerStyles
import json
import ctypes

gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

usePercentiles = False
# spurSigUnc = 0.5

def shiftaxis(g,shift=0):
    """This function shifts the x-axis on a TGraph."""
    N = g.GetN()
    x = g.GetX()
    for i in range(N):
        x[i] += shift
    g.GetHistogram().Delete()
    g.SetHistogram(0)
    return

def readGraphsFromFile(paths, dicts_out, graphs, ratios):
    i=0
    for p in paths:
        dicts_out.append({})
        graphs.append({})
        ratios.append({})

        f = TFile(p)

        for k in f.GetListOfKeys():
            name = k.GetName()
            d = f.Get(name)
            
            if not ("nsig" in name):
                continue

            if not isinstance(d, ROOT.TGraph):
                continue

            # print("Keeping", name)
            searchstring =r'_width(-?\d+)(:?_amp\d+)?'
            res=re.search(searchstring, name)
            w=int(res.group(1))
            try:
                a=int(res.group(2)[4:])
            except:
                a=0

            graphs[i][(w,a)] = d
            ratios[i][(w,a)] = ROOT.TGraphErrors()

            for j in range(graphs[i][(w,a)].GetN()):
                m = ctypes.c_double()
                y = ctypes.c_double()
                graphs[i][(w,a)].GetPoint(j, m, y)
                m = m.value
                y = y.value
                ey = graphs[i][(w,a)].GetErrorY(j)

                ratios[i][(w,a)].SetPoint(j, m, y / ey)
    
                # if not m in dicts_out[i]:
                #     dicts_out[i][m] = {}
                # if not w in dicts_out[i][m]:
                #     dicts_out[i][m][w] = {}
                # if not a in dicts_out[i][m][w]:
                #     dicts_out[i][m][w][a] = {}
            
                # dicts_out[i][m][w][a]["rms"] = ey
                # dicts_out[i][m][w][a]["bias"] = y
                # dicts_out[i][m][w][a]["ratio"] = y / ey
                # dicts_out[i][m][w][a]["uncertainty"] = spurSigUnc*ey

        i+=1

def readGraphsFromFileNoToys(paths, dicts_out, graphs, ratios):
    i=0
    for p in paths:
        dicts_out.append({})
        graphs.append({})
        ratios.append({})

        f = TFile(p)

        for k in f.GetListOfKeys():
            name = k.GetName()
            d = f.Get(name)
            
            if not isinstance(d, ROOT.TGraph):
                continue

            if not "g1_profile" in name:
                continue

            # hack, because information about sqrt(B) lost in TGraphErrors
            g_inj = f.Get(name.replace("profile","extraction"))
            l_x = []
            for j in range(g_inj.GetN()):
                x = ctypes.c_double()
                y = ctypes.c_double()
                g_inj.GetPoint(j, x, y)
                x = x.value
                l_x.append(x)
            # l_x.sort()
            # sqrtB = min([x for x in l_x if x > 0])*0.5
            # print("deb0:", l_x, sqrtB)

            searchstring =r'_(\d+)_(-?\d+)$'
            res=re.search(searchstring, name)
            m=int(res.group(1))
            w=int(res.group(2))

            if m==300:
                continue

            if not (w,0) in graphs[i]:
                graphs[i][(w,0)] = ROOT.TGraphErrors()
                ratios[i][(w,0)] = ROOT.TGraphErrors()

            l_a = []
            for j in range(d.GetN()):
                a = ctypes.c_double()
                y = ctypes.c_double()
                d.GetPoint(j, a, y)
                a = a.value
                l_a.append(a)
                if a != 0:
                    continue
                y = y.value
                ey = d.GetErrorY(j)
                # print("deb1:", j, y, ey)
            # l_a.sort()
            minx = min([x for x in l_x if x > 0])
            mina = min([a for a in l_a if a > 0])
            sqrtB = float(minx) / mina
            # print("deb0:", l_x, l_a, sqrtB)
                
            np = graphs[i][(w,0)].GetN()
            # print("deb:", a, y, ey, sqrtB)

            graphs[i][(w,0)].SetPoint(np, m, y*sqrtB)
            graphs[i][(w,0)].SetPointError(np, 0, ey*sqrtB)
            
            ratios[i][(w,0)].SetPoint(np, m, y / ey)
                            
            if not m in dicts_out[i]:
                dicts_out[i][m] = {}
            if not w in dicts_out[i][m]:
                dicts_out[i][m][w] = {}
            if not a in dicts_out[i][m][w]:
                dicts_out[i][m][w][0] = {}
            
            dicts_out[i][m][w][0]["rms"] = ey*sqrtB
            dicts_out[i][m][w][0]["bias"] = y*sqrtB
            dicts_out[i][m][w][0]["ratio"] = y / ey

        i+=1

def fillGraphsFromHists(paths, hists, dicts_out, graphs, ratios, fillstyles, colors, text, doAtlasLabel):
    for p in paths:
        dicts_out.append({})
        graphs.append({})
        ratios.append({})
            
        legend = ""
        if "fourPar" in p:
            legend = "4-par fit"
        elif "fivePar" in p:
            legend = "5-par fit"
        elif "sixPar" in p:
            legend = "6-par fit"
        elif "sevenPar" in p:
            legend = "7-par fit"
        elif "eightPar" in p:
            legend = "8-par fit"
        else:
            searchstring =r'constr(\d+)'
            res=re.search(searchstring, p)
            sigma=int(res.group(1))
            legend = "NLOFit, #sigma=%d" % sigma

        c = TCanvas("c1", "c1", 800, 600)
        outname = p.replace("extractionGraphs", "spuriousSignal").replace(".root", "_histograms.pdf")
        c.Print(outname + "[")

        for m in sorted(hists):
            for w in hists[m]:
                for a in hists[m][w]:
                    for name in hists[m][w][a]:

                        if not ("nsig" in name):
                            continue
    
                        list_h = hists[m][w][a][name]
    
                        c = TCanvas("c1", "c1", 800, 600)
                        c.SetRightMargin(0.075)
                        # c.SetLogy()
    
                        mean = []
                        rms = []
                        skew = []
                        kurt = []
    
                        for i, h in enumerate(list_h):
                            h.SetFillStyle(fillstyles[i])
                            h.SetLineColor(colors[i])
                            h.SetFillColor(colors[i])
                            h.SetMarkerColor(colors[i])
                            # h.GetXaxis().SetTitle(name)
                            h.GetXaxis().SetTitle("S_{fit}")
                            # h.GetYaxis().SetTitle("Toys (normalized)")
                            h.GetYaxis().SetTitle("Toys")
                            # h.Scale(1./h.Integral())
                            
                            mean.append(h.GetMean())
                            rms.append(h.GetRMS())
                            skew.append(h.GetSkewness())
                            kurt.append(h.GetKurtosis())
    
                            h.Rebin(2)
                            # h.SetMaximum(h.GetMaximum()*5)
                            h.SetMaximum(h.GetMaximum()*1.3)
                            h.Draw("same hist")
    
    
                        leg = TLegend(0.66,0.80,0.89,0.90)
                        # leg = TLegend(0.66,0.70,0.89,0.90)
                        # leg.AddEntry(list_h[0], "#splitline{NLOFit:}{#it{S}_{spur}/#sigma_{fit}=%.2f}" % (mean[0]/rms[0]), "f")
                        leg.AddEntry(list_h[0], "#splitline{%s:}{#it{S}_{spur}/#sigma_{fit}=%.2f}" % (legend, mean[0]/rms[0]), "f")
                        leg.Draw()

                        if doAtlasLabel:
                            ATLASLabel(0.20, 0.90, "Work in progress", 13)
                            myText(0.20, 0.85, 1, text, 13)
                        else:
                            myText(0.20, 0.91, 1, text, 13)
                            if w > 0:
                                signaltext = "m_{G} = %d GeV, #sigma_{G}/m_{G} = %.2f" % (m,w*0.01)
                            else:
                                signaltext = "m_{Z'} = %d GeV, g_{q} = 0.1" % m
                            myText(0.20, 0.85, 1, signaltext, 13)
    
                        # outname = p.replace("extractionGraphs", "spuriousSignal").replace(".root", "_%s.pdf" % name)
                        if a == 0:
                            c.Print(outname)
    
                        # if not ("nsig" in name):
                        #     continue
                        
                        for i in range(len(list_h)):
                            if not (w,a) in graphs[i]:
                                graphs[i][(w,a)] = ROOT.TGraphErrors()
                                ratios[i][(w,a)] = ROOT.TGraphErrors()
    
                                if abs(mean[i] / rms[i]) > 0.3:
                                    print("WARNING: mean/rms=%.2f for %s in file %s" % (mean[i]/rms[i], name, paths[i]))
    
                            j = graphs[i][(w,a)].GetN()
                            graphs[i][(w,a)].SetPoint(j, m, mean[i])
                            graphs[i][(w,a)].SetPointError(j, 0, rms[i])
    
                            ratios[i][(w,a)].SetPoint(j, m, mean[i] / rms[i])
    
                            # if not m in dicts_out[i]:
                            #     dicts_out[i][m] = {}
                            # if not w in dicts_out[i][m]:
                            #     dicts_out[i][m][w] = {}
                            # if not a in dicts_out[i][m][w]:
                            #     dicts_out[i][m][w][a] = {}
                            
                            # dicts_out[i][m][w][a]["rms"] = rms[i]
                            # dicts_out[i][m][w][a]["bias"] = mean[i]
                            # dicts_out[i][m][w][a]["ratio"] = mean[i] / rms[i]
                            # dicts_out[i][m][w][a]["uncertainty"] = spurSigUnc*rms[i]

        c.Print(outname + "]")


def main(args):
    SetAtlasStyle()
 
    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    parser.add_argument('--input_is_spurious', dest='input_is_spurious', action='store_true', help='Input is already a spurious signal graph. Otherwise a file created with createExtractionGraphs.py is expected.')
    parser.add_argument('--notoys', dest='notoys', action='store_true', help='Use graphs instead of hists in file created with createExtractionGraphs.py. Necessary if no toys but just Asimov dataset was run.')
    parser.add_argument('--means', dest='means', type=str, nargs='+', help='Means to draw in plot')
    parser.add_argument('--doAtlasLabel', action="store_true", help='Add ATLAS label to plots')
    args, paths = parser.parse_known_args(args)
    
    print(args, paths)
    
    # J100:
    text="#sqrt{s}=13 TeV, 132 fb^{-1} PD"
    ymin=-0.69e5
    ymax=0.69e5
    spacing=20

    if "J50" in paths[0]:
        # J50:
        text="#sqrt{s}=13 TeV, 15.0 fb^{-1} PD"
        ymin=-0.69e5
        ymax=0.69e5
        spacing=6

    colors = getColorSteps(len(paths))
    fillstyles = [3245, 3254, 3245, 3254, 3245, 3254]
    markers = getMarkerStyles()

    hists = {}
 
    if args.input_is_spurious == False and args.notoys == False: 
        for p in paths:
            f = TFile(p)
    
            for k in f.GetListOfKeys():
                name = k.GetName()
                d = f.Get(name)
                
                if not isinstance(d, ROOT.TDirectory):
                    continue
                    
                if usePercentiles and not "_percentile" in name:
                    continue
    
                if not usePercentiles and "_percentile" in name:
                    continue
    
                searchstring =r'mean(\d+)_width(-?\d+)(:?_amp\d+)?'
                res=re.search(searchstring, name)
                m=int(res.group(1))
                w=int(res.group(2))
    
                try:
                    a=int(res.group(3)[4:])
                except:
                    a=0
    
                for k2 in d.GetListOfKeys():
                    name = k2.GetName()
    
                    if not ("nsig" in name or "nbkg" in name):
                        continue
    
                    h = d.Get(name)
                    h.SetDirectory(0)
    
                    if not m in hists:
                        hists[m]={}
                    if not w in hists[m]:
                        hists[m][w]={}
                    if not a in hists[m][w]:
                        hists[m][w][a]={}
                    if not name in hists[m][w][a]:
                        hists[m][w][a][name]=[]
    
                    hists[m][w][a][name].append(h)
    
                d.Close()
            f.Close()
    
    dicts_out = []
    graphs = []
    ratios = []
    if args.input_is_spurious:
        # input is spurious signal root file already. Just need to read TGraphErrors.
        readGraphsFromFile(paths, dicts_out, graphs, ratios)
    elif args.notoys:
        readGraphsFromFileNoToys(paths, dicts_out, graphs, ratios)
    else:
        fillGraphsFromHists(paths, hists, dicts_out, graphs, ratios, fillstyles, colors, text, args.doAtlasLabel)

    for i,p in enumerate(paths):

        legend = ""
        if "fourPar" in p:
            legend = "4-par fit"
        elif "fivePar" in p:
            legend = "5-par fit"
        elif "sixPar" in p:
            legend = "6-par fit"
        elif "sevenPar" in p:
            legend = "7-par fit"
        elif "eightPar" in p:
            legend = "8-par fit"
        else:
            searchstring =r'constr(\d+)'
            res=re.search(searchstring, p)
            sigma=int(res.group(1))
            legend = "NLOFit, #sigma=%d" % sigma

        outname = "SpuriousSignal_%d" % i
        if "extractionGraphs" in p:
            outname = p.replace("extractionGraphs", "spuriousSignal").replace(".root", "")

        f_out = ROOT.TFile(outname + ".root", "RECREATE")

        colors = getColorSteps(len([(w,a) for (x,a) in graphs[i] if a==0]))

        c = ROOT.TCanvas("c1", "c1", 800, 600)
        pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
        pad1.SetBottomMargin(0.005) #Upper and lower plot are joined
        pad1.Draw()
        pad1.cd()

        leg = ROOT.TLegend(0.67,0.60,0.91,0.90)
        first = True

        icolor = 0
        for j, (w,a) in enumerate(sorted(graphs[i])):
            if a != 0:
                continue

            g=graphs[i][(w,a)]
            g.Write("nsig_width%d_amp%d" % (w,a))
            if len(graphs[i]) > 1:
                l=len(graphs[i])/2
                shift=(float(j)/l-1)*spacing
            else:
                shift=0
            shiftaxis(g,shift)

            if first:
                g.Draw("ap")

                line = TLine(g.GetXaxis().GetXmin(),0,g.GetXaxis().GetXmax(),0)
                line.SetLineColor(kGray+2)
                line.SetLineStyle(7)
                line.Draw()

                first = False

            g.Draw("p")

            if w > 0:
                g.SetTitle("#sigma_{G}/m_{G} = %.2f" % (w/100.))
            else:
                g.SetTitle("g_{q} = 0.1")
            g.GetXaxis().SetTitle("")
            g.GetYaxis().SetTitle("S_{fit}")
            g.GetYaxis().SetTitleOffset(1.7)
            g.GetYaxis().SetRangeUser(ymin, ymax)
            g.SetLineColor(colors[icolor])
            g.SetMarkerColor(colors[icolor])
            g.SetMarkerStyle(markers[icolor])

            leg.AddEntry(g, g.GetTitle())

            # g.Write("nsig_width%d_amp%d" % (w,a))
            icolor += 1

        if args.doAtlasLabel:
            ATLASLabel(0.57, 0.10, "Work in progress", 13)
            myText(0.91, 0.20, 1, text, 33)
            myText(0.905, 0.26, 1, legend, 33)
        else:
            myText(0.90, 0.13, 1, text, 33)
            myText(0.90, 0.19, 1, legend, 33)

        leg.Draw()

        c.cd()
        pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.3);
        pad2.SetTopMargin(0.01);
        pad2.SetBottomMargin(0.35)
        pad2.Draw()

        pad2.cd()

        first = True

        icolor = 0
        for j, (w,a) in enumerate(sorted(ratios[i])):
            if a != 0:
                continue

            g=ratios[i][(w,a)]
            if len(graphs[i]) > 1:
                l=len(graphs[i])/2
                shift=(float(j)/l-1)*spacing
            else:
                shift=0
            shiftaxis(g,shift)

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

            if (w > 0):
                g.SetTitle("#sigma_{G}/m_{G} = %.2f" % (w/100.))
                g.GetXaxis().SetTitle("m_{G} [GeV]")
            else:
                g.SetTitle("g_{q} = 0.1")
                g.GetXaxis().SetTitle("m_{Z'} [GeV]")

            g.GetXaxis().SetTitleOffset(3.5)
            g.GetYaxis().SetTitle("S_{spur} / #sigma_{fit}")
            g.GetYaxis().SetTitleOffset(1.7)
            g.GetYaxis().SetRangeUser(-1.49, 1.49)
            g.GetYaxis().SetNdivisions(506)
            g.SetLineColor(colors[icolor])
            g.SetMarkerColor(colors[icolor])
            g.SetMarkerStyle(markers[icolor])
            
            icolor += 1

        c.Update()

        c.Print(outname + ".pdf")
        c.Print(outname + ".svg")

        f_out.Close()

        # with open(outname + ".json", 'w') as f_json:
        #     json.dump(dicts_out[i], f_json)

    # raw_input("Press enter to continue...")


if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
