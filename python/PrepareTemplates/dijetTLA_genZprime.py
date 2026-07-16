import ROOT
import sys, re, os, math, argparse

def generateSignalWS():
  ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

  suffix_up   = "__1up"

  meas = ROOT.RooStats.HistFactory.Measurement("meas", "meas")
  meas.SetExportOnly( False )    # True omits plots and tables from output file
 
  if args.outfile =='':
    fileName = args.infile.split("/")[-1].replace(".root","_mR{0}_histFactoryWS.root").format(args.mass)
  else:
    fileName = args.outfile

  meas.SetOutputFilePrefix( fileName.replace(".root","") )
  # meas.SetPOI( "nsig" )

  meas.SetLumi(1.0)
  # meas.SetLumiRelErr(0)

  if "J75" in args.infile:
    chan = ROOT.RooStats.HistFactory.Channel( "J75yStar03" )
  elif "J100" in args.infile:
    chan = ROOT.RooStats.HistFactory.Channel( "J100yStar06" )
  else:
    return 1

  # Retrieve names from rootfile:
  # print "Opening:", args.infile
  inFile = ROOT.TFile(args.infile, "READ")

  # relevant systNames, pick up 1up only so we don't double count
  relevantNames = [ histKey.GetName() for histKey in inFile.GetListOfKeys() if ( ("rebinned" not in histKey.GetName()) and ("mR"+args.mass +"_" in histKey.GetName()) and (suffix_up in histKey.GetName())) ]

  # print relevantNames

  nominalNames = [ histKey.GetName() for histKey in inFile.GetListOfKeys() if ( ("rebinned" not in histKey.GetName()) and ("mR"+args.mass + "_" in histKey.GetName()) and ("nominal" in histKey.GetName())) ]
  
  # print nominalNames
  
  # for some mass points there are morphed and original templates: pick up original ones.
  if len(nominalNames) > 1:
    nominalNames = [ h for h in nominalNames if "mjj" in h]
  nominalName = nominalNames[0]
 
  # nominal = ROOT.RooStats.HistFactory.Sample( "nominal", "nominal", args.infile )
  # TODO: test including stat uncertainties!
  # background.ActivateStatError( "background1_statUncert", InputFile )
  signal = ROOT.RooStats.HistFactory.Sample("signal", nominalName, args.infile)
  signal.SetNormalizeByTheory(False) #no lumi unc on this
 
  # Add systematics
  for name in relevantNames:
    histName = name
    # print "histName:", histName
    if "nominal" in histName:
      continue
    else:
      # first let's clean the name
      systName = (histName.split("_JET")[1]).split(suffix_up)[0]
      systName = "JET"+systName

      # Both morphed and original are available for some mass points:
      # if original is available for this mass point, don't pick up mrphed:
      if "morph" in histName:
        if [ h for h in relevantNames if systName in h and "mjj" in h ]:
	  continue
      systUp = histName
      systDown = histName.replace("1up","1down")

      signal.AddHistoSys(systName, systDown, args.infile, "", systUp, args.infile, "")
      # add just one systematic:
      #break

  chan.AddSample( signal )

  # Done with this channel
  # Add it to the measurement:

  meas.AddChannel( chan )

  # Collect the histograms from their files,
  # print some output, 
  meas.CollectHistograms()
  meas.PrintTree();

  # Now, do the measurement
  hist2workspace = ROOT.RooStats.HistFactory.HistoToWorkspaceFactoryFast( meas )
  ws = hist2workspace.MakeCombinedModel( meas )

  ws.Print("all")

  print "Saving in fileName:", fileName
  f_out = ROOT.TFile(fileName, "RECREATE")
  f_out.cd()
  ws.Write()
  f_out.Close()
  inFile.Close()

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="%prog [options]", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
  parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
  parser.add_argument('--mass', dest='mass', type=str, default='', help='mass point')
  args = parser.parse_args()
  
  generateSignalWS()
