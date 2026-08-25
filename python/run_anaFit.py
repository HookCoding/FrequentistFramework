#!/usr/bin/env python

from __future__ import print_function
import os,sys,re,argparse,subprocess,shutil
import json
import platform
from pathlib import Path
from ExtractPostfitFromWS import PostfitExtractor
from ExtractFitParameters import FitParameterExtractor
from PreFit import PreFitter
try:
    from python.analysis_bumphunter import run_bumphunter
except ModuleNotFoundError:
    from analysis_bumphunter import run_bumphunter
try:
    from python.analysis_fit import build_fit_extract as _build_fit_extract
except ModuleNotFoundError:
    from analysis_fit import build_fit_extract as _build_fit_extract
try:
    from python.analysis_templates import replaceinfile
except ModuleNotFoundError:
    from analysis_templates import replaceinfile
try:
    from python.analysis_cli import main as _cli_main
except ModuleNotFoundError:
    from analysis_cli import main as _cli_main
try:
    from python.analysis_provenance import (
        build_analysis_provenance as _build_analysis_provenance,
        build_file_provenance as _build_file_provenance,
        calculate_file_sha256 as _calculate_file_sha256,
        collect_scientific_runtime as _collect_scientific_runtime,
        get_git_revision as _get_git_revision,
        get_repository_root as _get_repository_root,
        resolve_analysis_path as _resolve_analysis_path,
    )
    from python.analysis_results import write_analysis_results
except ModuleNotFoundError:
    from analysis_provenance import (
        build_analysis_provenance as _build_analysis_provenance,
        build_file_provenance as _build_file_provenance,
        calculate_file_sha256 as _calculate_file_sha256,
        collect_scientific_runtime as _collect_scientific_runtime,
        get_git_revision as _get_git_revision,
        get_repository_root as _get_repository_root,
        resolve_analysis_path as _resolve_analysis_path,
    )
    from analysis_results import write_analysis_results
try:
    from python.analysis_commands import execute as _execute, execute_required as _execute_required
except ModuleNotFoundError:
    from analysis_commands import execute as _execute, execute_required as _execute_required
try:
    from python.analysis_config import (
        detect_parameter_count,
        validate_fit_range,
        validate_output_folder,
    )
except ModuleNotFoundError:
    from analysis_config import detect_parameter_count, validate_fit_range, validate_output_folder
import ROOT


def execute(cmd):
    return _execute(cmd)


def execute_required(cmd, description, expected_outputs=()):
    return _execute_required(cmd, description, expected_outputs, execute_fn=execute)


def get_repository_root():
    return _get_repository_root(module_file=__file__)


def resolve_analysis_path(path, repository_root=None):
    return _resolve_analysis_path(path, repository_root=repository_root)


def calculate_file_sha256(path):
    return _calculate_file_sha256(path)


def build_file_provenance(path, repository_root=None):
    return _build_file_provenance(path, repository_root=repository_root)


def get_git_revision(repository_path):
    return _get_git_revision(repository_path)


def collect_scientific_runtime():
    return _collect_scientific_runtime(
        root_module=ROOT,
        platform_module=platform,
        executable=sys.executable,
    )


def build_analysis_provenance(
    datafile,
    datahist,
    topfile,
    categoryfile,
    backgroundfile,
    signalfile,
    rangelow,
    rangehigh,
    dosignal,
    dolimit,
    doprefit,
    maskthreshold,
):
    return _build_analysis_provenance(
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
        repository_root_fn=get_repository_root,
        revision_fn=get_git_revision,
        runtime_fn=collect_scientific_runtime,
        file_provenance_fn=build_file_provenance,
    )


def build_fit_extract(*args, **kwargs):
    return _build_fit_extract(
        *args,
        execute_required_fn=execute_required,
        execute_fn=execute,
        root_module=ROOT,
        postfit_extractor=PostfitExtractor,
        fit_parameter_extractor=FitParameterExtractor,
        **kwargs,
    )


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
    validate_fit_range(rangelow, rangehigh)
    validate_output_folder(folder)
    nbins=rangehigh - rangelow
    print("Fitting", nbins, "bins in range", rangelow, "-", rangehigh)
    args_names = locals()
    for key, value in args_names.items():
      print(f"{key}: {value}")

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
            nPars = detect_parameter_count(backgroundfile)
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

    if pval_global > maskthreshold : #or True:
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

        if pval_masked > maskthreshold:
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
    if dolimit and dosignal and pval_global > maskthreshold:
        print("Now running quickLimit")
        #rtv=execute("timeout --foreground 1800 quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-8 --muScanPoints 20 --minStrat 1 --nllOffset 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")))
        rtv=execute("quickLimit -f %s -d combData -p %s --checkWS 1 --initialGuess 100000 --minTolerance 1E-06 --muScanPoints 20 --minStrat 2 --nllOffset 0 --GKIntegrator 1 -o %s" % (wsfile, poi, outputfile.replace("FitResult","Limits")))
        if rtv != 0:
            print("WARNING: Non-zero return code from quickLimit. Check if tolerable")
    
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

    write_analysis_results(
        folder=folder,
        p_chi2=final_p_chi2,
        masked=fit_was_masked,
        provenance=provenance,
    )

    return 0

def main(args):
    return _cli_main(args, run_anaFit)



if __name__ == "__main__":  
    sys.exit(main(sys.argv[1:]))
