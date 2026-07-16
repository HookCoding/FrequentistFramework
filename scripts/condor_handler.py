import os
import subprocess
# Stolen from Kate's magic repo
# CHECK LOCALDIR VARIABLE!!!

class CondorHandler(object) :

  def __init__(self,log_path,batch_path) :

    self.log_path = log_path
    self.batch_path = batch_path
    # workday (8hs), tomorrow (1day), longlunch(2hs), testmatch (3days), nextweek(1week)
    self.job_length = "workday"
    self.email = 'alex.gekow@cern.ch'

  def send_job(self,command,tag, outputFolder) :
    # tag: if sending many jobs, tag distinguishes .sub and .sh files. (e.g.: mR)
    # outputFolder: after running on Condor all outputs are copied back to ${localdir}/$outputFolder

    # make files
    bashfile = self.make_bash_file(command, tag, outputFolder)
    jobfile = self.make_job_file(bashfile, tag)
    # do submit thing
    subprocess.call("condor_submit {0}".format(jobfile),shell=True)

  def make_bash_file(self,command, tag) :

    runFile = self.batch_path+"batch_{0}.sh".format(tag)

    queue = 'short.q'

    with open(runFile,"w") as fr :
      fr.write('#!/bin/bash\n')
      fr.write('#$ -M '+self.email+'\n')
      # define localdir from where to copy everything to condor:
      fr.write('localdir=/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework\n')
      # general setup:
      fr.write('cd /afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework\n')
      fr.write('source setup_buildCombineFit.sh\n')

      # Run the command:
      fr.write('echo \"Evaluating command: \"' + command + "\n")
      fr.write(command + '\n')
      
      fr.write('echo \'Done!\'')

    print ("Made run file",runFile)
    subprocess.call("chmod 755 " + runFile, shell=True )
    return runFile

  def make_job_file(self,runFile, tag) :

    batchFile = self.batch_path+"batch_{0}.job".format(tag)
    with open(batchFile, "w") as fsubcondor :
      fsubcondor.write('Universe        = vanilla\n')
      fsubcondor.write('Executable      = '+runFile+'\n')
      fsubcondor.write('+JobFlavour     = "{0}"\n'.format(self.job_length)) # 8 hours is default
      fsubcondor.write('Output          = {0}/stdout_{1}.txt\n'.format(self.log_path,tag))
      fsubcondor.write('Error           = {0}/stderr_{1}.txt\n'.format(self.log_path,tag))
      fsubcondor.write('log             = {0}/batch_{1}.log\n'.format(self.log_path,tag))
      fsubcondor.write('requirements    = (OpSysAndVer =?= "CentOS7")\n')
      fsubcondor.write('\nqueue 1\n')

    print ("Made job file",batchFile)
    return batchFile


if __name__ == "__main__":
  """
  Make condor submission per fit
  """
  # S+B fit of many toy pseudodata histograms
  mass = list(range(200, 1000, 50))
  # widths taken from mjj resolution 
  widths = [0.090, 0.080, 0.070, .0725, .060, 0.058, 0.056, 0.054, 0.052, 0.05, 0.048, 0.046, 0.045, 0.043, 0.042, 0.041]
  widths = [w*100 for w in widths]

  # Number of toys in pseudodata file
  pseudodata_index = range(1,100)

  assert len(mass) == len(widths), "Number of mass points and widths are not equal"

  logPath = "/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework/run/condor/"
  batchPath = logPath
  ch = CondorHandler(logPath, batchPath)

  for i in range(len(mass)):
    m = mass[i]
    w = width[i]
    for p in pseudodata_index:
      cmd = f". run_anaFitLoop.sh -m {m} -w {w} -p {p}"
      ch.make_bash_file(cmd, f"mass{m}_width{w}_pseudodata{p}")
