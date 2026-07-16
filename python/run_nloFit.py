#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
from ExtractPostfitFromWS import PostfitExtractor
from ExtractFitParameters import FitParameterExtractor
from PrepareTemplates import unifyBinning
from PreFitWS import PreFitter

dict_initialpars = {
    "alpha_var_alpha1_edit":-1.0007e+00,
    "alpha_var_pdf1_edit":-1.1401e-01,
    "alpha_var_pdf2_edit":-1.3525e+00,
    "alpha_var_pdf3_edit":-2.3984e+00,
    "alpha_var_pdf4_edit":1.6249e+00,
    "alpha_var_pdf5_edit":-3.6103e-02,
    "alpha_var_pdf6_edit":4.4677e-01,
    "alpha_var_pdf7_edit":1.8683e+00,
    "alpha_var_pdf8_edit":-5.6686e-01,
    "alpha_var_pdf9_edit":1.0884e+00,
    "alpha_var_pdf10_edit":-1.6455e+00,
    "alpha_var_pdf11_edit":3.3316e-01,
    "alpha_var_pdf12_edit":3.4948e-01,
    "alpha_var_pdf13_edit":-5.0233e-01,
    "alpha_var_pdf14_edit":-5.7377e-01,
    "alpha_var_pdf15_edit":5.8174e-01,
    "alpha_var_pdf16_edit":4.5264e-01,
    "alpha_var_pdf17_edit":-8.3712e-01,
    "alpha_var_pdf18_edit":-7.0269e-01,
    "alpha_var_pdf19_edit":1.0172e+00,
    "alpha_var_pdf20_edit":-2.9437e-01,
    "alpha_var_pdf21_edit":-2.3153e-01,
    "alpha_var_pdf22_edit":1.4756e+00,
    "alpha_var_pdf23_edit":-2.6926e+00,
    "alpha_var_pdf24_edit":-1.6066e+00,
    "alpha_var_pdf25_edit":-4.0304e-01,
    "alpha_var_pdf26_edit":9.4399e-02,
    "alpha_var_pdf27_edit":-1.8198e+00,
    "alpha_var_pdf28_edit":5.0544e-01,
    "alpha_var_scale1_edit":9.8909e-01
}

binning = [171, 188, 206, 224, 243, 262, 282, 302, 323, 344, 365, 387, 410, 433, 457, 481, 506, 531, 556, 582, 608, 635, 662, 690, 719, 748, 778, 808, 839, 871, 903, 936, 970, 1004, 1039, 1075, 1111, 1148, 1186, 1225, 1264, 1304, 1345, 1387, 1429, 1472, 1516, 1561, 1607, 1654, 1701, 1749, 1798, 1848, 1899, 1951, 2004, 2058, 2113, 2169, 2226, 2284, 2343, 2403, 2464, 2526, 2590, 2655, 2721, 2788, 2856, 2926, 2997, 3069, 3142, 3217]

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
    except Exception as e:
        print("ERROR: replaceinfile expects a list of tuples of strings [(old1,new1),...] as input")
        print(old_new_list)
        print(e)
        sys.exit(-1)

    with open(f, 'w') as file:
        file.write(filedata)

