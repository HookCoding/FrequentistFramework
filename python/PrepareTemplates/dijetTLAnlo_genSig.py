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
    
    signal = ROOT.RooStats.HistFactory.Sample( "signal", "signal", args.infile) #roostats name, histname, filename
    # signal.AddNormFactor( "nsig", 0, 0, 1e6 )
    signal.SetNormalizeByTheory(False) #no lumi unc on this
    chan.AddSample( signal )

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
