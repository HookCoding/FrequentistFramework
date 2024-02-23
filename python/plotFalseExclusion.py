import sys, ROOT, math, glob, os, re, argparse
from array import array
from color import getColorSteps

ROOT.gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("$_DIRXMLWSBUILDER/../atlasstyle-00-04-02/AtlasUtils.C")

ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

ROOT.TCandle.SetBoxRange(0.68)
ROOT.TCandle.SetWhiskerRange(0.90)

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    # parser.add_argument('--input_is_spurious', dest='input_is_spurious', action='store_true', help='Input is already a spurious signal graph. Otherwise a file created with createExtractionGraphs.py is expected.')
    parser.add_argument('--width', dest='width', type=int, default=None, help='Only plot given width')
    parser.add_argument('--means', dest='means', type=int, nargs='+', default=None, help='Means to draw in plot')

    args, paths = parser.parse_known_args(args)
    
    inpath = paths[0]
    infile = ROOT.TFile(inpath)
    
    graphs_lim = {}
    for k in infile.GetListOfKeys():
        name = k.GetName()
        g = infile.Get(name)
        if not isinstance(g, ROOT.TGraph):
            continue
            
        if not "g1_limit" in name:
            # only care for observed limits
            continue
            
        if not name.endswith("_%d" % args.width):
            continue

        searchstring =r'_(\d+)_(\d+)$'
        res=re.search(searchstring, name)
        m=int(res.group(1))
        w=int(res.group(2))
        g.SetTitle("m_{G} = %.0f GeV" % m)

        if args.means and not m in args.means:
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
    h1_all_limits = {}
    
    masses = natural_sort(graphs_lim.keys())

    print("outfile:", inpath.replace(".root", "_hists_width%d.root" % args.width))
    fout = ROOT.TFile(inpath.replace(".root", "_hists_width%d.root" % args.width), "RECREATE")
    
    for mass in masses:
        graph = graphs_lim[mass]
        above = {}
        total = {}
        ninj_list = []
        graphs_frac_above[mass] = ROOT.TGraphErrors();
        graphs_frac_below[mass] = ROOT.TGraphErrors();
    
        y_min = -1
        y_max = 0

        h1_limits = ROOT.TH1D("limits_mean%s_width%d" % (mass, args.width), "Observed limits on nsig_mean%s_width%d;95%% limit / #sqrt{B};#toys" % (mass, args.width), 2000, 0, 100)
        h1_limits.SetDirectory(0)
    
        for n in range(graph.GetN()):
            ninj = graph.GetX()[n]
            ulim = graph.GetY()[n]
            # print(ulim)
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

            if ninj == 3:
                h1_limits.Fill(ulim)

        fout.cd()
        h1_limits.Write("limits_mean%s_width%d" % (mass, args.width))
    
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
        bin_width = ninj_list[-1] / 12. if ninj_list[-1] > 0. else 1
    
        if bin_edges == []:
            #only set it once so all histograms have same binning. Necessary for the THStack later
     
            for n in ninj_list:
                bin_edges.append(n - 0.5*bin_width)
                bin_edges.append(n + 0.5*bin_width)
            
            bin_edges = array('d', bin_edges)
    
    
        h2_all_points[mass] = ROOT.TH2D("h2_"+str(mass), "", len(bin_edges)-1, bin_edges, 1000, 0, 5*bin_edges[-1]);
        h2_all_points[mass].SetDirectory(0)
    
        for n in range(graph.GetN()):
            ninj = graph.GetX()[n]
            ulim = graph.GetY()[n]
            if math.isnan(ulim):
                ulim = 0.
    
            h2_all_points[mass].Fill(ninj, ulim)
        
    fout.Close()
    
    canvas=ROOT.TCanvas("c","c", 800, 600)
    # canvas.SetRightMargin(0.10)

    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.3, 1, 1.0)
    pad1.SetBottomMargin(0.005) #Upper and lower plot are joined
    pad1.Draw()
    
    pad1.cd()
    
    # legend = ROOT.TLegend(0.15,0.6,0.75,0.89)
    legend = ROOT.TLegend(0.20,0.55,0.75,0.90)
    legend.SetNColumns(2)
    
    if "four" in inpath:
        text = "4-par fit"
    elif "five" in inpath:
        text = "5-par fit"
    elif "six" in inpath:
        text = "6-par fit"
    elif "seven" in inpath:
        text = "7-par fit"
    elif "eight" in inpath:
        text = "8-par fit"
    elif "nine" in inpath:
        text = "9-par fit"
    elif "nloFit" in inpath or "nlofit" in inpath:
        text = "NLOFit"
    
    lumi = 132000
    trig = "J100"
    if "lumi" in inpath:
        try:
            lumi=int(inpath.split("lumi")[0].split("_")[-1])
        except:
            pass

    if "J50" in inpath:
        lumi = 15000
        trig = "J50"
    text2 = ", %.1f fb^{-1} %s PD" % (lumi/1000, trig)
    
    colors = getColorSteps(len(masses))
    
    print(h2_all_points)

    hs = ROOT.THStack("hs","")
    for i,mass in enumerate(masses):
    
        h2_all_points[mass].SetLineWidth(2)
        h2_all_points[mass].SetLineColor(colors[i])
        h2_all_points[mass].SetMarkerColor(colors[i])
        legend.AddEntry(h2_all_points[mass], mass)
        
        # hs.Add(h2_all_points[mass], "CANDLEX(00111011)") #(zhpawMmb)
        hs.Add(h2_all_points[mass], "CANDLEX(00001011)") #(zhpawMmb)

    legend.AddEntry(0,"#sigma_{G}/m_{G} = %.2f" % (args.width/100.),"")
    
    # hs.Draw("CANDLEX(00111011)")
    hs.Draw("CANDLEX(00001011)")
    hs.GetYaxis().SetLimits(-0.5,14.)
    hs.GetXaxis().SetTitle("S_{inj} / #sqrt{B}")
    hs.GetYaxis().SetTitle("95% limit / #sqrt{B}")
    hs.GetYaxis().SetTitleOffset(1.5)
    hs.GetXaxis().SetTitleOffset(2)
    hs.GetXaxis().SetLabelOffset(2)
       
    line = ROOT.TLine(0, 0, bin_edges[-1], bin_edges[-1])
    line.SetLineWidth(2)
    line.SetLineStyle(7)
    line.SetLineColor(ROOT.kGray+1)
    line.Draw()
    
    legend.Draw()

    # ROOT.ATLASLabel(0.58, 0.20, "Work in progress", 13)
    # ROOT.myText(0.58, 0.25, 1, text+text2, 13)
    ROOT.ATLASLabel(0.57, 0.10, "Work in progress", 13)
    ROOT.myText(0.91, 0.20, 1, text+text2, 33)


    canvas.Update()
    # canvas.Print(os.path.basename(inpath).replace(".root", ".png"))
    
    
    canvas.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.3);
    pad2.SetTopMargin(0.01);
    pad2.SetBottomMargin(0.35)
    pad2.Draw()
    
    pad2.cd()
    
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
        # legend.AddEntry(graph_below,mass)
    
        i += 1
    
        if graph_below.GetN() == 0:
            continue
    
        if not axisExists:
            graph_below.Draw("APEL SAME")
            graph_below.GetYaxis().SetTitle("False excl. rate")
            graph_below.GetXaxis().SetTitle("S_{inj} / #sqrt{B}")
            graph_below.GetYaxis().SetNdivisions(505)
            # graph_below.GetXaxis().SetLimits(x_min,x_max)
            graph_below.GetXaxis().SetLimits(bin_edges[0],bin_edges[-1])
            graph_below.GetYaxis().SetRangeUser(0.,0.16)
            graph_below.GetYaxis().SetTitleOffset(1.5)
            graph_below.GetXaxis().SetTitleOffset(3.2)
            graph_below.Draw("APEL")
            canvas.Update()
            axisExists = 1
        else:
            graph_below.Draw("PEL")
    
        line2 = ROOT.TLine(bin_edges[0], 0.05, bin_edges[-1], 0.05)
        line2.SetLineWidth(2)
        line2.SetLineStyle(7)
        line2.SetLineColor(ROOT.kGray+1)
        line2.Draw()
    
    # legend2=legend.Clone()
    # legend2.SetX1NDC(0.2)
    # legend2.SetY1NDC(0.6)
    # legend2.SetX2NDC(0.6)
    # legend2.SetY2NDC(0.9)
    # legend2.Draw()    
    
    
    canvas.Print(inpath.replace(".root", "_width%d.pdf" % args.width))
    canvas.Print(inpath.replace(".root", "_width%d.svg" % args.width))
        
    # raw_input("Wait...")

if __name__ == "__main__":  
    # don't pass -b flag for root but keep -- flags for argparse
    args=[x for x in sys.argv[1:] if not (x.startswith("-") and not x.startswith("--"))]
    sys.exit(main(args))
