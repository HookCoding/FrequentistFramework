#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
import hashlib
import platform
from pathlib import Path
from run_execution import execute, execute_required
from run_manifest import write_analysis_results
from run_masking import run_bumphunter, should_mask
from run_provenance import build_analysis_provenance
from run_templates import prepare_run_templates, replaceinfile
from run_fit import build_fit_extract


def run_anaFit(datafile,
               datahist,
               topfile,
               categoryfile,
               wsfile,
               outputfile,
               nbkg,
               nsig,
               rangelow,
               rangehigh,
               signame,
               backgroundfile=None,
               signalfile=None,
               dosignal=False,
               dolimit=False,
               sigmean=1000,
               sigwidth=7.,
               maskthreshold=0.01,
               doprefit=False,
               folder="run/",
               systdict=None,
               covariancedict=None):

    nbins=rangehigh - rangelow
    print("Fitting", nbins, "bins in range", rangelow, "-", rangehigh)

    args_names = locals()
    for key, value in args_names.items():
      print(f"{key}: {value}")

    provenance = build_analysis_provenance(
        datafile=datafile,
        datahist=datahist,
        topfile=topfile,
        categoryfile=categoryfile,
        backgroundfile=backgroundfile,
        signalfile=signalfile,
        rangelow=rangelow,
        rangehigh=rangehigh,
        dosignal=dosignal,
        dolimit=dolimit,
        doprefit=doprefit,
        maskthreshold=maskthreshold,
    )

    # Copies/edits the top/category/signal/background XML templates and,
    # when doprefit is set, seeds initial parameter values via PreFitter.
    # See python/run_templates.py for the extracted logic (Tier 3 Chunk 5).
    tmptopfile, tmpcategoryfile, xml_categoryfile, xml_wsfile = prepare_run_templates(
        folder=folder,
        topfile=topfile,
        categoryfile=categoryfile,
        backgroundfile=backgroundfile,
        signalfile=signalfile,
        signame=signame,
        wsfile=wsfile,
        sigmean=sigmean,
        sigwidth=sigwidth,
        datafile=datafile,
        datahist=datahist,
        rangelow=rangelow,
        rangehigh=rangehigh,
        nbkg=nbkg,
        nsig=nsig,
        doprefit=doprefit,
        systdict=systdict,
    )

    if dosignal:
        poi="nsig_%s" % signame
        if sigwidth == -999:
    	    # poi="nsig_mR{}_gq0p1".format(sigmean)
            poi="nsig_mR{}".format(sigmean)
    else:
        poi=None

    
    print("##################################################################################################    do signal is ", dosignal)
    print("##################################################################################################    poi is  ", poi)

    #shutil.copy2('/afs/cern.ch/work/t/tofitsch/tlafits/tomas/background_dijetTLA_fromTemplate.xml', tmpbackgroundfile) #XXX
    #shutil.copy2('/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/background_dijetTLA_fromTemplate.xml', tmpbackgroundfile) #XXX
    pval_global, postfitfile, parameterfile = build_fit_extract(topfile=tmptopfile,
                                                                datafile=datafile, 
                                                                datahist=datahist, 
                                                                rangelow=rangelow, 
                                                                rangehigh=rangehigh,
                                                                wsfile=wsfile, 
                                                                fitresultfile=outputfile, 
                                                                poi=poi,
							                                )
                                                        

    print ("Global fit p(chi2)=%.3f" % pval_global)

    final_p_chi2 = pval_global
    fit_was_masked = False

    if not should_mask(pval_global, maskthreshold): #or True:
        print("p(chi2) threshold passed. Exiting with succesful fit.")
    else:
        print("p(chi2) threshold not passed.")

        #   if True:
        print("Now running BH for masking.")

        tmpcategoryfilemasked=tmpcategoryfile.replace(".xml","_masked.xml")

        # need to unset pythonpath in order to not use cvmfs numpy
        #execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "J100yStar06_rebinned/postfit", "J100yStar06_rebinned/data", "{}/BHresults.json".format(folder)))
        BHresults = run_bumphunter(postfitfile, folder)


        #blind_min = 135
        #blind_max = 136

        #cmd = [
        #    "sed",
        #    "-i",
        #    "-E",
        #    f's/"MaskMin": [0-9.]+, "MaskMax": [0-9.]+, "BlindRange": "[0-9]+,[0-9]+"/'
        #    f'"MaskMin": {blind_min}, "MaskMax": {blind_max}, "BlindRange": "{blind_min},{blind_max}"/',
        #    "{}/BHresults.json".format(folder)
        #]
        #
        #subprocess.run(cmd, check=True)

        tmptopfilemasked=tmptopfile.replace(".xml","_masked.xml")
        wsfilemasked=wsfile.replace(".root","_masked.root")
        outfilemasked=outputfile.replace(".root","_masked.root")
        xml_categoryfilemasked = os.path.relpath(tmpcategoryfilemasked, os.getcwd())
        xml_wsfilemasked = os.path.relpath(wsfilemasked, os.getcwd())

        shutil.copy2(tmptopfile, tmptopfilemasked) 
        shutil.copy2(tmpcategoryfile, tmpcategoryfilemasked) 

        replaceinfile(tmptopfilemasked, 
                      [(xml_categoryfile,xml_categoryfilemasked),
                       (r'(OutputFile="[A-Za-z0-9_/.-]*")',r'\1 Blind="true"'),
                       (xml_wsfile, xml_wsfilemasked),])
        replaceinfile(tmpcategoryfilemasked, 
                      [(r'(Binning="\d+")', r'\1 BlindRange="%s"' % BHresults["BlindRange"])])

        pval_masked,_,_ = build_fit_extract(tmptopfilemasked,
                                            datafile=datafile, 
                                            datahist=datahist, 
                                            rangelow=rangelow, 
                                            rangehigh=rangehigh,
                                            wsfile=wsfilemasked, 
                                            fitresultfile=outfilemasked, 
                                            poi=poi, 
                                            maskrange=(int(BHresults["MaskMin"]), int(BHresults["MaskMax"]))
                                            )

        print("Masked fit p(chi2)=%.3f" % pval_masked)

        if not should_mask(pval_masked, maskthreshold):
            print("p(chi2) threshold passed. Continuing with successful (window-excluded) fit.")
            wsfile=wsfilemasked
            final_p_chi2 = pval_masked
            fit_was_masked = True
        else:
            print("p(chi2) threshold still not passed.")
            print("Exiting with failed fit status.")
            return -1
    
    print()

    # blindrange not yet implemented with quickLimit
    if dolimit and dosignal and not should_mask(pval_global, maskthreshold):
        print("Now running quickLimit")
        #rtv=execute("timeout --foreground 1800 quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-8 --muScanPoints 20 --minStrat 1 --nllOffset 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")))
        rtv=execute("quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-06 --muScanPoints 20 --minStrat 2 --nllOffset 0 --GKIntegrator 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")))
        if rtv != 0:
            print("ERROR: quickLimit failed with exit code {}".format(rtv))
            return -1
    
    write_analysis_results(
        folder=folder,
        p_chi2=final_p_chi2,
        masked=fit_was_masked,
        provenance=provenance,
    )

    return 0

