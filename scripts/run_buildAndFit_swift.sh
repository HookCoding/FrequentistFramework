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
    datafile=Input/data/dijetTLA/lookInsideTheBoxWithUniformMjj.root
    # datafile=Input/data/dijetTLA/PD_130ifb_GlobalFit_531_2079_fivepar_finebinned_J100.root
    # datafile=Input/data/dijetTLA/PD_130ifb_GlobalFit_531_2079_fourpar_finebinned_J100.root
fi
if [[ -z $datahist ]]; then
    # datahist=Nominal/DSJ75yStar03_TriggerJets_J75_yStar03_mjj_finebinned_all_data
    datahist=Nominal/DSJ100yStar06_TriggerJets_J100_yStar06_mjj_finebinned_all_data
    # datahist=pseudodata_0
fi
if [[ -z $categoryfile ]]; then
    # categoryfile=config/dijetTLA/category_dijetTLA_J75yStar03.template
    # categoryfile=config/dijetTLA/category_dijetTLA_J100yStar06_fourPar.template
    categoryfile=config/dijetTLA/category_dijetTLA_J100yStar06_fivePar.template
fi
if [[ -z $topfile ]]; then
    # topfile=config/dijetTLA/dijetTLA_J75yStar03.template
    topfile=config/dijetTLA/dijetTLA_J100yStar06.template
fi
if [[ -z $wsfile ]]; then
    wsfile=run/dijetTLA_combWS_swift.root
fi
if [[ -z $sigmean ]]; then
    sigmean=1200
fi
if [[ -z $sigwidth ]]; then
    sigwidth=7
fi
if [[ -z $sigfit ]]; then
    sigfit=false
fi
if [[ -z $whw ]]; then
    #window half width (full window = 2*whw+1)
    whw=9
    if [[ $topfile == *"J75"* ]]; then
	whw=13
    fi
fi
if [[ -z $minbin ]]; then
    minbin=0
    if [[ $topfile == *"J100"* ]]; then
	minbin=6
    fi
fi
if [[ -z $nbkg ]]; then
    # nbkg="4E7,0,6E7"
    nbkg="2E8,0,3E8"
fi
if [[ -z $outputfile ]]; then
    # outputfile=run/FitResult_swift_J75yStar03_mean${sigmean}_width${sigwidth}.root
    outputfile=run/FitResult_swift_J100yStar06_mean${sigmean}_width${sigwidth}.root
fi

