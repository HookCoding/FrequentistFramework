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

def roundToMultiple(x, mult):
    return mult * round(x / mult)

def readGraphsFromFile(paths, dicts_out, graphs, ratios, spacing, width, means=None, amps=None):
    i=0
    for p in paths:
        dicts_out.append({})
        graphs.append({})
        ratios.append({})

        f = TFile(p)

        shift=-1
        for k in f.GetListOfKeys():
            name = k.GetName()
            d = f.Get(name)
            
            if not isinstance(d, ROOT.TGraph):
                continue

            if not "g1_profile" in name:
                continue

            searchstring =r'_(\d+)_(-?\d+)$'
            res=re.search(searchstring, name)
            m=int(res.group(1))
            w=int(res.group(2))

            if width!=None and w!=width:
                continue

            if means!=None and not m in means:
                continue

            shift+=1
            graphs[i][(m,w)] = d
            ratios[i][(m,w)] = ROOT.TGraphErrors()

            for j in range(graphs[i][(m,w)].GetN()):
                a = ctypes.c_double()
                y = ctypes.c_double()
                graphs[i][(m,w)].GetPoint(j, a, y)
                a = a.value
                y = y.value
                ey = graphs[i][(m,w)].GetErrorY(j)

                if amps and a not in amps:
                    continue

                a_shifted = a+((shift-5.)/10)*spacing
                graphs[i][(m,w)].SetPoint(j, a_shifted, y)

                # if a!=0:
                #     ratios[i][(m,w)].SetPoint(ratios[i][(m,w)].GetN(), a_shifted, (y-a) / ey)
                #     ratios[i][(m,w)].SetPointError(ratios[i][(m,w)].GetN()-1, 0, 0)
                if ey != 0:
                    ratios[i][(m,w)].SetPoint(ratios[i][(m,w)].GetN(), a_shifted, (y-a) / ey)
                    ratios[i][(m,w)].SetPointError(ratios[i][(m,w)].GetN()-1, 0, 0)
    
                if not m in dicts_out[i]:
                    dicts_out[i][m] = {}
                if not w in dicts_out[i][m]:
                    dicts_out[i][m][w] = {}
                if not a in dicts_out[i][m][w]:
                    dicts_out[i][m][w][a] = {}
            
                dicts_out[i][m][w][a]["rms"] = ey
                dicts_out[i][m][w][a]["bias"] = y
                if ey != 0:
                    dicts_out[i][m][w][a]["ratio"] = (y-a) / ey
                else:
                    dicts_out[i][m][w][a]["ratio"] = float('NaN')

        i+=1