def main(args):
    
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--datafile', dest='datafile', type=str, required=True, help='Input data file')
    parser.add_argument('--datahist', dest='datahist', type=str, required=True, help='Input finebinned data histogram name')
    parser.add_argument('--topfile', dest='topfile', type=str, required=True, help='Input top-level xml card')
    parser.add_argument('--categoryfile', dest='categoryfile', type=str, required=True, help='Input category xml card')
    parser.add_argument('--backgroundfile', dest='backgroundfile', type=str, help='Input background xml card')
    parser.add_argument('--signalfile', dest='signalfile', default= None, type=str, help='Input signal xml card')
    parser.add_argument('--wsfile', dest='wsfile', type=str, required=True, help='Output workspace file')
    parser.add_argument('--outputfile', dest='outputfile', type=str, required=True, help='Output fitresult file')
    parser.add_argument('--nbkg', dest='nbkg', type=str, required=True, help='Initial value and range of nbkg par (e.g. "2E8,0,3E8")')
    parser.add_argument('--nsig', dest='nsig', type=str, default='0,-1E6,1E6', help='Initial value and range of nsig par (e.g. "0,-1E6,1E6")')
    parser.add_argument('--rangelow', dest='rangelow', type=int, help='Start of fit range (in GeV)')
    parser.add_argument('--rangehigh', dest='rangehigh', type=int, help='End Start of fit range (in GeV)')
    parser.add_argument('--dosignal', dest='dosignal', action="store_true", help='Perform s+b fit (default: bkg-only)')
    parser.add_argument('--dolimit', dest='dolimit', action="store_true", help='Perform limit setting')
    parser.add_argument('--signame', dest='signame', type=str, help='Name of the signal parameter')
    parser.add_argument('--sigmean', dest='sigmean', type=int, default=1000, help='Mean of signal Gaussian for s+b fit (in GeV)')
    parser.add_argument('--sigwidth', dest='sigwidth', type=float, default=7., help='Width of signal Gaussian for s+b fit (in %). If -999 dealing with Zprime samples.')
    parser.add_argument('--maskthreshold', dest='maskthreshold', type=float, default=0.01, help='Threshold of p(chi2) below which to run BH and mask the most significant window')
    parser.add_argument('--doprefit', dest='doprefit', action="store_true", help='Perform ROOT prefit before quickFit')
    parser.add_argument('--folder', dest='folder', type=str, default='run', help='Output folder to store configs and results (default: run)')
    parser.add_argument('--sysfile', dest='sysfile', type=str, help='Path to json file containing signal systematics dict')

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
    print("current working directory", os.getcwd())

    systdict = None
    covariancedict = None
    if args.sysfile:
        with open(args.sysfile) as f:
            systdict = json.load(f)[str(args.sigmean)]
    #if args.covariancefile:
    #    with open(args.covariancefile) as f:
    #        covariancedict = json.load(f)[str(args.sigmean)]

    print(args.nbkg,args.nsig,args.dosignal,args.dolimit,args.sigmean,args.sigwidth,args.signame,args.maskthreshold,args.doprefit)
    return run_anaFit(datafile=args.datafile,
               datahist=args.datahist,
               topfile=args.topfile,
               categoryfile=args.categoryfile,
               backgroundfile=args.backgroundfile,
               signalfile=args.signalfile,
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
               doprefit=args.doprefit,
               systdict=systdict)



if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
