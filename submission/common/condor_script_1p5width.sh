#!/bin/bash
while getopts m:w:p:M:W:A:r: flag #B:S:L:H:
do
case "${flag}" in
    m) mass=${OPTARG};;
    w) width=${OPTARG};;
    p) pseudodata=${OPTARG};;
    M) si_mean=${OPTARG};;
    W) si_width=${OPTARG};;
    A) si_amp=${OPTARG};;
    #B) pars_b=${OPTARG};;
    #S) pars_bs=${OPTARG};;
    #L) range_low=${OPTARG};;
    #H) range_high=${OPTARG};;
    r) runfolder=${OPTARG};;
esac
done

# wrapperFunction to prevent input arguments from being used in source call
wrapperfunction() {
    # define localdir from where to copy everything to condor:
    #localdir=/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework
    localdir=/afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework
    export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
    source /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh
    # general setup:
    #cd /afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework
    cd /afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework
    source scripts/setup_buildCombineFit.sh
}
wrapperfunction



    echo "pseudo data argument ${pseudodata}"
    folder=${runfolder}
    
    ##########################################################################################################################
    rangelow=87
    #rangelow=150
    #rangelow=200
    #rangelow=300
    rangehigh=1000
    
    #rangelow=${range_low}
    #rangehigh=${range_high}
    #pars_B=five
    #pars_BS=four
    #pars_B=six
    #pars_BS=five
    #pars_B=seven
    #pars_BS=six
    #pars_B=eight
    #pars_BS=seven
    
    pars_B=ten
    pars_BS=eight

    #pars_B=${pars_b}
    #pars_BS=${pars_bs}

    echo "${folder}"
    #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${pars}Par/
    mkdir -p ${folder}
    signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
    backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars_BS}Par.template
    categoryfile=config/dijetisrTLA/category_dijetisrTLA.template
    topfile=config/dijetisrTLA/dijetisrTLA.template
    wsfile=${folder}/dijetisrTLA_combWS_${pars_B}Par.root
    sigmean=${mass}
    sigwidth=${width}
    dosignal=1
    dolimit=0
    
    

    #datafile=/afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework/run/Run3_TLA150_1000_fourPar_finebinned_scale25.28.root
    #datafile=/afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework/run/Run3_TLA150_1000_fivePar_finebinned_scale25.28.root
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${pars}Par/Run3_TLA150_1000_${pars}Par_finebinned_scale25.28.root

    # bkg only // SS
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${pars_B}Par/Run3_TLA${rangelow}_${rangehigh}_${pars_B}Par_finebinned_scale25.28.root
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/minimumStudy/${rangelow}_run_${pars_B}Par/Run3_TLA${rangelow}_${rangehigh}_${pars_B}Par_finebinned_scale25.28.root
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/Run3_TLA87_1000_tenPar_finebinned_scale_1000toys.root
    
    # scaling
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars_B}Par/Run3_TLA${rangelow}_${rangehigh}_${pars_B}Par_finebinned_scale25.28.root
    # no scaling
    datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars_B}Par/Run3_TLA${rangelow}_${rangehigh}_${pars_B}Par_finebinned_scale.root
    
    outputfile=${folder}/FitResult_anaFit_${pars_SB}Par_pseudodata${p}_mean${sigmean}_width${sigwidth}.root

    # signal injected
    # scaled
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars_B}Par/injected/Run3_TLA${rangelow}_${rangehigh}_${pars_B}Par_finebinned_scale25.28_mean${si_mean}_width${si_width}_amp${si_amp}.root
    # no scaling
    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars_B}Par/injected/Run3_TLA${rangelow}_${rangehigh}_${pars_B}Par_finebinned_scale_mean${si_mean}_width${si_width}_amp${si_amp}.root
    #outputfile=${folder}/FitResult_anaFit_${pars_SB}Par_pseudodata${p}_injected_mean${si_mean}_width${si_width}_amp${si_amp}_fit_mean${sigmean}_width${sigwidth}.root
    ##########################################################################################################################

    datahist="pseudodata_${pseudodata}"
    nbkg="dummy" #overwritten by prefit
    maskthreshold=0.01
    doprefit=1

    flags=""
    if (( $dosignal )); then flags="$flags --dosignal"; fi
    if (( $dolimit )); then flags="$flags --dolimit"; fi
    if (( $doprefit )); then flags="$flags --doprefit"; fi

    # Run the command:
    #. scripts/setup_buildAndFit.sh
    . /afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/scripts/setup_buildAndFit.sh
    

    #./python/run_anaFit.py \
    /afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/python/run_anaFit.py \
        --datafile $datafile \
        --datahist $datahist \
        --backgroundfile $backgroundfile \
        --signalfile $signalfile \
        --categoryfile $categoryfile \
        --topfile $topfile \
        --wsfile $wsfile \
        --sigmean $sigmean \
        --sigwidth $sigwidth \
        --nbkg $nbkg \
        --rangelow $rangelow \
        --rangehigh $rangehigh \
        --outputfile $outputfile \
        --maskthreshold $maskthreshold \
        --folder $folder \
        $flags