def build_fit_extract(topfile, datafile, datahist, datafirstbin, wsfile, fitresultfile, poi=None, maskrange=None, combinefile=None, externalchi2file=None, externalchi2fct=None, externalchi2bins=40, doprefit=False):
    rtv=execute('XMLReader -x %s -o "logy integral" -s 0' % topfile) # minimizer strategy fast
    if rtv != 0:
        print("WARNING: Non-zero return code from XMLReader. Check if tolerable")

    rtv=execute("manager -w edit -x %s" % combinefile)
    if rtv != 0:
        print("WARNING: Non-zero return code from workspaceCombiner. Check if tolerable")

    if doprefit:
        print(wsfile)
        pf = PreFitter(
            wsfile = wsfile,
            nRetries1 = 50000,
            nRetries2 = 50,
            updatews = 1,
        )

        pf.Fit()

    if poi:
        print("Now running s+b quickFit")
        _poi="-p %s" % poi
    else:
        print("Now running bkg-only quickFit")
        _poi=""

    if maskrange:
        _range="--range SBLo,SBHi"
        maskmin=maskrange[0]
        maskmax=maskrange[1]
    else:
        _range=""
        maskmin=-1
        maskmax=-1

    rtv=execute("quickFit -f %s -d combData %s --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 2 --nllOffset 1 --optConst 2 --GKIntegrator 1 --minTolerance 1E-10 %s -o %s" % (wsfile, _poi, _range, fitresultfile))
    if rtv != 0:
        print("WARNING: Non-zero return code from quickFit. Check if tolerable")

    postfitfile=fitresultfile.replace("FitResult","PostFit")
    parameterfile=fitresultfile.replace("FitResult","FitParameters")

    pfe = PostfitExtractor(
        datafile=datafile,
        datahist=datahist,
        datafirstbin=datafirstbin,
        wsfile=fitresultfile,
        maskmin=maskmin,
        maskmax=maskmax,
        externalchi2file=externalchi2file,
        externalchi2fct=externalchi2fct,
        externalchi2bins=externalchi2bins,
    )
    pval = pfe.GetPval()
    pfe.WriteRoot(postfitfile)

    fpe = FitParameterExtractor(wsfile=fitresultfile)
    fpe.WriteRoot(parameterfile)

    return (pval, postfitfile, parameterfile)

