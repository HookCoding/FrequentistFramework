#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse
from InjectGaussian import InjectGaussian
from run_nloFit import run_nloFit
from PrepareTemplates import unifyBinning

def main(args):
    
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--datafile', dest='datafile', type=str, required=True, help='Input data file')
    parser.add_argument('--datahist', dest='datahist', type=str, required=True, help='Input finebinned data histogram name')
    parser.add_argument('--topfile', dest='topfile', type=str, required=True, help='Input top-level xml card')
    parser.add_argument('--categoryfile', dest='categoryfile', type=str, required=True, help='Input category xml card')
    parser.add_argument('--bkgfile', dest='bkgfile', type=str, required=True, help='Input background xml card')
    parser.add_argument('--sigfile', dest='sigfile', type=str, required=True, help='Input signal xml card')
    parser.add_argument('--modelfile', dest='modelfile', type=str, required=True, help='Input RooStats model file with background templates')
    parser.add_argument('--signalmodelfile', dest='signalmodelfile', type=str, required=True, help='Input RooStats model file with signal template')
    parser.add_argument('--wsfile', dest='wsfile', type=str, required=True, help='Output workspace file')
    parser.add_argument('--combinefile', dest='combinefile', type=str, required=True, help='Input xml card for the workspaceCombiner')
    parser.add_argument('--outputfile', dest='outputfile', type=str, required=True, help='Output fitresult file')
    parser.add_argument('--nbkg', dest='nbkg', type=str, required=True, help='Initial value and range of nbkg par (e.g. "2E8,0,3E8")')
    parser.add_argument('--nsig', dest='nsig', type=str, default='0,-1E6,1E6', help='Initial value and range of nsig par (e.g. "0,-1E6,1E6")')
    parser.add_argument('--rangelow', dest='rangelow', type=int, help='Start of fit range (in GeV)')
    parser.add_argument('--rangehigh', dest='rangehigh', type=int, help='End Start of fit range (in GeV)')
    parser.add_argument('--constr', dest='constr', type=int, default=1, help='Constraint term of NPs (in sigma)')
    parser.add_argument('--externalchi2file', dest='externalchi2file', type=str, help='Input file containing TF1 to use for p(chi2) calculation')
    parser.add_argument('--externalchi2fct', dest='externalchi2fct', type=str, help='Name of TF1 to use for p(chi2) calculation')
    parser.add_argument('--externalchi2bins', dest='externalchi2bins', type=int, default=40, help='Number of bins in chi2 function')
    parser.add_argument('--doinitialpars', dest='doinitialpars', action="store_true", help='Initialise with empiric fit parameters != 0')
    parser.add_argument('--dosignal', dest='dosignal', action="store_true", help='Perform s+b fit (default: bkg-only)')
    parser.add_argument('--dolimit', dest='dolimit', action="store_true", help='Perform limit setting')
    parser.add_argument('--sigmean', dest='sigmean', type=int, default=1000, help='Mean of signal Gaussian for s+b fit (in GeV)')
    parser.add_argument('--sigwidth', dest='sigwidth', type=int, default=7, help='Width of signal Gaussian for s+b fit (in %)')
    parser.add_argument('--maskthreshold', dest='maskthreshold', type=float, default=0.01, help='Threshold of p(chi2) below which to run BH and mask the most significant window')
    parser.add_argument('--sigamp', dest='sigamp', type=float, default=0, help='Amplitude of Gaussian to inject (in sigma)')
    parser.add_argument('--loopstart', dest='loopstart', type=int, help='First toy to fit')
    parser.add_argument('--loopend', dest='loopend', type=int, help='Last toy to fit')

    args = parser.parse_args(args)
    signame="mean%s_width%s" % (args.sigmean, args.sigwidth)

    injecteddatafile=args.datafile
    if (args.sigamp > 0):
        print("Injecting signal of amplitude %.1f sigma (FWHM)" % args.sigamp)

        injecteddatafile="run/"+os.path.basename(args.datafile)
        injecteddatafile=injecteddatafile.replace(".root","_injected_mean%d_width%d_amp%.0f.root" % (args.sigmean, args.sigwidth, args.sigamp))

        InjectGaussian(infile=args.datafile, 
                       histname=args.datahist, 
                       sigmean=args.sigmean, 
                       sigwidth=args.sigwidth, 
                       sigamp=args.sigamp,
                       outfile=injecteddatafile,
                       firsttoy=args.loopstart,
                       lasttoy=args.loopend)

    if not injecteddatafile.endswith("_fixedBins.root"):
        print("Copying %s into unit bin widths" % injecteddatafile)

        unifyBinning.main([injecteddatafile])
        injecteddatafile=injecteddatafile.replace(".root","_fixedBins.root")
        
    if args.loopstart!=None and args.loopend!=None:
        for toy in range(args.loopstart, args.loopend+1):
            datahist="%s_%d" % (args.datahist, toy)
            outputfile=args.outputfile.replace(".root", "_%d.root" % toy)
            print("Running run_nloFit with datahist %s" % datahist)
            run_nloFit(datafile=injecteddatafile,
                       datahist=datahist,
                       topfile=args.topfile,
                       categoryfile=args.categoryfile,
                       bkgfile=args.bkgfile,
                       sigfile=args.sigfile,
                       modelfile=args.modelfile,
                       signalmodelfile=args.signalmodelfile,
                       wsfile=args.wsfile,
                       combinefile=args.combinefile,
                       outputfile=outputfile,
                       nbkg=args.nbkg,
                       nsig=args.nsig,
                       rangelow=args.rangelow,
                       rangehigh=args.rangehigh,
                       constr=args.constr,
                       externalchi2file=args.externalchi2file,
                       externalchi2fct=args.externalchi2fct,
                       externalchi2bins=args.externalchi2bins,
                       doinitialpars=args.doinitialpars,
                       dosignal=args.dosignal,
                       dolimit=args.dolimit,
                       signame=signame,
                       maskthreshold=args.maskthreshold)
    else:
        print("Running run_nloFit with datahist %s" % args.datahist)
        run_nloFit(datafile=injecteddatafile,
                   datahist=args.datahist,
                   topfile=args.topfile,
                   categoryfile=args.categoryfile,
                   bkgfile=args.bkgfile,
                   sigfile=args.sigfile,
                   modelfile=args.modelfile,
                   signalmodelfile=args.signalmodelfile,
                   wsfile=args.wsfile,
                   combinefile=args.combinefile,
                   outputfile=args.outputfile,
                   nbkg=args.nbkg,
                   nsig=args.nsig,
                   rangelow=args.rangelow,
                   rangehigh=args.rangehigh,
                   constr=args.constr,
                   externalchi2file=args.externalchi2file,
                   externalchi2fct=args.externalchi2fct,
                   externalchi2bins=args.externalchi2bins,
                   doinitialpars=args.doinitialpars,
                   dosignal=args.dosignal,
                   dolimit=args.dolimit,
                   signame=signame,
                   maskthreshold=args.maskthreshold)


if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
