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
    # Stop if the setup refuses: it `return`s on a wrong working directory, and `return`
    # from a sourced script hands control straight back here. `return` works when this
    # driver is sourced, as the header says to; `exit` covers `bash scripts/...` (which is
    # how tests/repro.py runs it). Not a bare `exit` - that would kill an interactive shell.
    if ! . scripts/setup_buildAndFit.sh; then
        echo "ERROR: run this from the FrequentistFramework repository root." >&2
        return 1 2>/dev/null || exit 1
    fi

    mkdir -p $out_dir

    # Set if any fit below exits non-zero. Reset on every run, because this script is
    # sourced and a stale value from a previous run would be reported as this one's.
    anafit_failed=

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
            fitstatus=$?
            if [[ $fitstatus -ne 0 ]]; then
                anafit_failed=$fitstatus
            fi

            # The plots are still produced on a failed fit: they are the diagnostics you
            # want in order to see why it failed. What must not happen is the run reporting
            # success, which is what the status below is for.
            # A run that fails the p(chi2) gate is re-fitted with the BumpHunter window
            # blinded, and it is that masked fit that gets accepted. This used to plot the
            # unmasked file unconditionally, so on such a run postFit.pdf showed the
            # REJECTED fit with nothing saying so (KNOWN_ISSUES.md issue 48). It now plots
            # whichever fit was accepted, and the label says which that is - the label is
            # what keeps this from being a silent substitution.
            #
            # Deliberately ONE file, not two: post_fit.pdf from plot_postfit.cpp already
            # draws the unmasked and masked fits side by side with the masked region and the
            # BumpHunter p-value, so the rejected fit stays available as a diagnostic. A
            # second file here would add a name to the run folder, which tests/repro.py
            # compares exactly, forcing a baseline re-cut for a change that moves no number.
            postfit_to_plot=${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root
            postfit_label="unmasked fit"
            if [[ -f ${folder}/PostFit_anaFit_${pars}Par_bkgOnly_masked.root ]]; then
                postfit_to_plot=${folder}/PostFit_anaFit_${pars}Par_bkgOnly_masked.root
                postfit_label="masked fit - BumpHunter window blinded"
            fi
            python python/plotPostFit.py -i "$postfit_to_plot" \
                                         -o ${folder}/postFit.pdf -c "$channel" \
                                         -l "$postfit_label"

            root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\", \"$channel\")"
        done
    done

    if [[ -n $anafit_failed ]]; then
        echo
        echo "ERROR: run_anaFit.py exited $anafit_failed - the fit did not pass p(chi2) even with"
        echo "       the BumpHunter window masked, so this result must not be used. The plots in"
        echo "       $out_dir are diagnostics only. See KNOWN_ISSUES.md issue 38."
    fi
    # Report the fit's own verdict as this script's status. Not `exit`: the header says to
    # source this script, and tests/repro.py runs it with `bash` - a subshell exit sets $?
    # for both without killing an interactive shell.
    ( exit ${anafit_failed:-0} )
}
