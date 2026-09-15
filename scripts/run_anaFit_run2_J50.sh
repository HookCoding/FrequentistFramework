#!/bin/bash
#
# Run 2 dijet TLA low-mass fit: full Run 2 J50 mjj spectrum,
# 302 - 2997 GeV, six background parameters, background-only.
#
# Run from the repository root:   . scripts/run_anaFit_run2_J50.sh
#
# The J100 configuration lives in scripts/run_anaFit_run2.sh and is not touched by this.

out_dir=${OUT_DIR:-$PWD/run}

{
    . scripts/setup_buildAndFit.sh

    mkdir -p $out_dir

    for pars in six #five seven
    do
        for rangelow in 302
        do
            rangehigh=2997

            # Background-only: no signal, no limits. The prefit supplies the starting
            # parameters and nbkg, so --doprefit is required (without it the PARn
            # placeholders in the background card are never substituted).
            dosignal=0
            dolimit=0
            doprefit=1

            # nsig is held constant at 0 in this bkg-only fit, so the signal Gaussian is
            # inert here. sigmean is kept inside [rangelow,rangehigh] anyway so the card stays
            # meaningful if dosignal is flipped on.
            sigmean=1000
            sigwidth=8

            # Full Run 2 dijet TLA, J50 trigger, yStar < 0.6. 1 GeV bins over 0-4000 GeV.
            # The J50 spectrum turns on around 225 GeV, so 302 is safely on the plateau.
            # The stream is prescaled: above ~300 GeV it holds ~4-5x fewer events than J100.
            datafile=Input/data/dijetTLA/mjj_spectra_J50_dataAll.root

            # Unlike the J100 file this one carries a single selection - no eta-veto
            # variants and no afterSelection/nominal path - so there is nothing to choose.
            datahist=hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj

            folder=$out_dir/run_J50_${rangelow}_${rangehigh}_${pars}Par

            # Run 2 cards: sqrt(s) = 13 TeV, matching PreFit.py which is hardcoded to 13000.
            # The top, background and signal cards are shared with the J100 fit - they hold
            # only placeholders and the trigger-independent dijet function, so the "J100" in
            # two of the filenames is just where they were first authored.
            # (run_anaFit.py parses nPars from the background FILENAME, hence ${pars}Par.)
            topfile=config/dijetTLA/dijetTLA_J100yStar06.template
            categoryfile=config/dijetTLA/category_dijetTLA_J50yStar06.template
            backgroundfile=config/dijetTLA/background_dijetTLA_J100yStar06_${pars}Par.template
            signalfile=config/dijetTLA/signal/signal_dijetTLA.template

            wsfile=${folder}/dijetTLA_combWS_${pars}Par.root
            outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root

            # Standard dijet binning over 171-3217, used for the rebinned chi2/p-value and
            # BumpHunter. Over 481-2997 its edges are identical to the published J100 binning
            # in fullRun2TLAJ100mjj.root; this file just extends the same binning down to the
            # low-mass region J50 covers. Supplying it explicitly bypasses createBinning.py,
            # whose resolution input is unreadable from this account and caps at 1000 GeV.
            # ExtractPostfitFromWS.py clips the edge list to [rangelow,rangehigh].
            rebinfile=Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root
            rebinhist=data

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
