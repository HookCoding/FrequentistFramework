#!/bin/bash
while getopts m:w:p:r: flag
do
case "${flag}" in
    m) mass=${OPTARG};;
    w) width=${OPTARG};;
    p) pseudodata=${OPTARG};;
    r) runfolder=${OPTARG};;
esac
done

# wrapperFunction to prevent input arguments from being used in source call
wrapperfunction() {
    # define localdir from where to copy everything to condor:
    localdir=/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework
    export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
    source /cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh
    # general setup:
    cd /afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework
    source scripts/setup_buildCombineFit.sh
}
wrapperfunction



    echo "pseudo data argument ${pseudodata}"
    folder=${runfolder}
    mkdir -p ${folder}
    signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
    backgroundfile=config/dijetisrTLA/background_dijetisrTLA_fivePar.template
    categoryfile=config/dijetisrTLA/category_dijetisrTLA.template
    topfile=config/dijetisrTLA/dijetisrTLA.template
    wsfile=${folder}/dijetisrTLA_combWS_fivePar.root
    sigmean=${mass}
    sigwidth=${width}
    dosignal=1
    dolimit=0
    # outputfile=${folder}/FitResult_anaFit_fivePar_mean${sigmean}_width${sigwidth}.root
    outputfile=${folder}/FitResult_anaFit_fivePar_pseudodata${p}_mean${sigmean}_width${sigwidth}.root
    rangelow=130
    rangehigh=1000
    datafile=/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework/run/Run3_TLA130_1000_fivePar_finebinned_scale67.41.root
    datahist="pseudodata_${pseudodata}"
    nbkg="dummy" #overwritten by prefit
    maskthreshold=0.01
    doprefit=1

    flags=""
    if (( $dosignal )); then flags="$flags --dosignal"; fi
    if (( $dolimit )); then flags="$flags --dolimit"; fi
    if (( $doprefit )); then flags="$flags --doprefit"; fi

    # Run the command:
    . scripts/setup_buildAndFit.sh

    ./python/run_anaFit.py \
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