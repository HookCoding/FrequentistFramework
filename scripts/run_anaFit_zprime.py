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
runData  = True
quietMode = False

# Specs
trigger = "J100"
dataset = 'partialDataset'  # 'full', 'partialDataset', 'TLA2016'

# Range of fit:
low= initialParameters[dataset][trigger]['low']
high=initialParameters[dataset][trigger]['high']

# xml template cards:
topfile 	= "config/dijetTLA/dijetTLA_J100yStar06_zprime.template"
categoryfile 	= "config/dijetTLA/category_dijetTLA_zprime.template"
backgroundfile 	= "config/dijetTLA/background_dijetTLA_J100yStar06_fivePar.xml"

#sigmeans = [ 550,600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600,1650,1700,1750,1800,1850,1900,1950,2000]
sigmeans = ["bOnly"]
sigwidth=-999

doLimit = False

# Output folder -- where everything is stored:
# default in python/run_anaFit.py is run/
outFolder = "run/PartialDatasets/"+trigger+"/Global5par/"


############################################################################
# Don't modify this, unless running on PD
############################################################################


if runData:
  # Running on Data:
  
  datafile = initialParameters[dataset][trigger]['datafile']
  datahist = initialParameters[dataset][trigger]['datahist']
  nbkg	   = initialParameters[dataset][trigger]['nbkg']

else:
  # Running on PD for tests

  datafile = "Input/data/dijetTLA/PD_2016TLA_J100/PD_133ifb_WHW10_fixLow1_TR0_fixLow1_fixHigh_3par.root"
  datahist = "pseudodata"
  # 130ifb
  nbkg = initialParameters['full'][trigger]['nbkg']
  # 0 for no signal injection
  sigamp=0
  loopstart=0
  loopend=1
  # smooothing test:
  sigmeans = ["bOnly"]


################## Create output folder:

# local or Condor, everything will be stored here:
if not os.path.isdir(outFolder):
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
  folder = 'output/'
else:
  folder = outFolder
 
#######################################################3
# PREPARE COMMAND LINE: 
for sigmean in sigmeans:
  
  # WS file name for xmlAnaWSBuilder:
  wsfile= folder + "dijetTLA_combWS_{0}_{1}_gq0p1.root"
  # Output file name for quickFit:
  outputfile = folder + "FitResult_{0}yStar06_{1}.root"

  if sigmean == "bOnly":
    wsfile = wsfile.format(trigger, "bOnly")
    outputfile = outputfile.format(trigger, "bOnly")
    doSignal = False
    doLimit = False
    # dummy signal mass point: won't do any s+b fit
    sigmean = 1000
  else:
    wsfile = wsfile.format(trigger, "mR"+str(sigmean))
    outputfile = outputfile.format(trigger, "mR"+str(sigmean))
    doSignal = True

  if runData:
    command = "python python/run_anaFit.py --datafile {0} --datahist {1} --topfile {2} --categoryfile {3} --wsfile {4} --outputfile {5} --nbkg {6} --rangelow {7} --rangehigh {8} --sigmean {9} --sigwidth {10} --folder {11} --backgroundfile {12}".format(datafile, datahist, topfile, categoryfile, wsfile, outputfile, nbkg, low, high, sigmean, sigwidth, folder, backgroundfile)

  else: # run on PD:
    command = "python python/run_injections_anaFit.py --datafile {0} --datahist {1} --categoryfile {2} --topfile {3} --wsfile {4} --sigmean {5} --sigwidth {6} --nbkg {7} --rangelow {8} --rangehigh {9} --outputfile {10} --folder {11} --sigamp {12} --loopstart {13} --loopend {14} --backgroundfile {15}".format(datafile, datahist, categoryfile, topfile, wsfile, sigmean, sigwidth, nbkg, low, high, outputfile, folder, sigamp, loopstart, loopend, backgroundfile) 

  if doSignal:
    command += " --dosignal "

  if doLimit:
    command += " --dolimit"


#######################################################3
  # SUBMISSION:

  print "Submitting command:\n"
  print command

  if not quietMode:
    if not useBatch:
      # Not working properly, don't know why. Just run it beforehand
      #subprocess.call("bash scripts/setup_buildCombineFit.sh", shell=True)
      subprocess.call(command, shell=True)

    else:
      batchmanager.send_job( command,"mR{}".format(sigmean), outFolder )
      print("submitted for {}\n\n".format(sigmean))
    
