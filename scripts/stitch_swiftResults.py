#!/usr/bin/env python

import ROOT
import array,math
import glob, argparse

#patternMatch = "PostFit_NotRebinned_fivePar_J100yStar_bOnly_ibin*.root"
#resolutionBinsFileName = "/home/mariana/Nube/TLA/FrequentistFramework/Input/data/dijetTLAnlo/data_J100yStar06_range171_3217.root"
#resolutionBinsHistoName = "data"

def computeResiduals(data, fit, histoName="residuals"):
    h = fit.Clone(histoName)
    h.SetDirectory(0)
    h.Reset("M")
    
    for ibin in range(1, fit.GetNbinsX()+1):
        valueErrorData = data.GetBinError(ibin)
        valueData = data.GetBinContent(ibin)
        valueFit = fit.GetBinContent(ibin)

        binSig = 0.
        if valueErrorData > 0. and valueFit > 0.:
            # binSig = (valueData - valueFit)/ valueErrorData
	    binSig = (valueData - valueFit)/ math.sqrt(valueFit)

            h.SetBinContent(ibin, binSig)
            h.SetBinError(ibin, 0)
    
    return h

def StitchSwiftResults( patternMatch, outputFileName, analysisRangeLow = 457, analysisRangeHigh = 2997, resolutionBinsFileName = "Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root", resolutionBinsHistoName = "data"):

  resfile = ROOT.TFile(resolutionBinsFileName, 'read')
  resHisto = resfile.Get(resolutionBinsHistoName)
  
  res_binEdges = [ resHisto.GetBinLowEdge(i) for i in range(1, resHisto.GetNbinsX()+2) ]
  res_binEdges = [ binEdge for binEdge in res_binEdges if binEdge > analysisRangeLow and binEdge< analysisRangeHigh] 
 
  # halving resolution bins:
  # used these ones for swifting
  binEdges = [171.0, 180.0, 188.0, 197.0, 206.0, 215.0, 224.0, 234.0, 243.0, 253.0, 262.0, 272.0, 282.0, 292.0, 302.0, 313.0, 323.0, 334.0, 344.0, 355.0, 365.0, 376.0, 387.0, 399.0, 410.0, 422.0, 433.0, 445.0, 457.0, 469.0, 481.0, 494.0, 506.0, 519.0, 531.0, 544.0, 556.0, 569.0, 582.0, 595.0, 608.0, 622.0, 635.0, 649.0, 662.0, 676.0, 690.0, 705.0, 719.0, 734.0, 748.0, 763.0, 778.0, 793.0, 808.0, 824.0, 839.0, 855.0, 871.0, 887.0, 903.0, 920.0, 936.0, 953.0, 970.0, 987.0, 1004.0, 1022.0, 1039.0, 1057.0, 1075.0, 1093.0, 1111.0, 1130.0, 1148.0, 1167.0, 1186.0, 1206.0, 1225.0, 1245.0, 1264.0, 1284.0, 1304.0, 1325.0, 1345.0, 1366.0, 1387.0, 1408.0, 1429.0, 1451.0, 1472.0, 1494.0, 1516.0, 1539.0, 1561.0, 1584.0, 1607.0, 1631.0, 1654.0, 1678.0, 1701.0, 1725.0, 1749.0, 1774.0, 1798.0, 1823.0, 1848.0, 1874.0, 1899.0, 1925.0, 1951.0, 1978.0, 2004.0, 2031.0, 2058.0, 2086.0, 2113.0, 2141.0, 2169.0, 2198.0, 2226.0, 2255.0, 2284.0, 2314.0, 2343.0, 2373.0, 2403.0, 2434.0, 2464.0, 2495.0, 2526.0, 2558.0, 2590.0, 2623.0, 2655.0, 2688.0, 2721.0, 2755.0, 2788.0, 2822.0, 2856.0, 2891.0, 2926.0, 2962.0, 2997.0, 3033.0, 3069.0, 3106.0, 3142.0, 3180.0, 3217.0]
 
  #binEdges = [ binEdge for binEdge in binEdges if binEdge > analysisRangeLow and binEdge< analysisRangeHigh]
  #print binEdges
  resolutionBins = array.array('d', binEdges)
  resolutionFrame = ROOT.TH1D("resolutionFrame", "", len(resolutionBins)-1, resolutionBins)

  collectFiles = glob.glob(patternMatch)

  #print "Found files:"
  #print collectFiles

  # Build histograms for full spectrum:
  h_data = ROOT.TH1D("data","data", analysisRangeHigh - analysisRangeLow, analysisRangeLow, analysisRangeHigh)
  h_swiftFit = h_data.Clone("swiftFit")
  h_swiftResiduals = h_data.Clone("swiftResiduals")

  for f in collectFiles:
      print "Opening file", f
      postfitFile = ROOT.TFile(f, 'read')
      h_thisData = postfitFile.Get("J100yStar06/data")
      h_fit  = postfitFile.Get("J100yStar06/postfit")
      h_res  = postfitFile.Get("J100yStar06/residuals")

      if h_thisData.GetNbinsX() != h_fit.GetNbinsX():
	print "ERROR: number of bins in data histogram and postfit histogram does not match, stitching won't work"
	sys.exit()
      
      # from this file we extract info only for the i-eth half-res bin:
      i = int(f.split("ibin")[1].split("_")[0])
      low = resolutionFrame.GetXaxis().GetBinLowEdge(i)
      high = resolutionFrame.GetXaxis().GetBinUpEdge(i)
      for j in range(1,h_fit.GetNbinsX()+1):
	if h_fit.GetXaxis().GetBinLowEdge(j)>= low and h_fit.GetXaxis().GetBinUpEdge(j)<= high:
	  print h_fit.GetBinCenter(j)
	  h_data.SetBinContent( h_data.FindBin( h_thisData.GetBinCenter(j)), h_thisData.GetBinContent(j) )
	  h_data.SetBinError( h_data.FindBin( h_thisData.GetBinCenter(j)),  h_thisData.GetBinError(j) ) 
	  h_swiftFit.SetBinContent( h_swiftFit.FindBin( h_fit.GetBinCenter(j)) , h_fit.GetBinContent(j))
	  h_swiftFit.SetBinError(   h_swiftFit.FindBin( h_fit.GetBinCenter(j)) , math.sqrt(h_fit.GetBinContent(j)))
	  h_swiftResiduals.SetBinContent( h_swiftResiduals.FindBin( h_res.GetBinCenter(j) ), h_res.GetBinContent(j))
      
      postfitFile.Close()

  h_swiftFit.SetLineColor(ROOT.kRed)
  h_swiftFit.SetLineWidth(2)
  # We also want to include stuff rebinned in resolution bins:
  firstBin = h_swiftFit.FindFirstBinAbove(0)
  # print "First non-zero bin is", firstBin

  binEdges = [ binEdge for binEdge in binEdges if binEdge > analysisRangeLow and binEdge< analysisRangeHigh]
  rebinBins = [ binEdge for binEdge in binEdges if binEdge >= h_swiftFit.GetBinLowEdge(firstBin) ]
  h_rebinFit = h_swiftFit.Clone()
  h_rebinFit = h_rebinFit.Rebin( len(rebinBins)-1, "swiftFit_rebinned", array.array('d', rebinBins))
  h_rebinFit.SetNameTitle("swiftFit_rebinned","swiftFit_rebinned")
  h_rebinData = h_data.Clone()
  h_rebinData = h_rebinData.Rebin( len(rebinBins)-1, "data_rebinned", array.array('d', rebinBins))
  h_rebinData.SetNameTitle("data_rebinned", "data_rebinned")
  # Recompute residuals in new binning:
  h_rebinResiduals = computeResiduals( h_rebinData, h_rebinFit, "swiftResiduals_rebinned")

  rebinBins = [ binEdge for binEdge in res_binEdges if binEdge >= h_swiftFit.GetBinLowEdge(firstBin) ]
  h_rebinFit_res = h_swiftFit.Clone()
  h_rebinFit_res = h_rebinFit.Rebin( len(rebinBins)-1, "swiftFit_rebinned_resolution", array.array('d', rebinBins))
  h_rebinFit_res.SetNameTitle("swiftFit_rebinned_resolution","swiftFit_rebinned_resolution")
  h_rebinData_res = h_data.Clone()
  h_rebinData_res = h_rebinData.Rebin( len(rebinBins)-1, "data_rebinned_resolution", array.array('d', rebinBins))
  h_rebinData_res.SetNameTitle("data_rebinned_resolution", "data_rebinned_resolution")
  # Recompute residuals in new binning:
  h_rebinResiduals_res = computeResiduals( h_rebinData_res, h_rebinFit_res, "swiftResiduals_rebinned_resolution")

  outputfile = ROOT.TFile(outputFileName,'recreate')
  outputfile.cd()
  h_swiftFit.Write()
  h_data.Write("data")
  h_swiftResiduals.Write()
  h_rebinFit.Write()
  h_rebinData.Write()
  h_rebinResiduals.Write()

  h_rebinFit_res.Write()
  h_rebinData_res.Write()
  h_rebinResiduals_res.Write()

  outputfile.Close()

  return