def run_nloFit(datafile,
               datahist,
               topfile,
               categoryfile,
               bkgfile,
               sigfile,
               modelfile,
               signalmodelfile,
               combinefile,
               wsfile,
               outputfile,
               nbkg,
               rangelow,
               rangehigh,
               constr=1,
               externalchi2file=None,
               externalchi2fct=None,
               externalchi2bins=40,
               doinitialpars=False,
               dosignal=False,
               dolimit=False,
               signame='',
               nsig='',
               maskthreshold=0.01,
               folder="run/",
               doprefit=False,):

    rangelow=binning.index(rangelow)
    rangehigh=binning.index(rangehigh)

    nbins=rangehigh - rangelow

    print("Fitting", nbins, "bins in range", rangelow, "-", rangehigh)

    # generate the config files on the fly in run dir
    if not os.path.isfile("{}/AnaWSBuilder.dtd".format(folder)):
        execute("ln -sf $PWD/config/dijetTLA/AnaWSBuilder.dtd $PWD/{}/AnaWSBuilder.dtd".format(folder))
    if not os.path.isfile("{}/Organization.dtd".format(folder)):
        execute("ln -sf $PWD/workspaceCombiner/dtd/Organization.dtd $PWD/{}/Organization.dtd".format(folder))

    tmpsigfile="{}/signal_dijetTLA_fromTemplate.xml".format(folder)
    tmpbkgfile="{}/background_dijetTLA_fromTemplate.xml".format(folder)
    tmpcategoryfile="{}/category_dijetTLA_fromTemplate.xml".format(folder)
    tmptopfile="{}/dijetTLA_fromTemplate.xml".format(folder)
    tmpcombinefile="{}/combineWS_dijetTLA_fromTemplate.xml".format(folder)
    combwsfile=wsfile.replace(".root", "_edit.root")

    shutil.copy2(topfile, tmptopfile) 
    shutil.copy2(categoryfile, tmpcategoryfile) 
    shutil.copy2(bkgfile, tmpbkgfile) 
    shutil.copy2(sigfile, tmpsigfile) 
    shutil.copy2(combinefile, tmpcombinefile) 

    replaceinfile(tmptopfile, 
                  [("CATEGORYFILE", tmpcategoryfile),
                   ("OUTPUTFILE", wsfile),
                   ("SIGNAME", signame),
               ])
    replaceinfile(tmpcategoryfile, 
                  [("DATAFILE", datafile),
                   ("DATAHIST", datahist),
                   ("BACKGROUNDFILE", tmpbkgfile),
                   ("RANGELOW", str(rangelow)),
                   ("RANGEHIGH", str(rangehigh)),
                   ("BINS", str(nbins)),
                   ("NBKG", nbkg),
                   ("SIGNAME", signame),
                   ("SIGNALFILE", tmpsigfile),
                   ("NSIG", nsig),
               ])
    replaceinfile(tmpbkgfile, 
                  [("BACKGROUNDMODEL", modelfile),])
    replaceinfile(tmpsigfile, 
                  [("SIGNALMODEL", signalmodelfile),])
    replaceinfile(tmpcombinefile, 
                  [("CONSTRSIGMA", str(constr)),
                   ("PARLIMIT", str(constr*5)),
                   ("INWSFILE", wsfile),
                   ("OUTWSFILE", combwsfile),
                   ("SIGNAME", signame),
               ])

    if doinitialpars:
        print("Inserting initial params")
        replacelist=[]
        for var,val in dict_initialpars.items():
            replacelist.append(('%s\[0,' % var, '%s[%.4e,' % (var, val)))
        replaceinfile(tmpcombinefile, replacelist) 
    else:
        print("Not inserting initial params")

    if dosignal:
        poi="nsig_%s" % signame
    else:
        poi=None

    pval_global, postfitfile, parameterfile = build_fit_extract(topfile=tmptopfile,
                                                                datafile=datafile.replace("_fixedBins",""), #undo the binning hack
                                                                datahist=datahist, 
                                                                datafirstbin=rangelow, 
                                                                wsfile=combwsfile, 
                                                                fitresultfile=outputfile, 
                                                                poi=poi,
                                                                combinefile=tmpcombinefile,
                                                                externalchi2file=externalchi2file,
                                                                externalchi2fct=externalchi2fct,
                                                                externalchi2bins=externalchi2bins,
                                                                doprefit=doprefit)

    print ("Global fit p(chi2)=%.3f" % pval_global)

    if pval_global > maskthreshold:
        print("p(chi2) threshold passed. Exiting with succesful fit.")
        _range=""
    else:
        print("p(chi2) threshold not passed.")
        print("Now running BH for masking.")

        # need to unset pythonpath in order to not use cvmfs numpy
        execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile {0} --outputjson {1}/BHresults.json --usebinnumbers; deactivate".format(postfitfile, folder))

        # pass results of pyBH via this json file
        with open("{}/BHresults.json".format(folder)) as f:
            BHresults=json.load(f)

        tmptopfilemasked=tmptopfile.replace(".xml","_masked.xml")
        tmpcategoryfilemasked=tmpcategoryfile.replace(".xml","_masked.xml")
        tmpcombinefilemasked=tmpcombinefile.replace(".xml","_masked.xml")
        wsfilemasked=wsfile.replace(".root","_masked.root")
        combwsfilemasked=wsfilemasked.replace(".root","_edit.root")
        outfilemasked=outputfile.replace(".root","_masked.root")

        shutil.copy2(tmptopfile, tmptopfilemasked) 
        shutil.copy2(tmpcategoryfile, tmpcategoryfilemasked) 
        shutil.copy2(tmpcombinefile, tmpcombinefilemasked)

        replaceinfile(tmptopfilemasked, 
                      [(tmpcategoryfile,tmpcategoryfilemasked),
                       (r'(OutputFile="[A-Za-z0-9_/.-]*")',r'\1 Blind="true"'),
                       (wsfile, wsfilemasked),])
        replaceinfile(tmpcategoryfilemasked, 
                      [(r'(Binning="\d+")', r'\1 BlindRange="%s"' % BHresults["BlindRange"]),])
        replaceinfile(tmpcombinefilemasked, 
                      [(wsfile, wsfilemasked),
                       (combwsfile, combwsfilemasked),])
        
        pval_masked,_,_ = build_fit_extract(tmptopfilemasked,
                                            datafile=datafile, 
                                            datahist=datahist, 
                                            datafirstbin=rangelow, 
                                            wsfile=combwsfilemasked, 
                                            fitresultfile=outfilemasked, 
                                            poi=poi, 
                                            maskrange=(int(BHresults["MaskMin"]), int(BHresults["MaskMax"])),
                                            combinefile=tmpcombinefilemasked,
                                            externalchi2file=externalchi2file,
                                            externalchi2fct=externalchi2fct,
                                            externalchi2bins=externalchi2bins,
                                            doprefit=doprefit)

        print("Masked fit p(chi2)=%.3f" % pval_masked)

        if pval_masked > maskthreshold:
            print("p(chi2) threshold passed. Continuing with successful (window-excluded) fit.")
            combwsfile=combwsfilemasked
            _range="--range SBLo,SBHi"
        else:
            print("p(chi2) threshold still not passed.")
            print("Exiting with failed fit status.")
            return -1
            
    # blindrange not yet implemented with quickLimit
    # if dolimit and dosignal and pval_global > maskthreshold:
    if dolimit and dosignal:
        print("Now running quickLimit")
        rtv=execute("timeout --foreground 28800 quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-10 --muScanPoints 20 --minStrat 2 --nllOffset 1 --optConst 2 --GKIntegrator 1 %s -o %s" % (combwsfile, poi, _range, outputfile.replace("FitResult","Limits")))
        if rtv != 0:
            print("WARNING: Non-zero return code from quickLimit. Check if tolerable")
    
    return 0

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
    parser.add_argument('--externalchi2bins', dest='externalchi2bins', type=int, default=40, help='Number of bins in external chi2 function')
    parser.add_argument('--doinitialpars', dest='doinitialpars', action="store_true", help='Initialise with empiric fit parameters != 0')
    parser.add_argument('--dosignal', dest='dosignal', action="store_true", help='Perform s+b fit (default: bkg-only)')
    parser.add_argument('--dolimit', dest='dolimit', action="store_true", help='Perform limit setting')
    parser.add_argument('--sigmean', dest='sigmean', type=int, default=1000, help='Mean of signal Gaussian for s+b fit (in GeV)')
    parser.add_argument('--sigwidth', dest='sigwidth', type=int, default=7, help='Width of signal Gaussian for s+b fit (in %)')
    parser.add_argument('--maskthreshold', dest='maskthreshold', type=float, default=0.01, help='Threshold of p(chi2) below which to run BH and mask the most significant window')
    parser.add_argument('--doprefit', dest='doprefit', action="store_true", help='Perform RooFit prefit before quickFit')
    parser.add_argument('--folder', dest='folder', type=str, default='run', help='Output folder to store configs and results (default: run)')

    args = parser.parse_args(args)
    signame="mean%s_width%s" % (args.sigmean, args.sigwidth)

    if not args.datafile.endswith("_fixedBins.root"):
        print("Copying %s into unit bin widths" % args.datafile)

        unifyBinning.main([args.datafile])
        args.datafile=args.datafile.replace(".root","_fixedBins.root")

    # create dir if not exists: https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
    try: 
        os.makedirs(args.folder)
    except OSError:
        if not os.path.isdir(args.folder):
            raise

    run_nloFit(datafile=args.datafile,
               datahist=args.datahist,
               topfile=args.topfile,
               categoryfile=args.categoryfile,
               bkgfile=args.bkgfile,
               sigfile=args.sigfile,
               modelfile=args.modelfile,
               signalmodelfile=args.signalmodelfile,
               combinefile=args.combinefile,
               wsfile=args.wsfile,
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
               maskthreshold=args.maskthreshold,
               folder=args.folder,
               doprefit=args.doprefit,)


if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
