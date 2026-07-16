#!/bin/python
import ROOT
from ROOT import RooWorkspace
#import ATLASStyle
#ATLASStyle.AtlasStyle()
#%%%%%%
#%%%%%%
#%%%%%%
#%%%%%%
#%%%%%%

def makePlot(frame, frame2, frame3):
    c = ROOT.TCanvas("c1","c1",600,600)
    c.SetBottomMargin(0)
    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.5, 1, 1.0)
    pad1.SetBottomMargin(0) #Upper and lower plot are joined
    pad1.Draw()

    pad1.cd()
    #pad1.SetLeftMargin(0.15)
    #frame.GetYaxis().SetTitleOffset(1.6)
    frame.Draw()
    frame.GetYaxis().SetTitleOffset(1.15)
    frame.GetYaxis().SetRangeUser(10,1000000)
    pad1.SetLogy()
    pad1.SetLogx()

    '''datahist.SetMarkerColor(ROOT.kBlue);
    datahist.SetLineColor(ROOT.kBlue);
    datahist.SetMarkerStyle(ROOT.kOpenCircle);
    datahist.SetMarkerSize(1.5);
    datahist.Draw("sameP");'''

    '''datahist_scaled.SetMarkerColor(ROOT.kRed);
    datahist_scaled.SetLineColor(ROOT.kRed);
    datahist_scaled.SetMarkerStyle(ROOT.kOpenCircle);
    datahist_scaled.SetMarkerSize(1.5);
    datahist_scaled.Draw("sameP");'''

    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.3, 1, 0.5);
    pad2.SetTopMargin(0);
    pad2.SetBottomMargin(0.0)
    #pad2.SetLeftMargin(0.15)
    pad2.Draw()
    pad2.cd()
    pad2.SetLogx()

    #frame2.GetYaxis().SetTitleOffset(1.6)
    frame2.GetYaxis().SetTitle("Residual Distribution")
    frame2.GetYaxis().SetLabelSize(0.1)
    frame2.GetYaxis().SetTitleOffset(0.45)
    frame2.GetYaxis().SetTitleSize(0.1)
    frame2.Draw()


    #f2 = ROOT.TFile("../test/200519_29p3invfb_J75DataitteddWithGlobFit_NominalBin_400_2079_tr1.root")
    #hdatatest = f2.Get("TriggerJets_J75_yStar03_mjj_2016binning_TLArange_data")
    #f2 = ROOT.TFile("../test/200519_29p3invfb_J75DataitteddWithGlobFit_FineBin_400_2079_2GeV.root")
    #hdatatest = f2.Get("TriggerJets_J75_yStar03_mjj_finebinned_all_data")
    #hbkgtest = f2.Get("BkgTemplate")
    #hdatatest.Add(hbkgtest,-1)
    #hdatatest.Draw("hist+same")

    c.cd()
    pad3 = ROOT.TPad("pad3", "pad3", 0, 0.1, 1, 0.3);
    pad3.SetTopMargin(0);
    pad3.SetBottomMargin(0.25)
    #pad3.SetLeftMargin(0.15)
    pad3.Draw()
    pad3.cd()
    pad3.SetLogx()

    #pad3.SetLeftMargin(0.15)
    ROOT.gStyle.SetOptTitle(0)

    frame3.GetYaxis().SetTitleOffset(0.45)
    frame3.GetXaxis().SetTitleOffset(1.1)
    frame3.GetXaxis().SetMoreLogLabels()
    frame3.GetYaxis().SetTitle("Pull Distribution")
    frame3.GetXaxis().SetTitle("Mass [GeV]")
    frame3.GetXaxis().SetLabelSize(0.1)
    frame3.GetXaxis().SetTitleSize(0.1)
    frame3.GetYaxis().SetLabelSize(0.1)
    frame3.GetYaxis().SetTitleSize(0.1)
    frame3.Draw()

    c.SaveAs("FitTests.pdf")

