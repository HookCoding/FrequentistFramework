import ROOT, sys


#Declare observable x -- this determines the x axis
x= ROOT.RooRealVar("x","x",400,2079) ;

# set up frame object
frame = x.frame(ROOT.RooFit.Title("J75 Data")) ;

#import J75 data
datafilename = "../Input/data/dijetTLA/TLA2016_NominalUnblindedData.root"
# DSJ100yStar06_TriggerJets_J100_yStar06_mjj_2016binning_TLArange_data
datahistname = "Nominal/DSJ75yStar03_TriggerJets_J75_yStar03_mjj_2016binning_TLArange_data"
datafile = ROOT.TFile(datafilename,"READ")
datahist = datafile.Get(datahistname)

# put histogram into RooDataHist object
data = ROOT.RooDataHist("data","data",ROOT.RooArgList(x),datahist);


# Construct background pdf
p1 = ROOT.RooRealVar("p1", "p1", 0.1, -0.5, 1.5)
p2 = ROOT.RooRealVar("p2", "p2", 4.5, -10, 10)
p3 = ROOT.RooRealVar("p3", "p3", 21, -30, 20)
p4 = ROOT.RooRealVar("p4", "p4", -28, -40, 10)
fx = ROOT.RooGenericPdf("fx","fx","p1*TMath::Power(x/13000.,-1*p2)*TMath::Exp( -1*(p3*x/13000. + p4*TMath::Power(x/13000.,2)))",ROOT.RooArgList(x,p1,p2,p3,p4)) ;

fx.fitTo(data) ;

data.plotOn(frame) ;
fx.plotOn(frame) ;
fx.paramOn(frame,ROOT.RooFit.Layout(0.55)) ;


#Construct a histogram with the residuals of the data w.r.t. the curve
hresid = frame.residHist() 

#Construct a histogram with the pulls of the data w.r.t the curve
hpull = frame.pullHist() 

#Create a new frame to draw the residual distribution and add the distribution to the frame
frame2 = x.frame(ROOT.RooFit.Title("Residual Distribution")) ;
frame2.addPlotable(hresid,"P") ;

#Create a new frame to draw the pull distribution and add the distribution to the frame
frame3 = x.frame(ROOT.RooFit.Title("Pull Distribution")) ;
frame3.addPlotable(hpull,"P") ;

c = ROOT.TCanvas("c1","c1",900,300)
c.Divide(3) 
#c.cd(1)

c.cd(1)
ROOT.gPad.SetLeftMargin(0.15)
frame.GetYaxis().SetTitleOffset(1.6)
frame.Draw()
ROOT.gPad.SetLogy()

c.cd(2)
ROOT.gPad.SetLeftMargin(0.15)
frame2.GetYaxis().SetTitleOffset(1.6)
frame2.Draw()

c.cd(3)
ROOT.gPad.SetLeftMargin(0.15)
frame3.GetYaxis().SetTitleOffset(1.6)
frame3.Draw()

raw_input("Press Enter...")


