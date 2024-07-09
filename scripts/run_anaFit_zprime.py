#!/usr/bin/env python

import subprocess, os, sys
from condor_handler import CondorHandler
sys.path.append("config/dijetTLA/")
from InitialParameters import initialParameters

##########################
## CHECK THIS		##
##########################

# Run mode and dataset
useBatch = False
runData  = True   # run PD
quietMode = False

# Specs
trigger = "J100"
#dataset = "unb2_smooth"
dataset = "partialDataset2_OF_2017_TG3" #"unb2_over-fitted"#  # 'unb2_insituScale' 
tag = "over-fitted"  # different calib options 

# Range of fit:
low= initialParameters[dataset][trigger]['low']
high=initialParameters[dataset][trigger]['high']
print low
print high

# Number of parameters in fit:
#parameters = [ "five", "six", "seven", "eight", "nine"]
parameters = [ "six" ] #"five","six", "seven", "eight"]
pd_parameters = [ "seven" ]#"six", "seven","eight", "nine"]

# ZPRIMES : 
# sigmeans = [ 550,600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600,1650,1700,1750,1800,1850,1900,1950,2000]
# sigmeans = [ 350, 400, 450, 500, 550,600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500]

# GAUSSIANS:
# J50
#sigmeans = [ 350, 375, 400, 425, 450, 500, 600, 700, 800 ] 
# J100
#sigmeans = [ 450, 500, 550, 600, 650, 700, 800, 1000, 1200, 1400, 1600, 1800]

#sigwidths = [ 5, 10, 15 ] 
sigmeans = ['bOnly']
sigwidths = [-999]

# do chi2 fit instead of NLL:
doChi2 = True
doChi2constraints = True

doLimit = False
doPrefit = True
maskthreshold=0.01

# Output folder -- where everything is stored:
# default in python/run_anaFit.py is run/
outFolder = "run/Unblinding2/BOnly_to_2017_FullGSCTest_Unb2_{}_TG3/".format(tag)
# XRootD:
XRootD_preffix = "root://eosatlas.cern.ch/"
eos_preffix = "/eos/user/m/mtoscani/Rel21/TLA/FrequentistFramework/"

############################################################################
# Don't modify this, unless running on PD
############################################################################


################## Create output folder:

# local or Condor, everything will be stored here:
if not os.path.isdir(eos_preffix + outFolder):
  subprocess.call("mkdir -p " + eos_preffix + outFolder, shell=True)
  if useBatch: # need to create a local folder for job submission:
    subprocess.call("mkdir -p " + outFolder, shell=True)

#######################################################3
# PREPARE CONDOR:

if useBatch:
  # Create location of .log, .sub and .sh files:
  batch_logs = outFolder + 'logs/'
  batch_scripts = outFolder +  'jobs/'
  if not os.path.isdir(batch_logs):
    subprocess.call("mkdir -p " + batch_logs, shell=True)
  if not os.path.isdir(batch_scripts):
    subprocess.call("mkdir -p " + batch_scripts, shell=True)

  # Prepare the handler:
  batchmanager = CondorHandler( batch_logs, batch_scripts)
  
  # In condor I store everything in an output/ folder and at the end I copy everything from $Condor/output to outFolder/
  #folder = 'output/'
#else:
  #folder = outFolder

# Everything is stored in EOS
folder =  eos_preffix + outFolder

################## Generate Symbolic link:

