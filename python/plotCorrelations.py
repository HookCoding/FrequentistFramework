#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ROOT
import sys, re, os, math, argparse
import numpy as np
from color import getColorSteps

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def DrawTH2D(h2, outfile, text = "", doText=True, drawAtlasLabel=True):
    ROOT.gStyle.SetPaintTextFormat("1.0f")
    # ROOT.gStyle.SetPalette(ROOT.kTemperatureMap)
    ROOT.gStyle.SetPalette(ROOT.kLightTemperature)
    ROOT.gStyle.SetNumberContours(255)

    # font=42 # Helvetica, relative
    ROOT.gStyle.SetTextFont(42)

    ROOT.gPad.SetLeftMargin(0.35)
    ROOT.gPad.SetRightMargin(.115)
    ROOT.gPad.SetBottomMargin(0.35)
    ROOT.gPad.SetTopMargin(0.04)

    #split h2 into diagonal for black text and off-diagonal for white

    h2_diag = h2.Clone()
    h2_offdiag = h2.Clone()
    h2_diag.Reset("M")
    h2_offdiag.Reset("M")
  
    for i in range(1, h2.GetNbinsX()+1):
        for j in range(1, h2.GetNbinsY()+1):
            ibin = h2.GetBin(i,j)
            if (i==j):
                h2_diag.SetBinContent(ibin,h2.GetBinContent(ibin))
            else:
                h2_offdiag.SetBinContent(ibin,h2.GetBinContent(ibin))

    for i in range(1, h2.GetNbinsX()+1):
        h2.GetXaxis().SetBinLabel(i, h2.GetXaxis().GetBinLabel(i).replace("ATLAS_",""))

    for i in range(1, h2.GetNbinsY()+1):
        h2.GetYaxis().SetBinLabel(i, h2.GetYaxis().GetBinLabel(i).replace("ATLAS_",""))

    miny = h2_offdiag.GetMinimum()
    maxy = h2_offdiag.GetMaximum()

    maxabs = max(abs(miny), abs(maxy))
    h2.SetMinimum(-1.2 * maxabs)
    h2.SetMaximum( 1.2 * maxabs)
                
    h2_diag.SetMarkerColor(ROOT.kWhite)
    h2_offdiag.SetMarkerColor(ROOT.kBlack)
    h2_offdiag.SetMarkerSize(0.6)

    h2.GetXaxis().LabelsOption("v");
    h2.GetXaxis().SetLabelSize(10);
    h2.GetYaxis().SetLabelSize(10);
    h2.GetZaxis().SetLabelSize(15);
    # h2.GetZaxis().SetTitle("\hbox{Correlation [‰]}") # does not render in pdf
    h2.GetZaxis().SetTitle("Correlation [10^{-3}]")
    h2.GetZaxis().SetTitleSize(15)
    h2.GetZaxis().SetTitleOffset(1.15)
    # h2.GetZaxis().SetTitleSize(1.0)

    if (doText):
        h2.Draw("colz")
        # h2_diag.Draw("text same")
        h2_offdiag.Draw("text same")
  
    else:
        h2.Draw("colz")

    if (drawAtlasLabel):
        ROOT.ATLASLabel(0.04, 0.285, "Work in progress", 13, 1, 15)
        ROOT.myText(0.04, 0.32, 1, text, 13, 15, 43)

    ROOT.gPad.Update()

    # raw_input("wait")

    ROOT.gPad.Print(outfile)


def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infiles', dest='infiles', nargs='+', type=str, required=True, help='Input file names')
    parser.add_argument('--inhist', dest='inhist', type=str, default="h2_cor", help='Input hist name')
    parser.add_argument('--folder', dest='folder', type=str, default='.', help='Output folder')

    args = parser.parse_args(args)

    # create dir if not exists: https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    try:
        os.makedirs(args.folder)
    except OSError:
        if not os.path.isdir(args.folder):
            raise

    c = ROOT.TCanvas("c1", "c1", 600, 600)

    for path in args.infiles:
        f_in = ROOT.TFile(path, "READ")
        h_in = f_in.Get(args.inhist)

        h_in.GetXaxis().SetRange(1,34)
        h_in.GetYaxis().SetRange(1,34)

        h_in.Scale(1000)

        outfile = os.path.join(args.folder, os.path.basename(path).replace(".root", ".pdf").replace("FitParameters","Correlations"))
        
        try:
            searchstring =r'_mR(\d+)_'
            res=re.search(searchstring, path)
            m=int(res.group(1))
        except:
            searchstring =r'_mean(\d+)_'
            res=re.search(searchstring, path)
            m=int(res.group(1))

        text = "m_{Z'} = %d GeV, g_{q} = 0.1" % m

        DrawTH2D(h_in, outfile, text, True, True)

        f_in.Close()


if __name__ == "__main__":  
   args=[x for x in sys.argv[1:] if not x == "-b"]
   sys.exit(main(args))   