binedges=( 400 420 441 462 484 507 531 555 580 606 633 661 690 720 751 784 818 853 889 927 966 1007 1049 1093 1139 1186 1235 1286 1339 1394 1451 1511 1573 1637 1704 1773 1845 1920 1998 2079 2163 2251 2342 2437 2536 2639 2746 2857 2973 3094 3220 3351 3487 3629 3776 3929 4088 4254 )
nbinedges=${#binedges[@]}

if [[ -z $maxbin ]]; then
    maxbin=$((nbinedges - 1))
fi

i=0
for edge in ${binedges[@]}; do
    if (($edge > $sigmean)); then
	binlow=$((i - whw - 1))
	if (($binlow < $minbin)); then
	    binlow=$minbin
	fi
	# if [[ $topfile == *"J100"* ]] && (( $binlow < minbin )); then
	#     binlow=$minbin
	# fi
	binhigh=$((binlow + 2*whw))
	if (($binhigh > $maxbin)); then
	    binhigh=$maxbin
	    binlow=$((i - whw - 1))
	    #if window too large for full bin range:
	    if (($binlow < $minbin)); then
		binlow=$minbin
	    fi
	fi
	break
    fi
    i=$((i+1))
done

# rangelow=${binedges[$binlow]}
# rangehigh=${binedges[$((binhigh+1))]} 
rangelow=531 #global fit
rangehigh=2079 #global fit
bins=$((rangehigh - rangelow))

echo "Fitting $bins bins in range $rangelow - $rangehigh"

tmpcategoryfile=run/category_dijetTLA_fromTemplate.xml
tmptopfile=run/dijetTLA_fromTemplate.xml

# generate the config files on the fly in run dir
if [ ! -f run/AnaWSBuilder.dtd ]; then
    ln -s ../config/dijetTLA/AnaWSBuilder.dtd run/AnaWSBuilder.dtd
fi

cp ${categoryfile} ${tmpcategoryfile}
sed -i "s@DATAFILE@${datafile}@g" ${tmpcategoryfile} #@ because datafile contains /
sed -i "s@DATAHIST@${datahist}@g" ${tmpcategoryfile}
sed -i "s@RANGELOW@${rangelow}@g" ${tmpcategoryfile}
sed -i "s@RANGEHIGH@${rangehigh}@g" ${tmpcategoryfile}
sed -i "s@BINS@${bins}@g" ${tmpcategoryfile}
sed -i "s@NBKG@${nbkg}@g" ${tmpcategoryfile}
 
cp ${topfile} ${tmptopfile}
sed -i "s@CATEGORYFILE@${tmpcategoryfile}@g" ${tmptopfile}
sed -i "s@OUTPUTFILE@${wsfile}@g" ${tmptopfile}

echo XMLReader -x ${tmptopfile} -o "logy integral" -s 0 # minimizer strategy fast, binned data 
XMLReader -x ${tmptopfile} -o "logy integral" -s 0 # minimizer strategy fast, binned data 
if [[ $? != 0 ]]; then
    echo "Non-zero return code from XMLReader. Check if tolerable"
fi

if ! $sigfit; then
    echo "Now running bkg-only quickFit"
    echo quickFit -f ${wsfile} -d combData --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 1 -o ${outputfile}
    quickFit -f ${wsfile} -d combData --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 1 -o ${outputfile}
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from quickFit. Check if tolerable"
    fi

    #sometimes randomly fails at exit:
    echo python python/ExtractPostfitFromWS.py --datafile $datafile --datahist $datahist --datafirstbin $rangelow --wsfile ${outputfile} --outfile ${outputfile/FitResult/PostFit} || true
    python python/ExtractPostfitFromWS.py --datafile $datafile --datahist $datahist --datafirstbin $rangelow --wsfile ${outputfile} --outfile ${outputfile/FitResult/PostFit} || true
    echo python python/ExtractFitParameters.py --wsfile ${outputfile} --outfile ${outputfile/FitResult/FitParameters}
    python python/ExtractFitParameters.py --wsfile ${outputfile} --outfile ${outputfile/FitResult/FitParameters}

else
    # Don't need to set all POIs to 0, that is default behavior. Only specify the floating POI
    PARS="nsig_mean${sigmean}_width${sigwidth}"

    echo "Now running s+b quickFit"
    echo quickFit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 -o ${outputfile}
    quickFit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 -o ${outputfile}
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from quickFit. Check if tolerable"
    fi

    echo python python/ExtractPostfitFromWS.py --datafile $datafile --datahist $datahist --datafirstbin $rangelow --wsfile ${outputfile} --outfile ${outputfile/FitResult/PostFit} || true
    python python/ExtractPostfitFromWS.py --datafile $datafile --datahist $datahist --datafirstbin $rangelow --wsfile ${outputfile} --outfile ${outputfile/FitResult/PostFit} || true
    echo python python/ExtractFitParameters.py --wsfile ${outputfile} --outfile ${outputfile/FitResult/FitParameters}
    python python/ExtractFitParameters.py --wsfile ${outputfile} --outfile ${outputfile/FitResult/FitParameters}

    echo "Now running quickLimit"
    echo quickLimit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --initialGuess 100000 -o ${outputfile/FitResult/Limits}
    quickLimit -f ${wsfile} -d combData -p $PARS --checkWS 1 --hesse 1 --initialGuess 100000 -o ${outputfile/FitResult/Limits}
    if [[ $? != 0 ]]; then
	echo "Non-zero return code from quickLimit. Check if tolerable"
    fi
fi
