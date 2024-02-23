#!/usr/bin/env python
from __future__ import print_function
import ROOT
import sys, re, os, math, argparse
from array import array
from ROOT import *
from math import sqrt
from glob import glob
from color import getColorSteps
import json
import ctypes

gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasLabels.C")
gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasStyle.C")
gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

def roundToMultiple(x, mult):
    return mult * round(x / mult)

def readGraphsFromFile(paths, graphs):
    i=0
    for p in paths:
        graphs.append({})

        f = TFile(p)

        for k in f.GetListOfKeys():
            name = k.GetName()
            d = f.Get(name)
            
            if not ("nsig" in name):
                continue

            if not isinstance(d, ROOT.TGraph):
                continue

            print(name)
            searchstring =r'_width([-]?\d+)(:?_amp\d+)?'
            res=re.search(searchstring, name)
            w=int(res.group(1))
            try:
                a=int(res.group(2)[4:])
            except:
                a=0

            if a != 0:
                continue

            graphs[i][(w,a)] = d

        i+=1

def fillGraphRms(g, g_rms):
    for j in range(g.GetN()):
        x = ctypes.c_double()
        y = ctypes.c_double()
        g.GetPoint(j, x, y)
        y = y.value
        ey = g.GetErrorY(j)

        g_rms.SetPointY(j, ey)
        g_rms.SetPointError(j, 0, 0)
        

def main(args):
    SetAtlasStyle()
 
    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    parser.add_argument('--uncertainty', dest='uncertainty', type=float, default=0.5, help='Factor to multiply the RMS with to get the spurious signal uncertainty')
    args, paths = parser.parse_known_args(args)
    
    graphs = []
    dicts_out = []

    readGraphsFromFile(paths, graphs)

    for i,p in enumerate(paths):
        dicts_out.append({})

        # J100:
        xmin = 500
        xmax = 1800
        spacing = 25

        if "J50" in p:
            xmin = 350
            xmax = 700
            spacing = 25

        for j, (w,a) in enumerate(sorted(graphs[i])):

            g=graphs[i][(w,a)]
            g_rms=g.Clone()
            fillGraphRms(g, g_rms)

            for m in range(xmin, xmax+1, spacing):

                if not m in dicts_out[i]:
                    dicts_out[i][m] = {}
                if not w in dicts_out[i][m]:
                    dicts_out[i][m][w] = {}
                if not a in dicts_out[i][m][w]:
                    dicts_out[i][m][w][a] = {}
            
                # dicts_out[i][m][w][a]["rms"] = ey
                # dicts_out[i][m][w][a]["bias"] = y
                # dicts_out[i][m][w][a]["ratio"] = y / ey
                dicts_out[i][m][w][a]["uncertainty"] = args.uncertainty*g_rms.Eval(m)

        outname = p.replace(".root","_rms%.1f.json" % args.uncertainty)
        print("Writing to %s" % outname)
        with open(outname, 'w') as f_json:
            json.dump(dicts_out[i], f_json, indent=2, sort_keys = True)

if __name__ == "__main__":  
   # don't pass -b flag for root but keep -- flags for argparse
   args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
   sys.exit(main(args))
