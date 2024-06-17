#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse
from InjectGaussian import InjectGaussian
from run_anaFit import run_anaFit

def main(args):
    
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--datafile', dest='datafile', type=str, required=True, help='Input data file')
    parser.add_argument('--datahist', dest='datahist', type=str, required=True, help='Input finebinned data histogram name')
    parser.add_argument('--topfile', dest='topfile', type=str, required=True, help='Input top-level xml card')
    parser.add_argument('--backgroundfile', dest='backgroundfile', type=str, help='Input background xml card')
    parser.add_argument('--signalfile', dest='signalfile', type=str, help='Input signal xml card')
    parser.add_argument('--categoryfile', dest='categoryfile', type=str, required=True, help='Input category xml card')
    parser.add_argument('--wsfile', dest='wsfile', type=str, required=True, help='Output workspace file')
    parser.add_argument('--outputfile', dest='outputfile', type=str, required=True, help='Output fitresult file')
    parser.add_argument('--nbkg', dest='nbkg', type=str, required=True, help='Initial value and range of nbkg par (e.g. "2E8,0,3E8")')
    parser.add_argument('--nsig', dest='nsig', type=str, default='0,-1E6,1E6', help='Initial value and range of nsig par (e.g. "0,-1E6,1E6")')
    parser.add_argument('--rangelow', dest='rangelow', type=int, required=True, help='Start of fit range (in GeV)')
    parser.add_argument('--rangehigh', dest='rangehigh', type=int, required=True, help='End Start of fit range (in GeV)')
    parser.add_argument('--dosignal', dest='dosignal', action="store_true", help='Perform s+b fit (default: bkg-only)')
    parser.add_argument('--dolimit', dest='dolimit', action="store_true", help='Perform limit setting')
    parser.add_argument('--sigmean', dest='sigmean', type=int, default=1000, help='Mean of signal Gaussian for s+b fit (in GeV)')
    parser.add_argument('--sigwidth', dest='sigwidth', type=int, default=7, help='Width of signal Gaussian for s+b fit (in %)')
    parser.add_argument('--signame', dest='signame', type=str, help='Name of the signal parameter')
    parser.add_argument('--maskthreshold', dest='maskthreshold', type=float, default=0.01, help='Threshold of p(chi2) below which to run BH and mask the most significant window')
    parser.add_argument('--doprefit', dest='doprefit', action="store_true", help='Perform ROOT prefit before quickFit')
    parser.add_argument('--folder', dest='folder', type=str, default='run', help='Output folder to store configs and results (default: run)')
    parser.add_argument('--sigamp', dest='sigamp', type=float, default=0, help='Amplitude of Gaussian to inject (in sigma)')
    parser.add_argument('--loopstart', dest='loopstart', type=int, help='First toy to fit')
    parser.add_argument('--loopend', dest='loopend', type=int, help='Last toy to fit')

    args = parser.parse_args(args)
    if not args.signame:
      if args.sigwidth == -999:
	args.signame="mR%s" % (args.sigmean)
      else:
        args.signame="mean%s_width%s" % (args.sigmean, args.sigwidth)

    # create dir if not exists: https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    try: 
        os.makedirs(args.folder)
    except OSError:
        if not os.path.isdir(args.folder):
            raise

    injecteddatafile=args.datafile
    if (args.sigamp > 0):
        print("Injecting signal of amplitude %.1f sigma (FWHM)" % args.sigamp)

        injecteddatafile=os.path.join(args.folder, os.path.basename(args.datafile))
        injecteddatafile=injecteddatafile.replace(".root","_injected_mean%d_width%d_amp%.0f.root" % (args.sigmean, args.sigwidth, args.sigamp))

        InjectGaussian(infile=args.datafile, 
                       histname=args.datahist, 
                       sigmean=args.sigmean, 
                       sigwidth=args.sigwidth, 
                       sigamp=args.sigamp,
                       outfile=injecteddatafile,
                       firsttoy=args.loopstart,
                       lasttoy=args.loopend)
        
    if args.loopstart!=None and args.loopend!=None:
        for toy in range(args.loopstart, args.loopend+1):
            datahist="%s_%d" % (args.datahist, toy)
            outputfile=args.outputfile.replace(".root", "_%d.root" % toy)
            print("\n\nRunning run_anaFit with datahist %s" % datahist)
            run_anaFit(datafile=injecteddatafile,
                       datahist=datahist,
                       topfile=args.topfile,
                       backgroundfile=args.backgroundfile,
                       signalfile=args.signalfile,
                       categoryfile=args.categoryfile,
                       wsfile=args.wsfile,
                       outputfile=outputfile,
                       nbkg=args.nbkg,
                       nsig=args.nsig,
                       rangelow=args.rangelow,
                       rangehigh=args.rangehigh,
                       dosignal=args.dosignal,
                       dolimit=args.dolimit,
                       sigmean=args.sigmean,
                       sigwidth=args.sigwidth,
                       folder=args.folder,
                       signame=args.signame,
                       maskthreshold=args.maskthreshold,
                       doprefit=args.doprefit)
    else:
        print("Running run_anaFit with datahist %s" % args.datahist)
        run_anaFit(datafile=injecteddatafile,
                   datahist=args.datahist,
                   topfile=args.topfile,
                   backgroundfile=args.backgroundfile,
                   signalfile=args.signalfile,
                   categoryfile=args.categoryfile,
                   wsfile=args.wsfile,
                   outputfile=args.outputfile,
                   nbkg=args.nbkg,
                   nsig=args.nsig,
                   rangelow=args.rangelow,
                   rangehigh=args.rangehigh,
                   dosignal=args.dosignal,
                   dolimit=args.dolimit,
                   sigmean=args.sigmean,
                   sigwidth=args.sigwidth,
                   folder=args.folder,
                   signame=args.signame,
                   maskthreshold=args.maskthreshold,
                   doprefit=args.doprefit)

if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
