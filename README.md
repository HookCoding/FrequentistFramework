# FrequentistFramework

This code is very preliminary and under construction, and its documentation is a work in progress. 

This is a frequentist statistical analysis framework based on:
https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/XmlAnaWSBuilder

You can also see the slides in the _docs/_ directory. 

# Install

This follows the README of the XmlAnaWSBuilder and quickFit. pyBumpHunter is run in a virtualenv to run python 3.6 alongside python 2.7 setup with ROOT

```
setupATLAS -c centos7
lsetup git
git clone https://:@gitlab.cern.ch:8443/atlas-phys-exotics-dijet-tla/FrequentistFramework.git
cd FrequentistFramework/
source scripts/install_FrequentistFramework.sh
```

If you plan to run the NLOFit, you need to prepare input workspaces from the template histograms in this repository. For that, run
```
source scripts/HistFactory/prepareInput.sh
source scripts/HistFactory/generate.sh
```

# Setup

In the future you can setup your environment via
```
setupATLAS -c centos7
source scripts/setup_buildCombineFit.sh
```

# Run

Example run command:
```
XMLReader -x config/dijetTLA/dijetTLA_J75yStar03.xml -s 0 --plotOption logy
```
This command will make a RooWorkspace starting J75-triggered data from https://arxiv.org/abs/1804.03496, fitted with the five parameter background function. It will also generate a summary PDF with the fit result.

To run pyBumpHunter, the virtualenv needs to be activated and deactivated afterwards. The ROOT setup can mess up $PYTHONPATH for numpy and other packages, so it needs to be overwritten when running scripts.
```
source pyBumpHunter/pyBH_env/bin/activate
# execute pyBumpHunter scripts like this:
env PYTHONPATH="" python3 python/FindBHWindow.py --inputfile XYZ.root
deactivate
```

# Scripts

The directory _python/_ contains a number of standalone Python scripts to plot and extracts the information from the workspace. Test files and .pdf files of how the output should look like are provided in each of the directories. 

   * _PlotWorkspace/PlotWorkspaceFit.py_ plots the fit and the data in the workspace (obtained from the command above) together with its residuals and pulls, and overlays it with the fit result from the previous statistical analysis framework. 

# quickFit and quickLimit

The output of the xmlAnaWSBuilder can be used as input for both quickFit and quickLimit to test signal hypotheses. The example from above produced the workspace _workspace/dijetTLA/dijetTLA_J75yStar03.root_ that contains a number of potential Gauss signals whose yields can be fit with quickFit. First, you can run a background-only fit with:
```
quickFit -f workspace/dijetTLA/dijetTLA_J75yStar03.root -d combData --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 -o run/FitResult.root
```
It can happen that quickFit claims "STATUS FAILED" for the fit, the lines above the final fit parameters will tell you the reason. Often it says:
```
Full matrix, but forced positive-definite
```
This usually means that a maximum in the likelihood could be found but that is not unique. E.g. two parameters can be varied leading to more or less the same post fit distribution. We choose to ignore this for now. 

To perform a signal+background fit (e.g. for a Gauss signal at 700 GeV with 7% width) run:
```
quickFit -f workspace/dijetTLA/dijetTLA_J75yStar03.root -d combData -p nsig_mean700_width7 --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 -o run/FitResult.root
```
quickFit will now treat the parameter _nsig_mean700_width7_ as floating POI in the fit while still keeping all others fixed to 0. The parameter specified here needs to exist in the RooStats workspace, meaning it needs to be defined by a custom signal .xml card in the xmlAnaWSBuilder.

If quickFit succeeds (or only fails because of forced positive-definite matrix) you can run quickLimit to set 95% CLs limits on your chosen parameter:
```
quickLimit -f workspace/dijetTLA/dijetTLA_J75yStar03.root -d combData -p nsig_mean700_width7 --checkWS 1 --hesse 1 --initialGuess 10000 -o run/Limits.root
```
With _initialGuess_ you need to specify the order of magnitude that you expect your limit to have. The default of 1 might be too small to achieve a difference between likelihoods larger than machine precision.

# Automation

All of this is performed in the python scripts _python/run_anaFit.py_ and _python/run_nloFit.py_. They need to be provided with _datafile_, _datahist_, _sigmean_ and _sigwidth_. They use generic copies of the xmlAnaWsBuilder .xml config files labeled as .template files which you can specify with the _topfile_ and _categoryfile_ variables. They are virtually identically but contain strings like DATAHIST instead of definite entries. These are then replaced in the run script with whatever you provided before executing the xmlAnaWSBuilder. The NLOFit will need additional inputs. Examples how to execute these scripts are given in _scripts/run_anaFit.sh_ and _scripts/run_nloFit.sh_.

If you produced many limits for different signal points, they can be summarized in a limit plot with _python/plotLimits.py_ that you will have to adapt to your paths, lumi, mass ranges etc.

# Importing Templates

To use histogram templates either for signal models or for the NLOFit background estimate in xmlAnaWSBuilder, they can best be turned into RooWorkspaces using HistFactory. Some python scripts for that are in _python/PrepareTemplates_, some bash scripts to execute them in order are in _scripts/HistFactory_. For the NLOFit templates, the histograms need to be cropped to match the fit range, have their bin width set to 1, normalized to an integral of 1 and depending on the PDF also add symmetric up/down variations. This is all performed in _scripts/HistFactory/prepareInput.sh_. For signal templates for the analytic fit, only the normalization needs to be done. The workspaces for NLOFit bkg and signal templates are generated via _scripts/HistFactory/generate.sh_. To add systematics to signal templates, _python/PrepareTemplates/dijetTLAnlo_genBkg.py_ should give a good first hint, since the MC variations are added as bkg systematics there.
