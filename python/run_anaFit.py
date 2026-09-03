#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
import hashlib
import platform
from pathlib import Path
from ExtractPostfitFromWS import PostfitExtractor
from ExtractFitParameters import FitParameterExtractor
from PreFit import PreFitter
from run_execution import execute, execute_required
from run_manifest import write_analysis_results
from run_masking import run_bumphunter, should_mask
from run_provenance import build_analysis_provenance
import ROOT


def replaceinfile(f, old_new_list):
    with open(f, 'r') as file :
        filedata = file.read()

    try:
        for tup in old_new_list:
            filedata = re.sub(tup[0], tup[1], filedata)
    except:
        print("ERROR: replaceinfile expects a list of tuples of strings [(old1,new1),...] as input")
        print(old_new_list)
        sys.exit(-1)

    with open(f, 'w') as file:
        file.write(filedata)

def build_fit_extract(topfile, datafile, datahist, rangelow, rangehigh, wsfile, fitresultfile, poi=None, maskrange=None):
    xmlreader_command = (
        'xmlAnaWSBuilder/build/bin/XMLReader -x %s '
        '-o "logy integral" --minimizerStrategy 0'
    ) % topfile
    if not execute_required(
        xmlreader_command,
        "XMLReader workspace generation",
        expected_outputs=[wsfile],
    ):
        raise RuntimeError("XMLReader workspace generation failed")
    if poi:
        print("Now running s+b quickFit")
        _poi="-p %s" % poi
        #bkgonly_opt = False
    else:
        print("Now running bkg-only quickFit")
        _poi=""
        #bkgonly_opt = True

    if maskrange:
        _range="--range SBLo_Run3TLA,SBHi_Run3TLA"
        maskmin=maskrange[0]
        maskmax=maskrange[1]
        print(">>>>>>>>>>>>>>>>>>>>>>>>>> BH mask range: "+str(maskmin)+","+str(maskmax))
    else:
        _range=""
        maskmin=-1
        maskmax=-1
        print(">>>>>>>>>>>>>>>>>>>>>>>>>> no BH mask range: setting to -1 both maskmin and maskmax!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    logfile=fitresultfile.replace("FitResult","quickFitLog").replace(".root", ".log")
    edmplot=fitresultfile.replace("FitResult","edm").replace(".root", ".pdf")

    #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! _poi is :"+str(_poi))
    quickfit_command = "quickFit/build/quickFit --chi2fit 1 --poissonerror 1 -f %s -d combData %s --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-6 %s -o %s > %s 2>&1" % (
        wsfile,
        _poi,
        _range,
        fitresultfile,
        logfile,
    )
    if not execute_required(
        quickfit_command,
        "quickFit background or signal fit",
        expected_outputs=[fitresultfile, logfile],
    ):
        raise RuntimeError("quickFit failed")

    execute("python plot_edm.py %s %s" % (logfile, edmplot))

    postfitfile=fitresultfile.replace("FitResult","PostFit")
    parameterfile=fitresultfile.replace("FitResult","FitParameters")

    f=ROOT.TFile(datafile)
    d=f.Get(datahist)
    datafirstbin=d.FindBin(rangelow)-1
    f.Close()
    
    # Define resolution binning for BH
    #binningFileName = f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"
    binningFileName = f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"

    print(binningFileName)
    if not os.path.exists(binningFileName):
        execute(f"python3 python/createBinning.py -s {rangelow} -e {rangehigh} -o {binningFileName}")

    print("EXECUTE: pfe = PostfitExtractor(")
    print("datafile=", datafile)
    print("datahist=", datahist)
    print("datafirstbin=", datafirstbin)
    print("wsfile=", fitresultfile)
        #rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
    print("rebinfile=", f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root")
    print("rebinhist=", "mjjBinning")
    print("maskmin=", maskmin)
    print("bkgonly=", True)
    print(")")

    pfe = PostfitExtractor(
        datafile=datafile,
        datahist=datahist,
        datafirstbin=datafirstbin,
        wsfile=fitresultfile,
        #rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
        rebinfile=f"Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
        rebinhist="mjjBinning",
        maskmin=maskmin,
        maskmax=maskmax,
        #bkgonly=bkgonly_opt
        bkgonly=True
    )
    # If we used masking in a b-only fit then we need to calculate the p-val from the correctly normalized postfit distribution
    if maskmin > -1 or maskmax > -1:
        pval = pfe.GetPval("Run3TLA_bkgonly_rebinned") #should be Run3TLA or Run3TLA_rebinned?
    else:
        pval = pfe.GetPval("Run3TLA_rebinned") #should be Run3TLA or Run3TLA_rebinned?
    
    print("pfe.WriteRoot(", postfitfile, ", dirPerCategory=True)")
    pfe.WriteRoot(postfitfile, dirPerCategory=True)
    #pfe.WriteRoot(postfitfile) # this looks problematic

    fpe = FitParameterExtractor(wsfile=fitresultfile)
    fpe.WriteRoot(parameterfile)

    return (pval, postfitfile, parameterfile)

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

    # generate the config files on the fly in run dir
    if not os.path.isfile("{}/AnaWSBuilder.dtd".format(folder)):
      #execute("ln -sf $PWD/config/dijetTLA/AnaWSBuilder.dtd $PWD/{}/AnaWSBuilder.dtd".format(folder))
      #execute("ln -sf ~/WORK/tla/FrequentistFramework/config/dijetisrTLA/AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder))
      execute("ln -sf `realpath config/dijetisrTLA/AnaWSBuilder.dtd` {}/AnaWSBuilder.dtd".format(folder))
      print("this is happening")
    if sigwidth == -999: # running on zprime samples:
      print("Running in Zprime samples")
      tmpcategoryfile="{0}/category_dijetTLA_fromTemplate_mR{1}.xml".format(folder, sigmean)
      tmptopfile="{0}/dijetTLA_fromTemplate_mR{1}.xml".format(folder, sigmean)
    else:
      tmpcategoryfile="{}/category_dijetTLA_fromTemplate.xml".format(folder)
      tmptopfile="{}/dijetTLA_fromTemplate.xml".format(folder)  
    tmpsignalfile="{}/signal_dijetTLA_fromTemplate.xml".format(folder)
    tmpbackgroundfile="{}/background_dijetTLA_fromTemplate.xml".format(folder)

    # XMLReader resolves relative paths from the current working directory.
    # Keep full paths for Python file operations, but write portable paths
    # relative to the repository working directory into generated XML files.
    xml_categoryfile = os.path.relpath(tmpcategoryfile, os.getcwd())
    xml_signalfile = os.path.relpath(tmpsignalfile, os.getcwd())
    xml_backgroundfile = os.path.relpath(tmpbackgroundfile, os.getcwd())
    xml_wsfile = os.path.relpath(wsfile, os.getcwd())
    
    print("--------------------------------------> tmpcategoryfile: "+tmpcategoryfile)
    print("--------------------------------------> tmptopfile: "+tmptopfile)

    shutil.copy2(topfile, tmptopfile) 
    shutil.copy2(categoryfile, tmpcategoryfile) 
    if signalfile:
        shutil.copy2(signalfile, tmpsignalfile) 
    
    replaceinfile(tmptopfile, 
                  [("CATEGORYFILE", xml_categoryfile),
                   ("OUTPUTFILE", xml_wsfile),
                   ("SIGNAME", signame),
               ])

    if backgroundfile:
        shutil.copy2(backgroundfile, tmpbackgroundfile) 
        replaceinfile(tmpcategoryfile, 
                      [("BACKGROUNDFILE", xml_backgroundfile)])
        
        if doprefit:
            nPars = 5

            if "three" in  backgroundfile:
                nPars = 3
            if "four" in  backgroundfile:
                nPars = 4
            elif "five" in  backgroundfile:
                nPars = 5
            elif "six" in  backgroundfile:
                nPars = 6
            elif "seven" in  backgroundfile:
                nPars = 7
            elif "eight" in  backgroundfile:
                nPars = 8
            elif "nine" in  backgroundfile:
                nPars = 9
            elif "ten" in  backgroundfile:
                nPars = 10
            # [1, -30, -30, -30, ...]
            parRangeLow = [1]+[-30]*(nPars-1)
            parRangeHigh = [1]+[30]*(nPars-1)
            
            # get prefit ranges from background file
            with open(tmpbackgroundfile) as f:
                lines = f.readlines()
                for line in lines:
                    if not "<!--" in line and "<ModelItem" in line:
                        matches = re.findall('\[PAR(\d+),[ ]*([+-]?[0-9]+(?:[.][0-9]*)?),[ ]*([+-]?[0-9]+(?:[.][0-9]*)?)[ ]*\]', line)
                        for m in matches:
                            #m[0] is parN
                            #m[1] is rangeLow
                            #m[2] is rangeHigh
                            parRangeLow[int(m[0])-1] = float(m[1])
                            parRangeHigh[int(m[0])-1] = float(m[2])

            print("Starting PreFit in parameter ranges:")
            print(parRangeLow)
            print(parRangeHigh)
                            
            pf = PreFitter(
                datafile = datafile,
                datahist = datahist,
                xMin = rangelow,
                xMax = rangehigh,
                nPars = nPars,
                nRetries1 = 2000*nPars,
                nRetries2 = 2*nPars,
                fitLog = True,
                parRangeLow = parRangeLow,
                parRangeHigh = parRangeHigh,
            )
            
            initPars,_nbkg = pf.Fit()
            print(_nbkg)
            nbkg="%.1E, 0, %.1E" % (_nbkg, 2*_nbkg)
            print(_nbkg)
            
            print("Starting fit with initial pars", initPars)

            for i in range(nPars):
                replaceinfile(tmpbackgroundfile, 
                              [("PAR%d" % (i+1), str(initPars[i]))
                           ])

    replaceinfile(tmpcategoryfile, [
        ("DATAFILE", datafile),
        ("DATAHIST", datahist),
        ("RANGELOW", str(rangelow)),
        ("RANGEHIGH", str(rangehigh)),
        ("BINS", str(nbins)),
        ("NBKG", nbkg),
	("NSIG", nsig),
	("SIGNAME", signame),
	("SIGNALFILE", xml_signalfile)
    ])    

    if signalfile:
        #replaceinfile(tmpsignalfile, 
        #              [("SIGMEAN", str(sigmean)),
        #               ("SIGWIDTH", str(sigwidth)),
        #]) 
        replacements = [("SIGNAME", str(signame)),   
                        ("SIGMEAN", str(sigmean)),   
                        ("SIGWIDTH", str(sigwidth)), 
            ]                                
              
        if systdict != None:
            print("replacing in signalfile now")
            replacements.append(("NOMINAL_MEAN", str(systdict["nominal_mean"])))
            replacements.append(("NOMINAL_WIDTH", str(systdict["nominal_sigma"])))
            replacements.append(("NOMINAL_ALPHAL", str(systdict["nominal_alpha_l"])))
            replacements.append(("NOMINAL_ALPHAH", str(systdict["nominal_alpha_h"])))
            replacements.append(("NOMINAL_NL", str(systdict["nominal_n_l"])))
            replacements.append(("NOMINAL_NH", str(systdict["nominal_n_h"])))
            for source in systdict["unc_mean_sources"]:
                val = systdict["unc_mean_sources"][source]
                replacements.append(("\[MAG_SCALE_"+str(source)+"\]", "["+str(val)+"]"))
            for source in systdict["unc_sigma_sources"]:
                val = systdict["unc_sigma_sources"][source]
                replacements.append(("\[MAG_RESOLUTION_"+str(source)+"\]", "["+str(val)+"]"))

        #  if covariancedict != None:
        #      print("replacing in signalfile now")
        #      replacements.append(("NOMINAL_MEAN", str(covariancedict["nominal_mean"])))
        #      replacements.append(("NOMINAL_WIDTH", str(covariancedict["nominal_sigma"])))
        #      replacements.append(("NOMINAL_ALPHAL", str(covariancedict["nominal_alpha_l"])))
        #      replacements.append(("NOMINAL_ALPHAH", str(covariancedict["nominal_alpha_h"])))
        #      replacements.append(("NOMINAL_NL", str(covariancedict["nominal_n_l"])))
        #      replacements.append(("NOMINAL_NH", str(covariancedict["nominal_n_h"])))
        #      replacements.append(("MAG_SCALE", str(covariancedict["covariance_cholesky"][4][4])))
        #      replacements.append(("MAG_RESOLUTION", str(covariancedict["covariance_cholesky"][5][5])))
        #      replacements.append(("MAG_CROSSTERM", str(covariancedict["covariance_cholesky"][5][4])))
                
        #set any unreplaced uncertainties to 0 (starting with MAG_ and then any letters, numbers or _ -):
        replacements.append(("\[MAG_[a-zA-Z0-9_\-]*\]", "[0]"))
        replaceinfile(tmpsignalfile, replacements)

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