def main(args):
    SetAtlasStyle()
 
    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    # parser.add_argument('--input_is_spurious', dest='input_is_spurious', action='store_true', help='Input is already a spurious signal graph. Otherwise a file created with createExtractionGraphs.py is expected.')
    parser.add_argument('--width', dest='width', type=int, default=None, help='Only plot given width')
    parser.add_argument('--means', dest='means', type=int, nargs='+', default=None, help='Means to draw in plot')
    parser.add_argument('--amps', dest='amps', type=int, nargs='+', default=None, help='Amps to draw in plot')
    parser.add_argument('--doAtlasLabel', action="store_true", help='Add ATLAS label to plots')

    args, paths = parser.parse_known_args(args)
    
    print(args, paths)
    
    # J100:
    # text="#sqrt{s}=13 TeV, 132 fb^{-1} PD"
    text="J100 PD, 132 fb^{-1}"
    xmin=-0.2
    xmax=5.2
    ymin=-0.9
    ymax=9
    spacing=0.3

    if "J50" in paths[0] or "302" in paths[0]:
        # J50:
        # text="#sqrt{s}=13 TeV, 15.0 fb^{-1} PD"
        text="J50 PD, 15.0 fb^{-1}"
        # ymin=-0.69e5
        # ymax=0.69e5
        # spacing=8

    # if args.width == -999:
        # xmin=-0.4
        # xmax=10.4
        # ymin=-1.8
        # ymax=16


    colors = getColorSteps(len(paths))
    markers = getMarkerStyles()

    dicts_out = []
    graphs = []
    ratios = []

    readGraphsFromFile(paths, dicts_out, graphs, ratios, spacing, args.width, args.means, args.amps)

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

        outname = "SignalExtraction_%d" % i
        if "extractionGraphs" in p:
            outname = p.replace("extractionGraphs", "SignalExtraction").replace(".root", "")

        f_out = ROOT.TFile(outname + ".root", "RECREATE")

        colors = getColorSteps(len(graphs[i]))

        c = ROOT.TCanvas("c1", "c1", 800, 600)
        pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
        pad1.SetBottomMargin(0.005) #Upper and lower plot are joined
        pad1.Draw()
        pad1.cd()

        # leg = ROOT.TLegend(0.20,0.50,0.50,0.90)
        if len(graphs[i]) > 5:
            leg = ROOT.TLegend(0.20,0.55,0.75,0.90)
            leg.SetNColumns(2)
            leg.SetFillStyle(0)
            box1 = ROOT.TPave(0.2,0.62,0.75,0.90,0,"NDC");
            box2 = ROOT.TPave(0.2,0.55,0.4,0.62,0,"NDC");
            box1.SetFillStyle(1001)
            box1.SetFillColor(ROOT.kWhite)
            box1.SetLineWidth(0)
            box2.SetFillStyle(1001)
            box2.SetFillColor(ROOT.kWhite)
            box2.SetLineWidth(0)
        else:
            leg = ROOT.TLegend(0.20,0.55,0.55,0.90)

        first = True

        for j, (m,w) in enumerate(sorted(graphs[i])):
            g=graphs[i][(m,w)]

            if first:
                g.Draw("apl")

                # l = TLine(0,0,g.GetXaxis().GetXmax(),g.GetXaxis().GetXmax())
                l = TLine(xmin,0,xmax,xmax)
                l.SetLineColor(kGray+2)
                l.SetLineStyle(7)
                l.Draw()

                first = False

            g.Draw("pl")

            # g.SetTitle("#sigma_{G}/m_{G} = %.2f" % (w/100.))
            if w > 0:
                g.SetTitle("m_{G} = %.0f GeV" % m)
            else:
                g.SetTitle("m_{Z'} = %.0f GeV" % m)
            g.GetXaxis().SetTitle("")
            g.GetYaxis().SetTitle("S_{fit} / #sqrt{B}")
            g.GetYaxis().SetTitleOffset(1.6) # ROOT 6.30
            g.GetXaxis().SetLimits(xmin, xmax)
            g.GetYaxis().SetRangeUser(ymin, ymax)
            g.SetLineColor(colors[j])
            g.SetLineWidth(2)
            g.SetMarkerColor(colors[j])
            g.SetMarkerStyle(markers[j])

            leg.AddEntry(g, g.GetTitle(), "pe")

            g.Write("nsig_mass%d_width%d" % (m,w))

        if args.doAtlasLabel:
            ATLASLabel(0.57, 0.10, "Work in progress", 13)
            myText(0.91, 0.20, 1, text, 33)
            myText(0.905, 0.26, 1, legend, 33)

        else:
            box3 = ROOT.TPave(0.80,0.06,0.92,0.20,0,"NDC");
            box4 = ROOT.TPave(0.70,0.06,0.92,0.14,0,"NDC");
            box3.SetFillStyle(1001)
            box3.SetFillColor(ROOT.kWhite)
            box3.SetLineWidth(0)
            box4.SetFillStyle(1001)
            box4.SetFillColor(ROOT.kWhite)
            box4.SetLineWidth(0)
            box3.Draw()
            box4.Draw()
            myText(0.90, 0.13, 1, text, 33)
            myText(0.90, 0.19, 1, legend, 33)


        # myText(0.20, 0.50, 1, "#sigma_{G}/m_{G} = %.2f" % (w/100.), 11)
        if w > 0:
            leg.AddEntry(0,"#sigma_{G}/m_{G} = %.2f" % (w/100.),"")
        else:
            leg.AddEntry(0,"g_{q} = 0.1","")
        
        if 'box1' in locals():
            box1.Draw()
        if 'box2' in locals():
            box2.Draw()
        
        leg.Draw()

        c.cd()
        pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.3);
        pad2.SetTopMargin(0.01);
        pad2.SetBottomMargin(0.35)
        pad2.Draw()

        pad2.cd()

        first = True

        for j, (m,w) in enumerate(sorted(ratios[i])):
            if args.width and w != args.width:
                continue

            g=ratios[i][(m,w)]

            if first:
                g.Draw("apl")

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

            g.Draw("pl")

            if w > 0:
                g.SetTitle("#sigma_{G}/m_{G} = %.2f" % (w/100.))
            else:
                g.SetTitle("g_{q} = 0.1")
            g.GetXaxis().SetTitle("S_{inj} / #sqrt{B}")
            g.GetXaxis().SetTitleOffset(1.0) # ROOT 6.30
            # g.GetXaxis().SetTitleOffset(3.5)
            g.GetYaxis().SetTitle("S_{spur} / #sigma_{fit}")
            g.GetYaxis().SetTitleOffset(1.6) # ROOT 6.30
            g.GetXaxis().SetLimits(xmin, xmax)
            # g.GetYaxis().SetRangeUser(-0.99, 0.99)
            g.GetYaxis().SetRangeUser(-1.49, 1.49)
            g.GetYaxis().SetNdivisions(506)
            g.SetLineColor(colors[j])
            g.SetLineWidth(2)
            g.SetMarkerColor(colors[j])
            g.SetMarkerStyle(markers[j])

        c.Update()

        if args.width:
            c.Print(outname + "_width%d.pdf" % args.width)
        else:
            c.Print(outname + ".pdf")
            c.Print(outname + ".svg")
        # c.Print(outname + "_width%d.svg" % args.width)

        f_out.Close()

        with open(outname + ".json", 'w') as f_json:
            json.dump(dicts_out[i], f_json)

    # raw_input("Press enter to continue...")


if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
