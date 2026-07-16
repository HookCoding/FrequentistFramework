import sys, ROOT, math, glob, os, re
from array import array
from color import getColorSteps

ROOT.TCandle.SetBoxRange(0.68)
ROOT.TCandle.SetWhiskerRange(0.95)

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

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
h2_all_points = {}
bin_edges = []

masses = natural_sort(graphs_lim.keys())

for mass in masses:
    graph = graphs_lim[mass]
    above = {}
    total = {}
    ninj_list = []
    graphs_frac_above[mass] = ROOT.TGraphErrors();
    graphs_frac_below[mass] = ROOT.TGraphErrors();

    y_min = -1
    y_max = 0

    for n in range(graph.GetN()):
        ninj = graph.GetX()[n]
        ulim = graph.GetY()[n]
        if math.isnan(ulim):
            ulim = 0.

        if ninj not in ninj_list: ninj_list.append(ninj)

        if ninj not in above: above[ninj] = 0
        if ninj not in total: total[ninj] = 0
        total[ninj] += 1
        if ulim > ninj:
            above[ninj] += 1
        if ulim > y_max:
            y_max = ulim
        if ulim < y_max:
            y_min = ulim

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

    # for candle plot:
    bin_width = ninj_list[-1] / 15. if ninj_list[-1] > 0. else 1

    if bin_edges == []:
        #only set it once so all histograms have same binning. Necessary for the THStack later
 
        for n in ninj_list:
            bin_edges.append(n - 0.5*bin_width)
            bin_edges.append(n + 0.5*bin_width)
        
        bin_edges = array('d', bin_edges)


    h2_all_points[mass] = ROOT.TH2D("h2_"+str(mass), "", len(bin_edges)-1, bin_edges, 1000, 0, 5*bin_edges[-1]);

    for n in range(graph.GetN()):
        ninj = graph.GetX()[n]
        ulim = graph.GetY()[n]
        if math.isnan(ulim):
            ulim = 0.

        h2_all_points[mass].Fill(ninj, ulim)
    
    

canvas=ROOT.TCanvas("c","c", 900, 600)
canvas.SetRightMargin(0.10)
# canvas.SetLogx(1)
#canvas.SetLogy(1)
ROOT.gStyle.SetLegendFillColor(0)
ROOT.gStyle.SetLegendBorderSize(0)
ROOT.gStyle.SetLegendFont(43)
ROOT.gStyle.SetLegendTextSize(20)
ROOT.gStyle.SetOptStat(0)

# legend = ROOT.TLegend(0.45,0.25,0.87,0.60)
legend = ROOT.TLegend(0.2,0.6,0.6,0.9)

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
        graph_below.GetXaxis().SetTitle("N_{inj} / #sqrt{N_{bkg}}")
        graph_below.GetXaxis().SetLimits(x_min,x_max)
        graph_below.GetYaxis().SetRangeUser(-0.,1.1)
        graph_below.Draw("APEL")
        canvas.Update()
        axisExists = 1
    else:
        graph_below.Draw("PEL")

    line = ROOT.TLine(x_min, 0.05, x_max, 0.05)
    line.SetLineWidth(2)
    line.SetLineStyle(7)
    line.SetLineColor(ROOT.kGray+1)
    line.Draw()

legend.Draw()
canvas.Update()
canvas.Print(os.path.basename(inpath).replace(".root", ".png"))

canvas2 = ROOT.TCanvas()

hs = ROOT.THStack("hs","")
for i,mass in enumerate(masses):

    h2_all_points[mass].SetLineColor(colors[i])
    h2_all_points[mass].SetMarkerColor(colors[i])

    hs.Add(h2_all_points[mass], "CANDLEX(00111011)") #(zhpawMmb)

hs.Draw("CANDLEX(00111011)")
hs.GetYaxis().SetLimits(0.,10.)
hs.GetXaxis().SetTitle("N_{inj} / #sqrt{N_{bkg}}")
hs.GetYaxis().SetTitle("95% limit / #sqrt{N_{bkg}}")
   
line = ROOT.TLine(0, 0, bin_edges[-1], bin_edges[-1])
line.SetLineWidth(2)
line.SetLineStyle(7)
line.SetLineColor(ROOT.kGray+1)
line.Draw()

legend2=legend.Clone()
legend2.SetX1NDC(0.2)
legend2.SetY1NDC(0.6)
legend2.SetX2NDC(0.6)
legend2.SetY2NDC(0.9)
legend2.Draw()    


canvas_name = os.path.basename(inpath).replace(".root", "_candleplot.png")
canvas2.Print(canvas_name)
    
#raw_input("Wait...")
