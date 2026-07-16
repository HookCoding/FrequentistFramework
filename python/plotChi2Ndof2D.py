#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse

ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasLabels.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasStyle.C")
ROOT.gROOT.LoadMacro("../atlasstyle-00-04-02/AtlasUtils.C")

def main(args):
    ROOT.SetAtlasStyle()

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infiles', dest='infiles', nargs='+', type=str, default='', help='Input file name')
    parser.add_argument('--fctname', dest='fctname', type=str, default='fit', help='Input TF1 name')
    parser.add_argument('--pvalhist', dest='pvalhist', type=str, default='pval', help='Name of pval hist')
    parser.add_argument('--outfile', dest='outfile', type=str, default='chi2_2D.root', help='Output file name')

    args = parser.parse_args(args)

    # dict_chi2 = {}
    dict_ndof = {}
    dict_ndoferr = {}
    dict_pval = {}

    x_vals = set()
    y_vals = set()

    for path in args.infiles:
        f_in = ROOT.TFile(path, "READ")
        
        try:
            x=re.findall(r'constr\d+', path)[1]
            x=int(x[6:])
            y=re.findall(r'constr\d+', path)[0]
            y=int(y[6:])
            
            if x == 10000:
                continue
        except:
            print "ERROR: Cannot extract constraint from file name"
            return 1
        
        x_vals.add(x)
        y_vals.add(y)

        f1_in = f_in.Get(args.fctname)
        # dict_chi2[(x,y)] = h_in.GetBinContent(args.histbin)
        dict_ndof[(x,y)] = f1_in.GetParameter(0)
        dict_ndoferr[(x,y)] = f1_in.GetParError(0)
        # dict_pval[(x,y)] = h_in.GetBinContent(args.pvalbin)

        try:
            h_pval=f_in.Get(args.pvalhist)
            dict_pval[(x,y)] = h_pval.GetMean()
        except:
            pass

        f_in.Close()

    x_vals = sorted(x_vals)
    y_vals = sorted(y_vals)

    h2_ndof = ROOT.TH2D("h2_ndof", "n.d.f.;Fit constraint term;PD constraint term;n.d.f.", len(x_vals), 0, len(x_vals), len(y_vals), 0, len(y_vals))
    h2_pval = ROOT.TH2D("h2_pval", "#it{p}(#chi^{2});Fit constraint term;PD constraint term;mean #it{p}(#chi^{2})", len(x_vals), 0, len(x_vals), len(y_vals), 0, len(y_vals))

    for i,x in enumerate(x_vals):
        h2_ndof.GetXaxis().SetBinLabel(i+1, str(x))
        h2_pval.GetXaxis().SetBinLabel(i+1, str(x))

    for i,y in enumerate(y_vals):
        h2_ndof.GetYaxis().SetBinLabel(i+1, str(y))
        h2_pval.GetYaxis().SetBinLabel(i+1, str(y))

        
    for i,x in enumerate(x_vals):
        for j,y in enumerate(y_vals):
            if x > y:
                continue
            try:
                b = h2_ndof.GetBin(i+1, j+1)
                h2_ndof.SetBinContent(b, dict_ndof[(x,y)])
                h2_ndof.SetBinError(b, dict_ndoferr[(x,y)])
            except:
                pass

            try:
                b = h2_pval.GetBin(i+1, j+1)
                h2_pval.SetBinContent(b, dict_pval[(x,y)])
            except:
                pass
         

    c1 = ROOT.TCanvas("c1", "c1", 800, 600)
    c1.cd()
    # c1.SetLogz()
    c1.SetRightMargin(0.15)
    c1.SetLeftMargin(0.15)
    # c1.SetTickx(1)
    # c1.SetTicky(0)

    h2_ndof.SetMinimum(30)
    h2_ndof.SetMaximum(50)


    ROOT.gStyle.SetTextFont(42);
    ROOT.gStyle.SetPaintTextFormat("4.1f")

    # h2_ndof.Draw("colz")
    h2_ndof.Draw("colz0,texte")
    h2_ndof.SetMarkerColor(ROOT.kBlack);
    h2_ndof.SetMarkerSize(1.0);

    l = ROOT.TLatex()
    l.SetTextAlign(31)
    l.SetNDC()
    l.SetTextColor(1)
    l.SetTextFont(43)

    ROOT.ATLASLabel(0.48, 0.20, "Work in progress", 11)
    l.DrawLatex(0.81, 0.26, "29.3 fb^{-1}, 2016 J100");
    l.DrawLatex(0.81, 0.32, "NLOFit");
    
    c2 = ROOT.TCanvas("c2", "c2", 800, 600)
    c2.cd()
    # c2.SetLogz()
    c2.SetRightMargin(0.15)
    c2.SetLeftMargin(0.15)

    h2_pval.SetMinimum(0.)
    h2_pval.SetMaximum(1.)

    ROOT.gStyle.SetPaintTextFormat("4.2f")

    h2_pval.Draw("colz0,text")
    h2_pval.SetMarkerColor(ROOT.kBlack);
    h2_pval.SetMarkerSize(1.0);

    ROOT.ATLASLabel(0.48, 0.20, "Work in progress", 11)
    l.DrawLatex(0.81, 0.26, "29.3 fb^{-1}, 2016 J100");
    l.DrawLatex(0.81, 0.32, "NLOFit");


    # # Scale g_pval to plot in same canvas
    # # rightmax = 1.1*max(dict_pval.values())
    # # rightmin = 0.9*min(dict_pval.values())
    # rightmin = 1.E-5
    # rightmax = 1.
    # leftmin = 0.
    # leftmax = 90.
    # logx = True
    # logyright = True

    # g_chi2.GetYaxis().SetRangeUser(leftmin,leftmax)

    # c.Update()

    # if logyright:
    #     # log:
    #     scale = (leftmax-leftmin)/(ROOT.TMath.Log10(rightmax)-ROOT.TMath.Log10(rightmin))
    #     offset = leftmax - scale*ROOT.TMath.Log10(rightmax)
    # else:
    #     # linear:
    #     scale = (leftmax-leftmin)/(rightmax-rightmin)
    #     offset = leftmax - scale*rightmax

    # g_pval.SetLineColor(ROOT.kRed)
    # g_pval.SetMarkerColor(ROOT.kRed)

    # for x in sorted(dict_pval):
    #     if logyright:
    #         y=ROOT.TMath.Log10(dict_pval[x])*scale + offset
    #     else:
    #         y=dict_pval[x]*scale + offset
    #     g_pval.SetPoint(g_pval.GetN(),x,y)

    # c.Update()

    # g_pval.Draw("PL")
    
    # if logyright:
    #     axis = ROOT.TGaxis(10**ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin(),
    #                        10**ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax(),rightmin,rightmax,510,"+LG")
    # else:
    #     axis = ROOT.TGaxis(ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin(),
    #                        ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax(),0,rightmax,510,"+L")

    # axis.SetLineColor(ROOT.kRed)
    # axis.SetLabelColor(ROOT.kRed)
    # axis.SetLabelSize(ROOT.gStyle.GetLabelSize("y"))
    # axis.SetLabelFont(ROOT.gStyle.GetLabelFont("y"))
    # axis.SetTitleFont(ROOT.gStyle.GetTitleFont("y"))
    # axis.SetTitleSize(ROOT.gStyle.GetTitleSize("y"))
    # axis.Draw()
    
    # c.Update()

    # ROOT.ATLASLabel(0.53, 0.20, "Work in progress", 11)
    # ROOT.myText(0.86, 0.26, 1, "NLOFit", 31)
    # ROOT.myText(0.86, 0.32, 1, "29.3 fb^{-1}, 2016 J100", 31)

    # # l=ROOT.TLegend(0.65, 0.60, 0.88, 0.78)
    # l=ROOT.TLegend(0.25, 0.185, 0.40, 0.365)
    # l.AddEntry(g_chi2, "#chi^{2}", "lp")
    # l.AddEntry(g_ndof, "n.d.f.", "lp")
    # l.AddEntry(g_pval, "#chi^{2} #it{p}-value", "lp")
    # l.Draw()

    c2.Update()

    raw_input("press enter")

    c2.Print(args.outfile.replace(".root", ".png"))
    c2.Print(args.outfile.replace(".root", ".pdf"))

    # f_out = ROOT.TFile(args.outfile, "RECREATE")
    # f_out.cd()
    
    # g_chi2.Write("g_chi2")
    # g_ndof.Write("g_ndof")
    # g_pval.Write("g_pval")

    # f_out.Close()


if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
