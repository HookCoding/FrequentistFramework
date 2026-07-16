#!/bin/bash

dirname=${PWD##*/}

if [[ ! -d xmlAnaWSBuilder ]] || [[ ! -d quickFit ]]; then
    echo "Execute from FrequentistFramework directory!"
    return 1
fi

if [[ -z $_DIRXMLWSBUILDER ]]; then
    cd xmlAnaWSBuilder/
    source setup_lxplus.sh
    cd ..
fi

if [[ -z $_DIRFIT ]]; then
    cd quickFit/
    source setup_lxplus.sh
    cd ..
fi

mkdir -p run

trap 'echo caught interrupt and exiting;exit' INT

# setting some default inputs if not given by env vars
if [[ -z $datafile ]]; then
    datafile=Input/data/dijetTLAnlo/PD_130ifb_nloFit_CT14nnlo_531_2079_J100.root
fi
if [[ -z $datahist ]]; then
    datahist=pseudodata
fi
if [[ -z $inputmodel ]]; then
    inputmodel=Input/model/dijetTLAnlo/LO_CT14nnlo_reducedNPs_scaledOnly_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
fi
if [[ -z $bkgfile ]]; then
    bkgfile=config/dijetTLAnlo/background_dijetTLAnlo_J100yStar06_CT14nnlo_reweightedData.xml
fi
if [[ -z $categoryfile ]]; then
    categoryfile=config/dijetTLAnlo/category_dijetTLAnlo_J100yStar06.template
fi
if [[ -z $topfile ]]; then
    topfile=config/dijetTLAnlo/dijetTLAnlo_J100yStar06.template
fi
if [[ -z $wsfile ]]; then
    wsfile=run/dijetTLAnlo_combWS_nlofit.root
fi
if [[ -z $sigmean ]]; then
    sigmean=1200
fi
if [[ -z $sigwidth ]]; then
    sigwidth=7
fi
if [[ -z $sigamp ]]; then
    sigamp=0
fi
if [[ -z $sigfit ]]; then
    sigfit=true
fi
if [[ -z $nbkg ]]; then
    nbkg="9E8,0,15E8"
fi
if [[ -z $outputfile ]]; then
    outputfile=run/FitResult_nlofit_J100yStar06_mean${sigmean}_width${sigwidth}_amp${sigamp}.root
fi
if [[ -z $loopstart ]]; then
    loopstart=0
fi
if [[ -z $loopend ]]; then
    loopend=49
fi

tmpbkgfile=run/background_dijetTLAnlo_fromTemplate.xml
tmpcategoryfile=run/category_dijetTLAnlo_fromTemplate.xml
tmptopfile=run/dijetTLAnlo_fromTemplate.xml

injecteddatafile=$datafile
# need to use bc for bash to understand floating points...
if (( $(echo "$sigamp > 0" | bc -l) )); then
    echo "Injecting signal of amplitude ${sigamp}sigma (FWHM)"

    injecteddatafile=`basename $datafile`
    injecteddatafile="run/${injecteddatafile/.root/_injected_mean${sigmean}_width${sigwidth}_amp${sigamp}.root}"
    echo "python python/InjectGaussian.py --infile $datafile --histname $datahist --sigmean $sigmean --sigwidth $sigwidth --sigamp $sigamp --outfile $injecteddatafile"
    python python/InjectGaussian.py --infile $datafile --histname $datahist --sigmean $sigmean --sigwidth $sigwidth --sigamp $sigamp --outfile $injecteddatafile
fi

templatebinning=Input/data/dijetTLAnlo/data_J100yStar06_range531_2079_fixedBins.root
if [[ $topfile == *"J75"* ]]; then
    templatebinning=Input/data/dijetTLAnlo/data_J75yStar03_range400_2079_fixedBins.root
fi

# apply uniform binning
injecteddatafileorigbinned=$injecteddatafile

if [[ $injecteddatafile != *"_fixedBins.root" ]]; then
    python python/PrepareTemplates/unifyBinning.py $injecteddatafile
    injecteddatafilerebinned=${injecteddatafile/.root/_fixedBins.root}
    injecteddatafile=$injecteddatafilerebinned
fi

# generate the config files on the fly in run dir
if [ ! -f run/AnaWSBuilder.dtd ]; then
    ln -s ../config/dijetTLAnlo/AnaWSBuilder.dtd run/AnaWSBuilder.dtd
fi

for i in $(seq $loopstart $loopend);
do

    loopoutputfile=${outputfile/.root/_${i}.root}
    loopdatahist=${datahist}_${i}
    echo $loopoutputfile

    cp ${bkgfile} ${tmpbkgfile}
    sed -i "s@INPUTMODEL@${inputmodel}@g" ${tmpbkgfile}

    cp ${categoryfile} ${tmpcategoryfile}
    # cp config/dijetTLAnlo/category_dijetTLAnlo_J100yStar06.template ${categoryfile}
    sed -i "s@DATAFILE@${injecteddatafile}@g" ${tmpcategoryfile} #@ because datafile contains /
    sed -i "s@DATAHIST@${loopdatahist}@g" ${tmpcategoryfile}
    sed -i "s@BACKGROUNDFILE@${tmpbkgfile}@g" ${tmpcategoryfile}
    sed -i "s@NBKG@${nbkg}@g" ${tmpcategoryfile}
    
    cp ${topfile} ${tmptopfile}
    # cp config/dijetTLAnlo/dijetTLAnlo_J100yStar06.template ${topfile}
    sed -i "s@CATEGORYFILE@${tmpcategoryfile}@g" ${tmptopfile}
    sed -i "s@OUTPUTFILE@${wsfile}@g" ${tmptopfile}

    XMLReader -x ${tmptopfile} -o "logy integral" -s 0 # minimizer strategy fast, binned data 
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from XMLReader. Check if tolerable"
    fi

    tol=1E-8

    if ! $sigfit; then


	echo "Now running bkg-only quickFit on toy $i"
	quickFit -f ${wsfile} -d combData --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minTolerance $tol --minStrat 1 -o ${loopoutputfile}
	if [[ $? != 0 ]]; then
	    echo "Non-zero return code from quickFit. Check if tolerable"
	fi

	python python/ExtractPostfitFromWS.py --datafile $injecteddatafileorigbinned --datahist $loopdatahist --wsfile ${loopoutputfile} --outfile ${loopoutputfile/FitResult/PostFit}

    else

	PARS="nsig_mean${sigmean}_width${sigwidth}"

	echo "Now running s+b quickFit on toy $i"
	quickFit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minTolerance $tol --minStrat 1 -o ${loopoutputfile}
	if [[ $? != 0 ]]; then
	    echo "Non-zero return code from quickFit. Check if tolerable"
	fi

	python python/ExtractPostfitFromWS.py --datafile $injecteddatafileorigbinned --datahist $loopdatahist --wsfile ${loopoutputfile} --outfile ${loopoutputfile/FitResult/PostFit}

	loopoutputfile2=${loopoutputfile/FitResult/Limits}

	echo "Now running quickLimit on toy $i"
	timeout --foreground 1500 quickLimit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --initialGuess 100000 --minTolerance $tol --minStrat 1 --nllOffset 1 -o ${loopoutputfile2}
	if [[ $? != 0 ]]; then
	    echo "Non-zero return code from quickLimit. Check if tolerable"
	fi
    fi	
done
