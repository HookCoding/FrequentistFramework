#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
from ExtractPostfitFromWS import PostfitExtractor
from ExtractFitParameters import FitParameterExtractor
from PreFit import PreFitter
import ROOT

def execute(cmd):
    print("EXECUTE:", cmd)
    sys.stdout.flush() # keeps print and subprocess output in sync
    rtv = subprocess.call(cmd, shell=True)
    return rtv

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

def build_fit_extract(topfile, datafile, datahist, rangelow, wsfile, fitresultfile, categoryname, poi=None, maskrange=None, dochi2fit=False, dochi2constraints=False, useSumW2=False):
    rtv=execute('XMLReader -x %s -o "logy integral" --minimizerStrategy 0' % topfile) # minimizer strategy fast
    if rtv != 0:
        print("WARNING: Non-zero return code from XMLReader. Check if tolerable")

    if poi:
        print("Now running s+b quickFit")
        _poi="-p %s" % poi
    else:
        print("Now running bkg-only quickFit")
        _poi=""

    if maskrange:
        # _range="--range SBLo,SBHi"
        _range="--range SBLo_{},SBHi_{}".format(categoryname, categoryname)
        maskmin=maskrange[0]
        maskmax=maskrange[1]
    else:
        _range=""
        maskmin=-1
        maskmax=-1

    if dochi2fit:
        chi2flag = "--chi2fit 1"
    else:
        chi2flag = "--chi2fit 0"
    if dochi2constraints:
        chi2flag += " --chi2constraints 1"
    else:
        chi2flag += " --chi2constraints 0"
    if useSumW2:
        chi2flag += " --poissonerror 0"

    rtv=execute("quickFit -f %s -d combData %s --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-10 %s %s -o %s" % (wsfile.replace("root://eosatlas.cern.ch/",""), _poi, _range, chi2flag, fitresultfile))
    if rtv != 0:
        print("WARNING: Non-zero return code from quickFit. Check if tolerable")

    postfitfile=fitresultfile.replace("FitResult","PostFit")
    parameterfile=fitresultfile.replace("FitResult","FitParameters")

    f=ROOT.TFile(datafile)
    d=f.Get(datahist)
    datafirstbin=d.FindBin(rangelow)-1
    f.Close()

    pfe = PostfitExtractor(
        datafile=datafile,
        datahist=datahist,
        datafirstbin=datafirstbin,
        wsfile=fitresultfile,
        rebinfile="Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root",
        rebinhist="data",
        maskmin=maskmin,
        maskmax=maskmax,
        bkgonly=True,
        undolog=False,
        useSumW2=useSumW2
    )
    pval = pfe.GetPval("J100yStar06_rebinned")
    pfe.WriteRoot(postfitfile, dirPerCategory=True)
    # pfe.WriteRoot(postfitfile)

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
               doBH=False,
               sigmean=1000,
               sigwidth=7,
               maskthreshold=0.01,
               doprefit=False,
               dochi2fit=False,
               dochi2constraints=False,
               useSumW2=False,
               folder="run/",
               spursig=0,
               theounc=0,
               systdict=None,
               covariancedict=None,
               categoryname="J100yStar06"):

    nbins=rangehigh - rangelow

    print("Fitting", nbins, "bins in range", rangelow, "-", rangehigh)

    # generate the config files on the fly in run dir
    if not os.path.isfile("{}/AnaWSBuilder.dtd".format(folder)):
        execute("ln -sf $PWD/config/dijetTLA/AnaWSBuilder.dtd {}AnaWSBuilder.dtd".format(folder))
    
    suffix = "_bkgonly"
    if dosignal:
        suffix = "_mean{0}_width{1}".format(sigmean, sigwidth)

    tmpbackgroundfile=os.path.join(folder, os.path.basename(backgroundfile).replace(".template",".xml"))
    tmpsignalfile=os.path.join(folder, os.path.basename(signalfile).replace(".template", suffix + ".xml"))
    tmpcategoryfile=os.path.join(folder, os.path.basename(categoryfile).replace(".template", suffix + ".xml"))
    tmptopfile=tmpcategoryfile.replace("category_","")
    if dosignal and sigwidth == -999: # running on zprime samples:
        print("Running in Zprime samples")
        tmpcategoryfile=tmpcategoryfile.split("_mean")[0]+"_mR{}.xml".format(sigmean)
        tmptopfile=tmptopfile.split("_mean")[0]+"_mR{}.xml".format(sigmean)
    
    print("Generated following cards:\n")
    print("\tTop card:", tmptopfile)
    print("\tCategory card:", tmpcategoryfile)
    print("\tBackground card:", tmpbackgroundfile)
    print("\tSignal card:", tmpsignalfile)

    shutil.copy2(topfile, tmptopfile) 
    shutil.copy2(categoryfile, tmpcategoryfile) 
    if signalfile:
        shutil.copy2(signalfile, tmpsignalfile)

    replaceinfile(tmptopfile,
                  [("CATEGORYFILE", tmpcategoryfile),
                   ("OUTPUTFILE", wsfile),
                   ("SIGNAME", signame),
               ])

    if backgroundfile:
        shutil.copy2(backgroundfile, tmpbackgroundfile)
        replaceinfile(tmpcategoryfile, 
                      [("BACKGROUNDFILE", tmpbackgroundfile)])

        if doprefit:
            nPars = 5
            if "four" in backgroundfile:
                nPars = 4
            elif "five" in backgroundfile:
                nPars = 5
            elif "six" in backgroundfile:
                nPars = 6
            elif "seven" in backgroundfile:
                nPars = 7
            elif "eight" in backgroundfile:
                nPars = 8
            elif "nine" in backgroundfile:
                nPars = 9
            else:
                searchstring =r'(\d+)Par'
                res=re.search(searchstring, backgroundfile)
                nPars=int(res.group(1))

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
            nbkg="%.3E, %1.E, %.1E" % (_nbkg, 0.1*_nbkg, 1.2*_nbkg)

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
        ("SIGNALFILE", tmpsignalfile),
        ("SPURSIG", str(spursig)),
        ("THEOUNC", str(theounc)),
    ])


    if signalfile:
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

        if covariancedict != None:
            print("replacing in signalfile now")
            replacements.append(("NOMINAL_MEAN", str(covariancedict["nominal_mean"])))
            replacements.append(("NOMINAL_WIDTH", str(covariancedict["nominal_sigma"])))
            replacements.append(("NOMINAL_ALPHAL", str(covariancedict["nominal_alpha_l"])))
            replacements.append(("NOMINAL_ALPHAH", str(covariancedict["nominal_alpha_h"])))
            replacements.append(("NOMINAL_NL", str(covariancedict["nominal_n_l"])))
            replacements.append(("NOMINAL_NH", str(covariancedict["nominal_n_h"])))
            replacements.append(("MAG_SCALE", str(covariancedict["covariance_cholesky"][4][4])))
            replacements.append(("MAG_RESOLUTION", str(covariancedict["covariance_cholesky"][5][5])))
            replacements.append(("MAG_CROSSTERM", str(covariancedict["covariance_cholesky"][5][4])))
                
        #set any unreplaced uncertainties to 0 (starting with MAG_ and then any letters, numbers or _ -):
        replacements.append(("\[MAG_[a-zA-Z0-9_\-]*\]", "[0]"))
        replaceinfile(tmpsignalfile, replacements)


    if dosignal:
        poi="nsig_%s" % signame
        if sigwidth == -999:
            poi="nsig_mR{}_gq0p1".format(sigmean)
    else:
        poi="ATLAS_spurious_%s=0_0_0" % signame
        if sigwidth == -999:
            poi="ATLAS_spurious_mR{}_gq0p1=0_0_0".format(sigmean)
        # poi=None

    pval_global, postfitfile, parameterfile = build_fit_extract(topfile=tmptopfile,
                                                                datafile=datafile,
                                                                datahist=datahist,
                                                                rangelow=rangelow,
                                                                wsfile=wsfile,
                                                                fitresultfile=outputfile,
                                                                categoryname=categoryname,
                                                                poi=poi,
                                                                dochi2fit=dochi2fit,
                                                                dochi2constraints=dochi2constraints,
                                                                useSumW2=useSumW2)

    print ("Global fit p(chi2)=%.3f" % pval_global)

    if pval_global > maskthreshold:
        print("p(chi2) threshold passed. Exiting with succesful fit.")
        _range=""
    else:
        print("p(chi2) threshold not passed.")
        print("Now running BH for masking.")

        tmpcategoryfilemasked=tmpcategoryfile.replace(".xml","_masked.xml")

        # need to unset pythonpath in order to not use cvmfs numpy
        execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "{}_rebinned/postfit".format(categoryname), "{}_rebinned/data".format(categoryname), "{}/BHresults.json".format(folder)))

        # pass results of pyBH via this json file
        with open("{}/BHresults.json".format(folder)) as f:
            BHresults=json.load(f)

        tmptopfilemasked=tmptopfile.replace(".xml","_masked.xml")
        wsfilemasked=wsfile.replace(".root","_masked.root")
        outfilemasked=outputfile.replace(".root","_masked.root")

        shutil.copy2(tmptopfile, tmptopfilemasked)
        shutil.copy2(tmpcategoryfile, tmpcategoryfilemasked)

        replaceinfile(tmptopfilemasked,
                      [(tmpcategoryfile,tmpcategoryfilemasked),
                       (r'(OutputFile="[A-Za-z0-9_/.-]*")',r'\1 Blind="true"'),
                       (wsfile, wsfilemasked),])
        replaceinfile(tmpcategoryfilemasked,
                      [(r'(Binning="\d+")', r'\1 BlindRange="%s"' % BHresults["BlindRange"])])

        pval_masked, postfitfile, parameterfile = build_fit_extract(tmptopfilemasked,
                                                                    datafile=datafile,
                                                                    datahist=datahist,
                                                                    rangelow=rangelow,
                                                                    wsfile=wsfilemasked,
                                                                    fitresultfile=outfilemasked,
                                                                    categoryname=categoryname,
                                                                    poi=poi,
                                                                    maskrange=(int(BHresults["MaskMin"]), int(BHresults["MaskMax"])),
                                                                    dochi2fit=dochi2fit,
                                                                    dochi2constraints=dochi2constraints,
                                                                    useSumW2=useSumW2)

        print("Masked fit p(chi2)=%.3f" % pval_masked)

        if pval_masked > maskthreshold:
            print("p(chi2) threshold passed. Continuing with successful (window-excluded) fit.")
        else:
            print("p(chi2) threshold still not passed.")
            # print("Exiting with failed fit status.")
            # return -1

        wsfile=wsfilemasked
        outputfile=outfilemasked

        _range="--range SBLo_{},SBHi_{}".format(categoryname, categoryname)

    if dochi2fit:
        chi2flag = "--chi2fit 1"
    else:
        chi2flag = "--chi2fit 0"
    if dochi2constraints:
        chi2flag += " --chi2constraints 1"
    else:
        chi2flag += " --chi2constraints 0"

    # # blindrange not yet implemented with quickLimit
    # if dolimit and dosignal and pval_global > maskthreshold:
    if dolimit and dosignal:
        print("Now running quickLimit")
        rtv=execute("quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-10 --muScanPoints 20 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 %s %s -o %s" % (wsfile, poi, _range, chi2flag, outputfile.replace("FitResult","Limits")))
        if rtv != 0:
            print("WARNING: Non-zero return code from quickLimit. Check if tolerable")

    if doBH:
        BHfile = outputfile.replace("FitResult","BHResult").replace(".root", ".json")

        # need to unset pythonpath in order to not use cvmfs numpy
        execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "{}_rebinned/postfit".format(categoryname), "{}_rebinned/data".format(categoryname), BHfile))

        # reduce file size by removing info of pseudoexperiments
        # "min_Pval_arr" contains min local p-value of data [0] and N pseudoexperiments [1:]
        # "res_arr" contains local p-value of data: 
        #   [0][:] -> smallest window, all positions
        #   [1][:] -> next bigger window, all positions
        #   ...

        keys_to_remove = ["min_Pval_ar", "min_width_ar", "min_loc_ar", "res_ar", "t_ar"]

        with open(BHfile) as f:
            BHresults=json.load(f)

        for key in keys_to_remove:
            BHresults["pyBHresult"][key] = BHresults["pyBHresult"][key][:1]

        with open(BHfile, "w") as f:
            json.dump(BHresults, f, indent=2)

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
    parser.add_argument('--doBH', dest='doBH', action="store_true", help='Run BumpHunter')
    parser.add_argument('--signame', dest='signame', type=str, help='Name of the signal parameter')
    parser.add_argument('--sigmean', dest='sigmean', type=int, default=1000, help='Mean of signal Gaussian for s+b fit (in GeV)')
    parser.add_argument('--sigwidth', dest='sigwidth', type=int, default=7, help='Width of signal Gaussian for s+b fit (in %). If -999 dealing with Zprime samples.')
    parser.add_argument('--maskthreshold', dest='maskthreshold', type=float, default=0.01, help='Threshold of p(chi2) below which to run BH and mask the most significant window')
    parser.add_argument('--doprefit', dest='doprefit', action="store_true", help='Perform ROOT prefit before quickFit')
    parser.add_argument('--dochi2fit', dest='dochi2fit', action="store_true", help='Minimize chi2 instead of NLL')
    parser.add_argument('--dochi2constraints', dest='dochi2constraints', action="store_true", help='Include the constraint terms into chi2. Becomes virtually identical to NLL this way.')
    parser.add_argument('--useSumW2', dest='useSumW2', action='store_true', help='Use data hist errors for chi2 instead of sqrt(N_fit)')
    parser.add_argument('--folder', dest='folder', type=str, default='run', help='Output folder to store configs and results (default: run)')
    parser.add_argument('--spursigfile', dest='spursigfile', type=str, help='Path to json file containing spurious signal dict')
    parser.add_argument('--theouncfile', dest='theouncfile', type=str, help='Path to json file containing dict with theory normalization uncertainty')
    parser.add_argument('--sysfile', dest='sysfile', type=str, help='Path to json file containing signal systematics dict')
    parser.add_argument('--covariancefile', dest='covariancefile', type=str, help='Path to json file containing signal systematics covariance dict')
    parser.add_argument('--categoryname', dest='categoryname', type=str, default='J100yStar06', help='Name of category to fit')

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

    spursig=0
    if args.spursigfile:
        with open(args.spursigfile) as f:
            dict_spursig = json.load(f)
        spursig = dict_spursig[str(args.sigmean)][str(args.sigwidth)]['0']['uncertainty']

    theounc=0
    if args.theouncfile:
        with open(args.theouncfile) as f:
            dict_theounc = json.load(f)
        theounc = dict_theounc[str(args.sigmean)]['xsec_uncertainty']

    systdict = None
    covariancedict = None
    if args.sysfile:
        with open(args.sysfile) as f:
            systdict = json.load(f)[str(args.sigmean)]
    if args.covariancefile:
        with open(args.covariancefile) as f:
            covariancedict = json.load(f)[str(args.sigmean)]


    run_anaFit(datafile=args.datafile,
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
               doBH=args.doBH,
               sigmean=args.sigmean,
               sigwidth=args.sigwidth,
               folder=args.folder,
               signame=args.signame,
               maskthreshold=args.maskthreshold,
               doprefit=args.doprefit,
               dochi2fit=args.dochi2fit,
               dochi2constraints=args.dochi2constraints,
               useSumW2=args.useSumW2,
               spursig=spursig,
               theounc=theounc,
               systdict=systdict,
               covariancedict=covariancedict,
               categoryname=args.categoryname)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
