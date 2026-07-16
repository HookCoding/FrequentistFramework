import ROOT
from ROOT import TFile, TH1F, RooRealVar, RooDataHist, RooHistPdf, RooMomentMorph, RooArgList, RooPlot, TCanvas, RooArgSet

import numpy as np

def interpolate_mass(m:float):
    # Open your file containing histograms
    f_150 = TFile.Open("/afs/cern.ch/user/a/agekow/work/dijet-isr-tla-ntuple-analysis/hist-ZPrime150.root")
    f_400 = TFile.Open("/afs/cern.ch/user/a/agekow/work/dijet-isr-tla-ntuple-analysis/hist-ZPrime400.root")

    # Load TH1F histograms for different mass points
    # h_m125 = file.Get("h_m125")
    h_m150 = f_150.Get("mjj")
    # h_m200 = file.Get("h_m200")
    h_m400 = f_400.Get("mjj")

    # Define the mass variable
    x = RooRealVar("x", "x", 150, 1000)  # Adjust the range according to your histograms

    # Convert TH1F to RooDataHist
    # dh_m125 = RooDataHist("dh_m125", "dh_m125", RooArgList(x), h_m125)
    dh_m150 = RooDataHist("dh_m150", "dh_m150", RooArgList(x), h_m150)
    # dh_m200 = RooDataHist("dh_m200", "dh_m200", RooArgList(x), h_m200)
    dh_m400 = RooDataHist("dh_m400", "dh_m400", RooArgList(x), h_m400)

    # Create RooHistPdfs
    # pdf_m125 = RooHistPdf("pdf_m125", "pdf_m125", x, dh_m125)
    pdf_m150 = RooHistPdf("pdf_m150", "pdf_m150", RooArgSet(x), dh_m150)
    # pdf_m200 = RooHistPdf("pdf_m200", "pdf_m200", x, dh_m200)
    pdf_m400 = RooHistPdf("pdf_m400", "pdf_m400", RooArgSet(x), dh_m400)

    # Define the morphing variable (mass)
    mass = RooRealVar("mass", "mass", 150, 1000)

    # Create a list of mass points and corresponding PDFs
    # masses = ROOT.RooArgList()
    # masses.add(ROOT.RooRealVar("m150", "m150", 150));
    # masses.add(ROOT.RooRealVar("m400", "m400", 400));

    masses = ROOT.RooArgList(ROOT.RooFit.RooConst(150.0), ROOT.RooFit.RooConst(400.0))

    # pdfs = RooArgList(pdf_m125, pdf_m150, pdf_m200, pdf_m400)
    pdfs = RooArgList(pdf_m150, pdf_m400)

    # Create the moment morphing PDF
    momentMorph = RooMomentMorph("momentMorph", "momentMorph", mass, RooArgList(x), pdfs, masses, RooMomentMorph.NonLinear)

    # Set the desired mass points to interpolate
    
    mass.setVal(m)  # Example mass point to interpolate

    h_interpolated = TH1F("h_interpolated_"+str(m), "mjj GeV", 1000, 100, 1000)  # Adjust bins and range as needed

    # Sample the interpolated PDF and fill the histogram
    for i in range(1, h_interpolated.GetNbinsX() + 1):
        x_value = h_interpolated.GetBinCenter(i)
        x.setVal(x_value)
        bin_content = momentMorph.getVal(RooArgList(x))
        h_interpolated.SetBinContent(i, bin_content)
        # h_interpolated.SetBinError(i, np.sqrt(bin_content)) # Poisson errors
        h_interpolated.SetDirectory(0)
    return h_interpolated

# Run the interpolation function
output_file = TFile("interpolated_mass.root", "RECREATE")
# interpolateMasses = [175, 225, 250, 275, 300, 325, 350, 375]
interpolateMasses = [175, 225, 250, 275, 300, 325, 350, 375]

for m in interpolateMasses:
    
    h = interpolate_mass(m)
    print(h.Integral())
    output_file.cd()

    h.Write()
    
output_file.Close()