def makePlotWithHist(frame, frame2, frame3):

    #Juno
    #f2 = ROOT.TFile("200709_3p2invfb_J75DataFineBinFitteddWithGlobFit_400_2079_tr1.root")
    #Emma/Juno, but 2 GeV bins
    #f2 = ROOT.TFile("200519_29p3invfb_J75DataitteddWithGlobFit_FineBin_400_2079_2GeV.root")
    #Juno v2
    f2 = ROOT.TFile("SampleFiles/200709_tr3_J75DataFineBinFitteddWithGlobFit_400_2079_tr1.root")

    hdatatest = f2.Get("TriggerJets_J75_yStar03_mjj_finebinned_all_data")
    hbkgtest = f2.Get("BkgTemplate")

    c = ROOT.TCanvas("c1","c1",600,600)
    c.SetBottomMargin(0)
    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.5, 1, 1.0)
    pad1.SetBottomMargin(0) #Upper and lower plot are joined
    pad1.Draw()

    pad1.cd()
    #pad1.SetLeftMargin(0.15)
    #frame.GetYaxis().SetTitleOffset(1.6)
    frame.Draw()
    frame.GetYaxis().SetTitleOffset(1.15)
    frame.GetYaxis().SetRangeUser(10,1000000)
    pad1.SetLogy()
    pad1.SetLogx()

    hbkgtest.SetMarkerColor(ROOT.kBlue);
    hbkgtest.SetLineColor(ROOT.kBlue);
    #hbkgtest.SetMarkerStyle(ROOT.kOpenCircle);
    #hbkgtest.SetMarkerSize(1.5);
    hbkgtest.Draw("sameHIST");

    '''datahist_scaled.SetMarkerColor(ROOT.kRed);
    datahist_scaled.SetLineColor(ROOT.kRed);
    datahist_scaled.SetMarkerStyle(ROOT.kOpenCircle);
    datahist_scaled.SetMarkerSize(1.5);
    datahist_scaled.Draw("sameP");'''

    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.3, 1, 0.5);
    pad2.SetTopMargin(0);
    pad2.SetBottomMargin(0.0)
    #pad2.SetLeftMargin(0.15)
    pad2.Draw()
    pad2.cd()
    pad2.SetLogx()

    #frame2.GetYaxis().SetTitleOffset(1.6)
    frame2.GetYaxis().SetTitle("Residual Distribution")
    frame2.GetYaxis().SetLabelSize(0.1)
    frame2.GetYaxis().SetTitleOffset(0.45)
    frame2.GetYaxis().SetTitleSize(0.1)
    frame2.Draw()

    hdatatest.Add(hbkgtest,-1)
    hdatatest.Draw("hist+same")

    c.cd()
    pad3 = ROOT.TPad("pad3", "pad3", 0, 0.1, 1, 0.3);
    pad3.SetTopMargin(0);
    pad3.SetBottomMargin(0.25)
    #pad3.SetLeftMargin(0.15)
    pad3.Draw()
    pad3.cd()
    pad3.SetLogx()

    #pad3.SetLeftMargin(0.15)
    ROOT.gStyle.SetOptTitle(0)

    frame3.GetYaxis().SetTitleOffset(0.45)
    frame3.GetXaxis().SetTitleOffset(1.1)
    frame3.GetXaxis().SetMoreLogLabels()
    frame3.GetYaxis().SetTitle("Pull Distribution")
    frame3.GetXaxis().SetTitle("Mass [GeV]")
    frame3.GetXaxis().SetLabelSize(0.1)
    frame3.GetXaxis().SetTitleSize(0.1)
    frame3.GetYaxis().SetLabelSize(0.1)
    frame3.GetYaxis().SetTitleSize(0.1)
    frame3.Draw()

    c.SaveAs("SampleOutputs/FitTestsHist.pdf")

#%%%%%%
#%%%%%%
#%%%%%%
#%%%%%%
#%%%%%%

input_file = ROOT.TFile.Open("SampleFiles/20200701_bkgonly_test_dijetTLA_J75yStar03_v01.root")

input_file.ls()

this_workspace = input_file.Get("combWS")
#this line is needed as everything needs called by name, and this lists everything that is inside the workspace
print("\n***Printing workspace content [using Print('V')]:")
this_workspace.Print("V")

#getting the overall model -> points to having _modelSB_J75yStar03 inside
#print("\n***Getting the overall pdf [_model_J75yStar03, using '.pdf']:")
#this_model = this_workspace.pdf("_model_J75yStar03")
#this_model.Print("V")

#getting the SB model -> points to having pdf__background_J75yStar03 and pdf__signal_J75yStar03 inside
#print("\n***Getting the overall SB pdf [_modelSB_J75yStar03, using '.pdf']:")
#this_model = this_workspace.pdf("_modelSB_J75yStar03")
#this_model.Print("V")

print("\n***Getting the background pdf [pdf__background_J75yStar03, using '.pdf']:")
bkg_pdf = this_workspace.pdf("pdf__background_J75yStar03")
bkg_pdf.Print("V")

print("\n***Getting the signal pdf [pdf__signal_J75yStar03, using '.pdf']:")
signal_pdf = this_workspace.pdf("pdf__signal_J75yStar03")
signal_pdf.Print("V")

print("\n***Getting the data [combData, using '.data']:")
this_data = this_workspace.data("combData")
this_data.Print("V")

#bkg_pdf.fitTo(this_data)

c = ROOT.TCanvas("c1","c1",600,600)
c.cd()
frame_main = this_workspace.var('obs_x_channel').frame(ROOT.RooFit.Title("Fit tests"))
frame_main.Draw()

#plot the data and the fit
this_data.plotOn(frame_main, ROOT.RooFit.MarkerColor(ROOT.kBlack), ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.MarkerStyle(ROOT.kOpenCircle), ROOT.RooFit.MarkerSize(0.01))
bkg_pdf.plotOn(frame_main, ROOT.RooFit.LineColor(ROOT.kYellow),ROOT.RooFit.LineWidth(3))
#plot the fit parameters as well
bkg_pdf.paramOn(frame_main,ROOT.RooFit.Layout(0.65))

#residuals panel
h_residuals = frame_main.residHist()
frame_residuals = this_workspace.var('obs_x_channel').frame(ROOT.RooFit.Title(""))
frame_residuals.addPlotable(h_residuals,"P")

#pulls panel
h_pulls = frame_main.pullHist()
frame_pulls = this_workspace.var('obs_x_channel').frame(ROOT.RooFit.Title(""))
frame_pulls.addPlotable(h_pulls,"HIST")

#makePlot(frame_main, frame_residuals, frame_pulls)

#for now, this function is going to be also pulling the histogram
makePlotWithHist(frame_main, frame_residuals, frame_pulls)
