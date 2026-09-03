import argparse
from typing import NamedTuple

import ROOT


class PostfitHistograms(NamedTuple):
    postfit: "ROOT.TH1"
    data: "ROOT.TH1"
    chi2: "ROOT.TH1"


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputFile", type=str, required=True)
    parser.add_argument("-o", "--output", type=str, required=True)
    return parser.parse_args(argv)


def load_postfit_histograms(input_file):
    # Returns the still-open ROOT.TFile alongside the histograms it owns -
    # not just a PostfitHistograms triple. Verified directly (see
    # doc/ACTIVITY_LOG.md's Tier 3 Chunk 10.B entry): once this function
    # returns, its own local TFile reference is garbage-collected unless
    # the caller keeps a reference of its own, which silently invalidates
    # every histogram returned alongside it (later use raises
    # "'CPyCppyy_NoneType' object has no attribute ..."). The original,
    # single-scope script never hit this, because its TFile stayed alive
    # as a script-level name for the whole run. Returning it here
    # preserves that exact lifetime across the new function boundary.
    postfit_file = ROOT.TFile.Open(input_file, "READ")
    postfit = postfit_file.Get("Run3TLA/postfit")
    data = postfit_file.Get("Run3TLA/data")
    chi2 = postfit_file.Get("Run3TLA/chi2")

    data.SetMarkerStyle(8)
    data.SetMarkerSize(0.5)
    data.SetMarkerColor(ROOT.kBlack)
    data.SetLineWidth(0)
    postfit.SetLineWidth(2)
    postfit.SetLineColor(ROOT.kAzure + 7)

    return PostfitHistograms(postfit=postfit, data=data, chi2=chi2), postfit_file


def build_ratio_histogram(data, postfit):
    h_ratio = data.Clone("h_ratio")
    h_ratio.Divide(postfit)

    h_ratio.SetTitle("")
    h_ratio.GetYaxis().SetTitle("Data / Postfit")
    h_ratio.GetYaxis().SetNdivisions(505)
    h_ratio.GetYaxis().SetTitleSize(20)
    h_ratio.GetYaxis().SetTitleFont(42)
    h_ratio.GetYaxis().SetTitleOffset(1.55)
    h_ratio.GetYaxis().SetLabelFont(42)
    h_ratio.GetYaxis().SetLabelSize(15)
    h_ratio.GetYaxis().SetRangeUser(0.85, 1.15)

    h_ratio.GetXaxis().SetTitle("Observable [units]")
    h_ratio.GetXaxis().SetTitleSize(20)
    h_ratio.GetXaxis().SetTitleFont(42)
    h_ratio.GetXaxis().SetTitleOffset(3.0)
    h_ratio.GetXaxis().SetLabelFont(42)
    h_ratio.GetXaxis().SetLabelSize(15)

    h_ratio.SetMarkerStyle(20)
    return h_ratio


def draw_postfit_canvas(data, postfit, chi2_hist, ratio_hist):
    c = ROOT.TCanvas()
    pad1 = ROOT.TPad("pad1", "top pad", 0, 0.3, 1, 1.0)
    pad1.SetBottomMargin(0)  # no x-axis labels on top pad
    pad1.Draw()
    pad1.cd()
    data.Draw()
    postfit.Draw("same c")

    legend = ROOT.TLegend(0.65, 0.7, 0.88, 0.88)
    legend.AddEntry(data, "Data", "lep")
    legend.AddEntry(postfit, "Postfit", "l")
    legend.Draw()

    text = ROOT.TLatex()
    text.SetTextSize(0.04)
    text.SetTextFont(42)
    text.SetNDC()
    rchi2 = chi2_hist.GetBinContent(6)
    text.DrawLatex(0.65, 0.55, f"#chi^{{2}}/ndof = {rchi2:.3f}")
    c.cd()

    pad2 = ROOT.TPad("pad2", "bottom pad", 0, 0.05, 1, 0.3)
    pad2.SetTopMargin(0)
    pad2.SetBottomMargin(0.3)
    pad2.Draw()
    pad2.cd()

    ratio_hist.Draw("E1")

    c.Update()
    return c


def main(argv=None):
    ROOT.gStyle.SetOptStat(0)
    ROOT.gROOT.SetBatch(True)

    args = parse_args(argv)

    histograms, postfit_file = load_postfit_histograms(args.inputFile)
    ratio_hist = build_ratio_histogram(histograms.data, histograms.postfit)
    canvas = draw_postfit_canvas(histograms.data, histograms.postfit, histograms.chi2, ratio_hist)

    canvas.SaveAs(args.output)
    postfit_file.Close()


if __name__ == "__main__":
    main()
