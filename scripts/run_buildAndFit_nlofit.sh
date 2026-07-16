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


# setting some default inputs if not given by env vars
if [[ -z $datafile ]]; then
    # datafile=Input/data/dijetTLAnlo/data_J75yStar03_range400_2079_fixedBins.root
    datafile=Input/data/dijetTLAnlo/data_J100yStar06_range531_2079_fixedBins.root
fi
if [[ -z $datahist ]]; then
    datahist=data
fi
if [[ -z $inputmodel ]]; then
    inputmodel=Input/model/dijetTLAnlo/LO_CT14nnlo_reducedNPs_scaledOnly_reweightedNLO_inflated10000/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
fi
if [[ -z $bkgfile ]]; then
    bkgfile=config/dijetTLAnlo/background_dijetTLAnlo_J100yStar06_CT14nnlo.template
fi
if [[ -z $categoryfile ]]; then
    # categoryfile=config/dijetTLAnlo/category_dijetTLAnlo_J75yStar03.template
    categoryfile=config/dijetTLAnlo/category_dijetTLAnlo_J100yStar06.template
fi
if [[ -z $topfile ]]; then
    # topfile=config/dijetTLAnlo/dijetTLAnlo_J75yStar03.template
    topfile=config/dijetTLAnlo/dijetTLAnlo_J100yStar06.template
fi
if [[ -z $wsfile ]]; then
    wsfile=run/dijetTLAnlo_combWS_nloFit.root
fi
if [[ -z $sigmean ]]; then
    sigmean=1000
fi
if [[ -z $sigwidth ]]; then
    sigwidth=7
fi
if [[ -z $sigfit ]]; then
    sigfit=false
fi
if [[ -z $nbkg ]]; then
    nbkg="2E8,0,3E8"
fi
if [[ -z $outputfile ]]; then
    # outputfile=run/FitResult_nloFit_J75yStar03_mean${sigmean}_width${sigwidth}.root
    outputfile=run/FitResult_nloFit_J100yStar06_mean${sigmean}_width${sigwidth}.root
fi

tmpbkgfile=run/background_dijetTLAnlo_fromTemplate.xml
tmpcategoryfile=run/category_dijetTLAnlo_fromTemplate.xml
tmptopfile=run/dijetTLAnlo_fromTemplate.xml

# generate the config files on the fly in run dir
if [ ! -f run/AnaWSBuilder.dtd ]; then
    ln -s ../config/dijetTLAnlo/AnaWSBuilder.dtd run/AnaWSBuilder.dtd
fi

cp ${bkgfile} ${tmpbkgfile}
sed -i "s@INPUTMODEL@${inputmodel}@g" ${tmpbkgfile}

cp ${categoryfile} ${tmpcategoryfile}
sed -i "s@DATAFILE@${datafile}@g" ${tmpcategoryfile} #@ because datafile contains /
sed -i "s@DATAHIST@${datahist}@g" ${tmpcategoryfile}
sed -i "s@BACKGROUNDFILE@${tmpbkgfile}@g" ${tmpcategoryfile}
sed -i "s@NBKG@${nbkg}@g" ${tmpcategoryfile}
 
cp ${topfile} ${tmptopfile}
sed -i "s@CATEGORYFILE@${tmpcategoryfile}@g" ${tmptopfile}
sed -i "s@OUTPUTFILE@${wsfile}@g" ${tmptopfile}

XMLReader -x ${tmptopfile} -o "logy integral" -s 0 # minimizer strategy fast, binned data 
if [[ $? != 0 ]]; then
    echo "Non-zero return code from XMLReader. Check if tolerable"
fi

if ! $sigfit; then
    echo "Now running bkg-only quickFit"
    quickFit -f ${wsfile} -d combData --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 1 -o ${outputfile}
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from quickFit. Check if tolerable"
    fi

    #sometimes randomly fails at exit:
    python python/ExtractPostfitFromWS.py --datafile ${datafile/_fixedBins/} --datahist $datahist --wsfile ${outputfile} --outfile ${outputfile/FitResult/PostFit} || true
    python python/ExtractFitParameters.py --wsfile ${outputfile} --outfile ${outputfile/FitResult/FitParameters}
else
    # Don't need to set all POIs to 0, that is default behavior. Only specify the floating POI
    PARS="-p nsig_mean${sigmean}_width${sigwidth}"

    echo "Now running s+b quickFit"
    quickFit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 1 -o ${outputfile}
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from quickFit. Check if tolerable"
    fi

    python python/ExtractPostfitFromWS.py --datafile ${datafile/_fixedBins/} --datahist $datahist --wsfile ${outputfile} --outfile ${outputfile/FitResult/PostFit} || true
    python python/ExtractFitParameters.py --wsfile ${outputfile} --outfile ${outputfile/FitResult/FitParameters}

    echo "Now running quickLimit"
    quickLimit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --initialGuess 100000 --minStrat 1 --nllOffset 1 -o ${outputfile/FitResult/Limits}
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from quickLimit. Check if tolerable"
    fi
fi
