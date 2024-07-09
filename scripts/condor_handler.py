import os
import subprocess
# Stolen from Kate's magic repo
# CHECK LOCALDIR VARIABLE!!!

class CondorHandler(object) :

  def __init__(self,log_path,batch_path) :

    self.log_path = log_path
    self.batch_path = batch_path
    # workday (8hs), tomorrow (1day), longlunch(2hs), testmatch (3days), nextweek(1week)
    self.job_length = "testmatch"
    self.email = 'mariana.toscani@cern.ch'

  def send_job(self,command,tag, outputFolder) :
    # tag: if sending many jobs, tag distinguishes .sub and .sh files. (e.g.: mR)
    # outputFolder: after running on Condor all outputs are copied back to ${localdir}/$outputFolder

    # make files
    bashfile = self.make_bash_file(command, tag, outputFolder)
    jobfile = self.make_job_file(bashfile, tag)
    # do submit thing
    subprocess.call("condor_submit {0}".format(jobfile),shell=True)

  def make_bash_file(self,command, tag, outputFolder) :

    runFile = self.batch_path+"batch_{0}.sh".format(tag)

    queue = 'short.q'

    with open(runFile,"w") as fr :
      fr.write('#!/bin/bash\n')
      fr.write('#$ -M '+self.email+'\n')
      # define localdir from where to copy everything to condor:
      fr.write('localdir=/afs/cern.ch/work/m/mtoscani/public/TLA/FrequentistFramework/\n')
      # general setup:
      fr.write('export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase\n')
      fr.write('source /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh\n\n')
      # prepare condor directories:
      fr.write('mkdir dir\n')
      fr.write('cd dir\n')
      fr.write('mkdir out log err output\n')

      # copy packages required:
      fr.write('cp -rf ${localdir}/config . \n')
      fr.write('cp -rf ${localdir}/Input . \n')
      fr.write('cp -rf ${localdir}/python . \n')
      fr.write('cp -rf ${localdir}/pyBumpHunter . \n')
      fr.write('cp -rf ${localdir}/quickFit . \n')
      fr.write('cp -rf ${localdir}/workspaceCombiner . \n')
      fr.write('cp -rf ${localdir}/xmlAnaWSBuilder . \n')
      fr.write('cp -rf ${localdir}/scripts/setup_buildCombineFit.sh . \n\n')
      # TODO add outputfolder if exists? If no WS building, but yes fitting or limit  
      fr.write('ls -a \n')
      
      # Setup the packages:
      fr.write('source setup_buildCombineFit.sh\n')

      # Run the command:
      fr.write('echo \"Evaluating command: \"' + command + "\n")
      fr.write('eval ' + command + '\n')

      # Copy output back to local directory:
      #fr.write('cp -rf output/* ${localdir}/'+ outputFolder + '\n')
      
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
