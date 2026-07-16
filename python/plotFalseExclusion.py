import sys, ROOT, math, glob, os
from color import getColorSteps

def getMode(h):
    numBins = h.GetXaxis().GetNbins();
    max_bin_content = -1
    max_bin_center = -1
    for i in range (numBins+1):
        #print h.GetBinContent(i), h.GetBinCenter(i)
        if h.GetBinContent(i) > max_bin_content:
            max_bin_content = h.GetBinContent(i)
            max_bin_center  = h.GetBinCenter(i)

    return max_bin_center

ROOT.gROOT.SetStyle("ATLAS")

if len(sys.argv) > 1:
    inpath = sys.argv[1]
else:
    inpath = "../TestData/DummyCoverageTest.root"

infile = ROOT.TFile(inpath)

graphs_lim = {}
for k in infile.GetListOfKeys():
    name = k.GetName()
    g = infile.Get(name)
    if not isinstance(g, ROOT.TGraph):
        continue

    graphs_lim[g.GetTitle()] = g
    print "adding", g.GetTitle()

################################################

x_min = 0
x_max = 0

graphs_frac_above = {}
graphs_frac_below = {}
for mass, graph in graphs_lim.iteritems():
    above = {}
    total = {}
    ninj_list = []
    graphs_frac_above[mass] = ROOT.TGraphErrors();
    graphs_frac_below[mass] = ROOT.TGraphErrors();
    for n in range(graph.GetN()):
        ninj = graph.GetX()[n]
        ulim = graph.GetY()[n]
        if ninj not in ninj_list: ninj_list.append(ninj)
        #print mass, n, ninj, ulim
        if ninj not in above: above[ninj] = 0
        if ninj not in total: total[ninj] = 0
        total[ninj] += 1
        if ulim > ninj:
            above[ninj] += 1
    ninj_list.sort()
    for n in ninj_list:
        value = above[n]*1./total[n]
        error = math.sqrt( (above[n]+1.)*(above[n]+2.)/(total[n]+2.)/(total[n]+3.) - (above[n]+1.)**2/(total[n]+2.)**2 )
        graphs_frac_above[mass].SetPoint(graphs_frac_above[mass].GetN(), n, value )
        graphs_frac_above[mass].SetPointError(graphs_frac_above[mass].GetN()-1, 0, error)
        below = total[n] - above[n]
        value = below*1./total[n]
        error = math.sqrt( (below+1.)*(below+2.)/(total[n]+2.)/(total[n]+3.) - (below+1.)**2/(total[n]+2.)**2 )
        graphs_frac_below[mass].SetPoint(graphs_frac_below[mass].GetN(), n, value )
        graphs_frac_below[mass].SetPointError(graphs_frac_below[mass].GetN()-1, 0, error)
        
        if n > x_max:
            x_max = 1.1*n
        if n < x_min:
            x_min = 1.1*n


canvas=ROOT.TCanvas("c","c", 900, 600)
canvas.SetRightMargin(0.10)
# canvas.SetLogx(1)
#canvas.SetLogy(1)
ROOT.gStyle.SetLegendFillColor(0)
ROOT.gStyle.SetLegendBorderSize(0)
ROOT.gStyle.SetLegendFont(43)
ROOT.gStyle.SetLegendTextSize(25)
ROOT.gStyle.SetOptStat(0)

# legend = ROOT.TLegend(0.18,0.60,0.62,0.90)
legend = ROOT.TLegend(0.45,0.25,0.87,0.60)
# legend.AddEntry(0,"Window half-width = 13 (J75)","")
# legend.AddEntry(0,"Window half-width = 9 (J100)","")

text = "global fit"
if "four" in inpath:
    text += " 4 par"
if "five" in inpath:
    text += " 5 par"
if "nloFit" in inpath:
    text = "NLOFit"

lumi = 29
if "lumi" in inpath:
    try:
        lumi=int(inpath.split("lumi")[0].split("_")[-1])
    except:
        pass
    text2 = ", %d fb^{-1}" % lumi


legend.AddEntry(0,text+text2,"")
legend.SetBorderSize(0)
masses = sorted(graphs_lim.keys())
colors = getColorSteps(len(masses))
i = 0
axisExists = 0
for mass in masses:
    print i, mass
    # graph = graphs_frac_above[mass]
    # graph.SetMarkerStyle(ROOT.kOpenCircle)
    # graph.SetMarkerSize(1)
    # graph.SetMarkerColor(colors[i])
    # graph.SetLineColor(colors[i])
    # graph.SetLineWidth(2)
    # graph.SetLineStyle(ROOT.kDotted)

    graph_below = graphs_frac_below[mass]
    graph_below.SetMarkerStyle(ROOT.kFullCircle)
    graph_below.SetMarkerSize(1)
    graph_below.SetMarkerColor(colors[i])
    graph_below.SetLineColor(colors[i])
    graph_below.SetLineWidth(2)
    legend.AddEntry(graph_below,mass)

    i += 1

    if graph_below.GetN() == 0:
        continue

    if not axisExists:
        graph_below.Draw("APEL SAME")
        graph_below.GetYaxis().SetTitle("False exclusion rate")
        graph_below.GetXaxis().SetTitle("Injected signal events")
        graph_below.GetXaxis().SetLimits(x_min,x_max)
        graph_below.GetYaxis().SetRangeUser(-0.,1.1)
        graph_below.Draw("APEL")
        canvas.Update()
        axisExists = 1
    else:
        graph_below.Draw("PEL")
    # graph_below.Draw("PEL")

    line = ROOT.TLine(x_min, 0.05, x_max, 0.05)
    line.SetLineWidth(2)
    line.SetLineStyle(7)
    line.SetLineColor(ROOT.kGray+1)
    line.Draw()

legend.Draw()
canvas.Update()
# canvas.Print("FalseExclusionRate.png")
canvas.Print(os.path.basename(inpath).replace(".root", ".png"))


raw_input("Wait...")