subprocess.call("ln -s $PWD/config/dijetTLA/AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder), shell=True)
print "ln -s $PWD/config/dijetTLA/AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder)

########################### START SUBMISSION:

for i,pars in enumerate(parameters):

  backgroundfile 	= "config/dijetTLA/background_dijetTLA_J100yStar06_{0}Par.template".format(pars)
  if runData:
    # Running on Data:
    datafile = initialParameters[dataset][trigger]['datafile']
    datahist = initialParameters[dataset][trigger]['datahist']
    nbkg	   = initialParameters[dataset][trigger]['nbkg']

  else:
    # Sanity check:
    if len(parameters) is not len(pd_parameters):
      print "ERROR: len(parameters) does not match len(pd_parameters)"
      print "ERROR: check that you're running N fit to (N+1) PD, or Nfit to N PD for closure"
      sys.exit()

    # Running on PD
    datafile = initialParameters[dataset][trigger][tag][pd_parameters[i]]
    datahist = "pseudodata"
    # 130ifb (overriden if doPrefit)
    nbkg = initialParameters[dataset][trigger]['nbkg']

    # 0 for no signal injection
    sigamp=0
    loopstart=0
    loopend=999

  #######################################################3
  # PREPARE COMMAND LINE: 
  
  for sigmean in sigmeans:

    for sigwidth in sigwidths:
      
      if sigwidth == -999:
	# xml template cards for zprime:
	topfile 	= "config/dijetTLA/dijetTLA_J100yStar06_zprime.template"
	categoryfile 	= "config/dijetTLA/category_dijetTLA_zprime.template"
	signalfile 	= ""
      else:
	# xml template cards for gaussians:
	topfile		= "config/dijetTLA/dijetTLA_J100yStar06.template"
	categoryfile  	= "config/dijetTLA/category_dijetTLA.template"
	signalfile 	= "config/dijetTLA/signal/signal_dijetTLA.template"

      # WS file name for xmlAnaWSBuilder:
      wsfile= XRootD_preffix + folder + "dijetTLA_combWS_{0}Par_{1}yStar06_{2}_gq0p1.root"
      # Output file name for quickFit:
      outputfile = XRootD_preffix + folder + "FitResult_anaFit_{0}Par_{1}yStar06_{2}.root"

      if sigmean == "bOnly":
	wsfile = wsfile.format(pars, trigger, "bOnly")
	outputfile = outputfile.format(pars, trigger, "bOnly")
	doSignal = False
	doLimit = False
	sigmean = 1000
	sigStr = "bOnly"
      else:
	if sigwidth == -999:
	  sigStr = "mR"+sigmean
	else: 
	  sigStr = "mean{0}_width{1}".format(sigmean,sigwidth)
	wsfile = wsfile.format(pars, trigger, sigStr)
	outputfile = outputfile.format(pars, trigger, sigStr)
	doSignal = True

      if runData:
	command = "python python/run_anaFit.py --datafile {0} --datahist {1} --topfile {2} --categoryfile {3} --backgroundfile {4} --wsfile {5} --outputfile {6} --nbkg {7} --rangelow {8} --rangehigh {9} --sigmean {10} --sigwidth {11} --folder {12} --maskthreshold {13}".format(datafile, datahist, topfile, categoryfile, backgroundfile, wsfile, outputfile, nbkg, low, high, sigmean, sigwidth, folder, maskthreshold)

      else: # run on PD:
	command = "python python/run_injections_anaFit.py --datafile {0} --datahist {1} --categoryfile {2} --topfile {3} --backgroundfile {4} --wsfile {5} --sigmean {6} --sigwidth {7} --nbkg {8} --rangelow {9} --rangehigh {10} --outputfile {11} --folder {12} --maskthreshold {13} --sigamp {14} --loopstart {15} --loopend {16}".format(datafile, datahist, categoryfile, topfile, backgroundfile,  wsfile, sigmean, sigwidth, nbkg, low, high, outputfile, folder, maskthreshold, sigamp, loopstart, loopend) 

      if signalfile != "":
	command += " --signalfile " + signalfile

      if doSignal:
	command += " --dosignal"

      if doLimit:
	command += " --dolimit"

      if doPrefit:
	command += " --doprefit"

      if doChi2:
	command += " --dochi2fit"

	if doChi2constraints:
	  command += " --dochi2constraints"

    #######################################################3
      # SUBMISSION:

      print "Submitting command:\n"
      print command

      if not quietMode:
	if not useBatch:
	  # Not working properly, don't know why. Just run it beforehand
	  subprocess.call(". scripts/setup_buildCombineFit.sh", shell=True)
	  subprocess.call(command, shell=True)

	else:
	  batchmanager.send_job( command,"job_" + pars + "_" + sigStr, outFolder )
	  print("submitted for {}\n\n".format(sigStr))
      print "\n"	
