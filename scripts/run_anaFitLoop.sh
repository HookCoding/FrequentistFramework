#!/bin/bash
# Do an S+B fit per pseudodata after running an initial run_anaFit

{
    . scripts/setup_buildAndFit.sh

	# mass=($(seq 200 50 950))
	# widths taken from mjj resolution 
	# widths=(0.09 0.08 0.07 0.0725 0.06 0.058 0.056 0.054 0.052 0.05 0.048 0.046 0.045 0.043 0.042 0.041)
	# widths=(9 8 7 7.25 6 5.8 5.6 5.4 5.2 5 4.8 4.6 4.5 4.3 4.2 4.1)
	while getopts m:w:p:r: flag
	do
		case "${flag}" in
			m) mass=${OPTARG};;
			w) width=${OPTARG};;
			p) pseudodata=${OPTARG};;
			r) runfolder=${OPTARG};;
		esac
	done

	# # Loop over pseudo-data
    # for pd in $(seq 1 99)
    # do
		
		# Loop over signal models.
		# Gaussians with width determined from mjj resolution
		# for file in /afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework/config/dijetisrTLA/signal_ZPrime_Gauss/*.xml
		# array_length=${#mass[@]}
		# echo "arr ${array_length}"
		# for (( i=0; i<array_length; i++ ))
		# do
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
			rangelow=150
			rangehigh=1000
			#datafile=/afs/cern.ch/work/a/agekow/tlarun3/FrequentistFramework/run/Run3_TLA150_1000_fivePar_finebinned_scale29.55.root
			#datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/outputHistograms.root
			datafile=/afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework/run/Run3_TLA150_1000_fivePar_finebinned_scale29.55.root
			datahist="pseudodata_${pseudodata}"
			nbkg="dummy" #overwritten by prefit
			maskthreshold=0.01
			doprefit=1

			flags=""
			if (( $dosignal )); then flags="$flags --dosignal"; fi
			if (( $dolimit )); then flags="$flags --dolimit"; fi
			if (( $doprefit )); then flags="$flags --doprefit"; fi

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

	# 	done
    # done
}
