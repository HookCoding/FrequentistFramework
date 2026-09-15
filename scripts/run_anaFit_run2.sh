#!/bin/bash
#
# Run 2 dijet TLA baseline fit: full Run 2 J100 mjj spectrum with the tile gap veto,
# 481 - 3000 GeV, six background parameters, background-only.
#
# Run from the repository root:   . scripts/run_anaFit_run2.sh
#
# The Run 3 ISR TLA configuration lives in scripts/run_anaFit.sh and is not touched by this.

out_dir=${OUT_DIR:-$PWD/run}
#out_dir=/eos/home-t/tofitsch/tlafits   # not writable from this account

{
    . scripts/setup_buildAndFit.sh

    mkdir -p $out_dir

    for pars in six #five seven
    do
        for rangelow in 481
        do
            rangehigh=3000

            # Background-only: no signal, no limits. The prefit supplies the starting
            # parameters and nbkg, so --doprefit is required (without it the PARn
            # placeholders in the background card are never substituted).
            dosignal=0
            dolimit=0
            doprefit=1

            # nsig is held constant at 0 in this bkg-only fit, so the signal Gaussian is
            # inert here. sigmean is kept inside [rangelow,rangehigh] anyway so the card stays
            # meaningful if dosignal is flipped on (the old default, 400, is below 481).
            sigmean=1000
            sigwidth=8

            # Full Run 2 dijet TLA, J100 trigger, yStar < 0.6. 1 GeV bins over 0-4000 GeV.
            datafile=Input/data/dijetTLA/mjj_spectra_J100_dataAll.root

            # Tile gap veto: rejects 1.0 < |eta| < 1.6.
            datahist=hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj
            # other selections in the same file (each also has an afterSelection/nominal path):
            #datahist=hists_yStar06/HLT_j0_perf_ds1_L1J100/h_mjj                   # no eta veto
            #datahist=hists_yStar06_rejectEta_10_24/HLT_j0_perf_ds1_L1J100/h_mjj   # wider veto
            #datahist=hists_yStar06_requireEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj  # gap region only
            #datahist=hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj

            folder=$out_dir/run_${rangelow}_${rangehigh}_${pars}Par

            # Run 2 cards: sqrt(s) = 13 TeV, matching PreFit.py which is hardcoded to 13000.
            # (the dijetisrTLA cards are 13.6 TeV and would prefit the wrong energy here)
            topfile=config/dijetTLA/dijetTLA_J100yStar06.template
            categoryfile=config/dijetTLA/category_dijetTLA.template
            backgroundfile=config/dijetTLA/background_dijetTLA_J100yStar06_${pars}Par.template
            signalfile=config/dijetTLA/signal/signal_dijetTLA.template

            wsfile=${folder}/dijetTLA_combWS_${pars}Par.root
            outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root

            # Published Run 2 analysis binning (57 bins, 481-2997) used for the rebinned
            # chi2/p-value and BumpHunter. Supplying it explicitly bypasses createBinning.py,
            # whose resolution fit is Run 3 ISR and only valid to 2000 GeV.
            rebinfile=Input/data/dijetTLA/fullRun2TLAJ100mjj.root
            rebinhist="Dijet mass distribution (J100)/Hist1D_y1"

            # Channel name is authored once, in the category card.
            channel=$(sed -n 's/.*<Channel Name="\([^"]*\)".*/\1/p' $categoryfile)

            nbkg="dummy" #overwritten by prefit
            maskthreshold=0.01

            flags=""
            if (( $dosignal )); then flags="$flags --dosignal"; fi
            if (( $dolimit  )); then flags="$flags --dolimit";  fi
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
                --rebinfile $rebinfile \
                --rebinhist "$rebinhist" \
                $flags

            python python/plotPostFit.py -i ${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root \
                                         -o ${folder}/postFit.pdf -c "$channel"

            root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\", \"$channel\")"
        done
    done
}
