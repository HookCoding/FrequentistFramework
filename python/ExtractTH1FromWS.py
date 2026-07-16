#!/bin/python

import ROOT
from ROOT import RooWorkspace

input_file = ROOT.TFile.Open("20200701_bkgonly_test_dijetTLA_J75yStar03_v01.root", "r")
input_file.ls()

this_workspace = input_file.Get("combWS")
print("\n***Printing workspace content [using Print('V')]:")
this_workspace.Print("V")
print("\n***Printing workspace content [using '.ls']:")
this_workspace.ls()

#datasets
#--------
#RooDataSet::combData(obs_x_channel,channellist)
#RooDataSet::asimovData_0(obs_x_channel,channellist)
#RooDataSet::asimovData_1_prefit(obs_x_channel,channellist)
#RooDataSet::asimovData_1(obs_x_channel,channellist)

this_roodataset = this_workspace.data("asimovData_1")
print("\n***Printing dataset content:")
this_roodataset.Print("V")

c=ROOT.TCanvas()
frame = this_workspace.var('obs_x_channel').frame(ROOT.RooFit.Title("test title"))
frame.Draw()
this_roodataset.plotOn(frame)
c.SaveAs("test.png")
#w.data("").plotOn(frame)

#
# #get the RooArgSet (=multiple RooAbsArgs) corresponding to the 0th position
# this_xVariable = this_roodataset.get(0)
#
# print("\n***Printing variable content:")
# this_xVariable.Print("V")
#
# #get the RooArgSet (=multiple RooAbsArgs)
# this_rooDataHist = ROOT.RooDataHist("this_rooDataHist", "this_RooDataHist", this_xVariable)
# print("\n***Printing dataHist content:")
# this_rooDataHist.Print("V")
#
# #is this sensible?
# this_rooDataHist.createHistogram("obs_x_channel").Draw()
#
# this_TH1 = this_rooDataHist.createHistogram("obs_x_channel",1679)
# #this_TH1.Print("all") #empty?
#
# #    data = ROOT.RooDataHist("data","data",ROOT.RooArgList(w.var('mass')),datahist);
#
#
# #RooDataHist dh("dh","binned version of d",RooArgSet(x,y),d) ;
#
# #this_xVariable.get("RooRealVar")
#
# #this_TH1 = this_roodataset.createHistogram("obs_x_channel","obs_x_channel") #ROOT.RooFit.Binning(3000,0,3000))
