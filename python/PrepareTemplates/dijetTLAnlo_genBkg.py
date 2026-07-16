import ROOT
import sys, re, os, math, argparse

def rchop(s, sub):
    return s[:-len(sub)] if s.endswith(sub) else s

def main(args):
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='', help='Input file name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
    args = parser.parse_args(args)

    suffix_up   = "_1u"
    suffix_down = "_1d"

    meas = ROOT.RooStats.HistFactory.Measurement("meas", "meas")
    meas.SetExportOnly( False )    # True omits plots and tables from output file
    meas.SetOutputFilePrefix( rchop(args.outfile, ".root") )
    # meas.SetPOI( "nsig" )

    meas.SetLumi(1.0);
    # meas.SetLumiRelErr(0);

    if "J75" in args.infile:
        chan = ROOT.RooStats.HistFactory.Channel( "J75yStar03" )
    elif "J100" in args.infile:
        chan = ROOT.RooStats.HistFactory.Channel( "J100yStar06" )
    else:
        return 1

    nominal = ROOT.RooStats.HistFactory.Sample( "nominal", "nominal", args.infile )
    # background.ActivateStatError( "background1_statUncert", InputFile )
    nominal.SetNormalizeByTheory(False) #no lumi unc on this

    inFile = ROOT.TFile(args.infile, "READ")
    for histKey in inFile.GetListOfKeys():
        histName = histKey.GetName()
        
        if "var" in histName:
            if histName.endswith(suffix_down):
                continue
            
            if histName.endswith(suffix_up):
                varMerge = rchop(histName, suffix_up)
                varUp    = histName
                varDown  = rchop(histName, suffix_up) + suffix_down
                
            nominal.AddHistoSys(varMerge, varDown, args.infile, "", varUp, args.infile, "")

    inFile.Close()

    chan.AddSample( nominal )

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

    f_out = ROOT.TFile(args.outfile, "RECREATE")
    ws.Write()
    f_out.Close()
    
if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
