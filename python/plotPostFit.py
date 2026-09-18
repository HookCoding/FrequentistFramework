import ROOT
import argparse
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--inputFile', type=str, required=True)
parser.add_argument('-o', '--output', type=str, required=True)
parser.add_argument('-c', '--channel', type=str, default='Run3TLA',
                    help='Channel name, i.e. the directory inside the PostFit file '
                         '(Run3TLA for dijetisrTLA, J100yStar06 for dijetTLA)')
parser.add_argument('-l', '--label', type=str, default='',
                    help='Text drawn on the plot saying which fit this is, e.g. '
                         '"masked fit (BumpHunter window blinded)". Without it a reader cannot '
                         'tell a masked plot from an unmasked one. See KNOWN_ISSUES.md issue 48.')
args = parser.parse_args()

postfit_file = ROOT.TFile.Open(args.inputFile, "READ")
postfit = postfit_file.Get(args.channel+"/postfit")
data = postfit_file.Get(args.channel+"/data")
data.SetMarkerStyle(8)
data.SetMarkerSize(0.5)
data.SetMarkerColor(ROOT.kBlack)
data.SetLineWidth(0)
postfit.SetLineWidth(2)
postfit.SetLineColor(ROOT.kAzure+7)

c = ROOT.TCanvas()
pad1 = ROOT.TPad("pad1","top pad",0,0.3,1,1.0)
pad1.SetBottomMargin(0)  # no x-axis labels on top pad
pad1.Draw()
pad1.cd()
data.Draw()
postfit.Draw("same c")

legend = ROOT.TLegend(0.65,0.7,0.88,0.88)
legend.AddEntry(data,"Data","lep")
legend.AddEntry(postfit,"Postfit","l")
legend.Draw()

text = ROOT.TLatex()
text.SetTextSize(0.04)
text.SetTextFont(42)
text.SetNDC()
string = "#chi^{2}/ndof = "
h_rchi2 = postfit_file.Get(args.channel+"/chi2")
# Bin 2, not 6: ExtractPostfitFromWS.py writes chi2 in bin 1, chi2/ndof in bin 2 and the
# p-value in bin 6, and labels the axis accordingly. This read said 6 while the label said
# chi2/ndof, so every plot showed the p-value under the wrong name (KNOWN_ISSUES.md issue 45).
rchi2 = h_rchi2.GetBinContent(2)
string+= f"{rchi2:.3f}"
text.DrawLatex(0.65,0.55, string)

# Which fit this is. A run that fails the p(chi2) gate produces two PostFit files, and
# without this the two plots are indistinguishable. See KNOWN_ISSUES.md issue 48.
if args.label:
    text.DrawLatex(0.65, 0.60, args.label)
c.cd()

pad2 = ROOT.TPad("pad2","bottom pad",0,0.05,1,0.3)
pad2.SetTopMargin(0)
pad2.SetBottomMargin(0.3)
pad2.Draw()
pad2.cd()

# Ratio = data / postfit
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
h_ratio.GetYaxis().SetRangeUser(0.85,1.15)

h_ratio.GetXaxis().SetTitle("Observable [units]")
h_ratio.GetXaxis().SetTitleSize(20)
h_ratio.GetXaxis().SetTitleFont(42)
h_ratio.GetXaxis().SetTitleOffset(3.0)
h_ratio.GetXaxis().SetLabelFont(42)
h_ratio.GetXaxis().SetLabelSize(15)

h_ratio.SetMarkerStyle(20)
h_ratio.Draw("E1")

c.Update()


c.SaveAs(args.output)
postfit_file.Close()
