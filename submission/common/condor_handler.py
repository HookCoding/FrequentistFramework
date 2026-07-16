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
    #self.email = 'alex.gekow@cern.ch'
    self.email = 'lisandro.tomas.bazzano.hurrell@cern.ch'

  def send_job(self,command,tag) :
    # tag: if sending many jobs, tag distinguishes .sub and .sh files. (e.g.: mR)
    # outputFolder: after running on Condor all outputs are copied back to ${localdir}/$outputFolder

    # make files
    bashfile = self.make_bash_file(command, tag)
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
      #fr.write('localdir=/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework\n')
      fr.write('localdir=/afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework\n')
      fr.write('export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase\n')
      fr.write('source /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh\n\n')
      # general setup:
      #fr.write('cd /afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework\n')
      fr.write('cd /afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework\n')
      fr.write('source scripts/setup_buildCombineFit.sh\n')

      # Run the command:
      fr.write('echo \"Evaluating command: \"' + command + "\n")
      fr.write(command+'\n')
      
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
      # fsubcondor.write('requirements    = (OpSysAndVer =?= "CentOS7")\n')
      fsubcondor.write('\nqueue 1\n')

    print ("Made job file",batchFile)
    return batchFile


if __name__ == "__main__":
  """
  Make condor submission per fit
  """
  ##############################################
  ##############################################
  
  rangelow="125"
  rangehigh="1000"

  #params_B = "five"
  #params_BS = "four"
  #params_B = "six"
  #params_BS = "five"
  #params_B = "seven"
  #params_BS = "six"
  #params_B = "eight"
  #params_BS = "seven"
  
  #params_B = "six"
  #params_BS = "four"
  #params_B = "seven"
  #params_BS = "five"
  #params_B = "eight"
  #params_BS = "six"
  #params_B = "nine"
  #params_BS = "seven"
  params_B = "ten"
  params_BS = "eight"
  
  ##############################################
  ##############################################

  # S+B fit of many toy pseudodata histograms
  #mass = list(range(200, 1000, 50))
  

  # widths taken from mjj resolution 
  #mass = list(range(150, 1000, 50))
  #widths = [10, 8.5, 7.6, 7, 6.5, 6, 5.8, 5.5, 5.2,   5, 4.8, 4.7, 4.5, 4.4, 4.3, 4.2, 4.1] # in percent
  
  # widths taken from mjj resolution 
  mass =   [ 100, 120,  140, 150,  160, 180, 200, 225, 250, 300,  350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950]
  widths = [12.5,  11, 10.5,  10,  9.5,   9, 8.5,   8, 7.6,   7,  6.5,   6, 5.8, 5.5, 5.2,   5, 4.8, 4.7, 4.5, 4.4, 4.3, 4.2, 4.1] # in percent
  times_width = 1

  # Z' spurious signal
  #mass   =   [150, 160, 180, 200, 225, 250, 300, 350, 400]
  #widths =   [ -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1]

  #mass = [150]
  #mass = list(range(350, 1000, 50))
  #widths = [9, 8, 7, 7.25, 6.0, 5.8, 5.6, 5.4, 5.2, 5, 4.8, 4.6, 4.5, 4.3, 4.2, 4.1] # in percent
  #widths = [10]
  #widths = [7.25, 6.0, 5.8, 5.6, 5.4, 5.2, 5, 4.8, 4.6, 4.5, 4.3, 4.2, 4.1] # in percent
  # Number of toys in pseudodata file
  
  pseudodata_index = range(0,100)
  #pseudodata_index = range(0,1000)

  assert len(mass) == len(widths), "Number of mass points and widths are not equal"


  signalInjection = True
  #si_means  = [650,650,650,650,650,650]
  #si_widths = [5,5,5,5,5,5]
  #si_amps   = [0,1,2,3,4,5]
  #si_means  = [200,200,200,200,200,200,400,400,400,400,400,400,600,600,600,600,600,600,800,800,800,800,800,800]
  #si_widths = [5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5]
  #si_widths = [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]
  #si_widths = [15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15]

  si_means = [120,150,180,200,250,300,400,600,800]
  si_widths = [15,15,15,15,15,15,15,15,15]
  si_means = [600,800]
  si_widths = [15,15]
  #si_widths = [10,10,10,10,10,10,10,10,10]
  #si_widths = [5,5,5,5,5,5,5,5,5]
  
  si_amps   = [0,1,2,3,4,5] 
  
  # Z' spurious signal signal injection
  #si_means   =   [150, 160, 180, 200]
  #si_widths  =   [ -1,  -1,  -1,  -1]
  #si_means   =   [225, 250, 300, 350, 400]
  #si_widths  =   [ -1,  -1,  -1,  -1, -1]


  if signalInjection:
      #mass = [650]
      #widths = [5]
      mass = si_means
      widths = si_widths

  argsfile = "condor_args.txt"
  with open(argsfile, "w") as f:
    for i in range(len(mass)):
      m = mass[i]
      w = widths[i]*times_width
      #print(m,w)
      for p in pseudodata_index:
        #print(p)
        tag = f"mass{m}_width{w:.2f}_pseudodata{p}"

        if signalInjection:
          # injection
          for si in range(len(si_amps)):
            #si_mean  = si_means[si] 
            #si_width = si_widths[si]
            si_mean = m
            si_width = w
            si_amp   = si_amps[si]
            #if m != si_mean: continue
            
            # injection of gaussians
            if w > 0:# gaus
              signalInjection_tag = "_injected_mean"+str(si_mean)+"_width"+str(si_width)+"_amp"+str(si_amp)
              outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/injected/pseudodatafits_"+params_BS+"Par_quickFitEdit_minTol"+signalInjection_tag+"/fit_"+params_BS+"Par_"+tag+signalInjection_tag
            else: # z prime injection
              signalInjection_tag = "_injected_mean"+str(si_mean)+"_amp"+str(si_amp)
              outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/injected_zprime/pseudodatafits_"+params_BS+"Par_quickFitEdit_minTol"+signalInjection_tag+"/fit_"+params_BS+"Par_"+tag+signalInjection_tag

            # Create an args file so we can submit one job which will automatically expand to an individual job per argument
            f.write(f"-m {m} -w {w:.2f} -p {p} -M {si_mean} -W {si_width} -A {si_amp} -r {outputdir}")
            #f.write(f"-m {m} -w {w:.2f} -p {p} -sim {si_mean} -siw {si_width:.2f} -sia {si_amp} -r {outputdir}")
            f.write('\n')
            #print(si_mean,si_width,si_amp)
        else:
          # SS
          #outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+params_B+"Par/pseudodatafits_"+params_BS+"Par/fit_"+params_BS+"Par_"+tag
          #outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/minimumStudy/120_run_"+params_B+"Par/pseudodatafits_"+params_BS+"Par/fit_"+params_BS+"Par_"+tag
          #outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/pseudodatafits_"+params_BS+"Par_minimizerTolerance_01/fit_"+params_BS+"Par_"+tag
          #outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/pseudodatafits_"+params_BS+"Par_1000toys/fit_"+params_BS+"Par_"+tag
          
          if w > 0:# gaus
            outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/pseudodatafits_"+params_BS+"Par_quickFitEdit_minTol/fit_"+params_BS+"Par_"+tag
          else:# z prime
            outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/pseudodatafits_"+params_BS+"Par_quickFitEdit_minTol_zprime/fit_"+params_BS+"Par_"+tag
            #outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/bkg_only_pseudodatafits_"+params_BS+"Par_quickFitEdit_minTol_zprime/fit_"+params_BS+"Par_"+tag
          
          #outputdir = "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_"+rangelow+"_"+rangehigh+"_"+params_B+"Par/pseudodatafits_"+params_BS+"Par_quickFitEdit_minTol_1p5width/fit_"+params_BS+"Par_"+tag
          # Create an args file so we can submit one job which will automatically expand to an individual job per argument
          f.write(f"-m {m} -w {w:.2f} -p {p} -r {outputdir}") #-B {params_BS} -S {params_B} -L {rangelow} -H {rangehigh}
          f.write('\n')

        # cmd = f". scripts/run_anaFitLoop.sh -m {m} -w {w:.2f} -p {p} -r {outputdir}"
        # ch.send_job(cmd, tag)

