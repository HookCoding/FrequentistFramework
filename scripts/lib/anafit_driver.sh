#
# Shared body of scripts/run_anaFit_run2.sh and scripts/run_anaFit_run2_J50.sh.
# The two drivers differ only in their configuration block (rangelow, rangehigh,
# datafile, datahist, folder prefix, categoryfile, rebinfile, rebinhist); every
# function below is byte-identical logic pulled out of both, sourced by each.
#
# Each function is called from inside the driver's own `{ ... }` block, not
# from inside another function, wherever a `return` needs to exit the sourced
# driver script itself rather than just the function - see _setup_environment.
#

_setup_environment() {
    local out_dir=$1
    if ! . scripts/setup_buildAndFit.sh; then
        return 1
    fi
    mkdir -p "$out_dir"
}

_build_flags() {
    local dosignal=$1 dolimit=$2 doprefit=$3
    local flags=""
    if (( dosignal )); then flags="$flags --dosignal"; fi
    if (( dolimit  )); then flags="$flags --dolimit";  fi
    if (( doprefit )); then flags="$flags --doprefit"; fi
    echo "$flags"
}

# Reads datafile, datahist, backgroundfile, signalfile, categoryfile, topfile,
# wsfile, sigmean, sigwidth, nbkg, rangelow, rangehigh, outputfile,
# maskthreshold, folder, rebinfile, rebinhist and flags from the caller's
# scope - the driver's configuration block sets every one of them before
# calling this. Returns run_anaFit.py's exit status.
_run_anafit() {
    local run_anafit=${RUN_ANAFIT:-./python/run_anaFit.py}
    $run_anafit \
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
}

# Sets postfit_to_plot and postfit_label in the caller's scope. A run that
# fails the p(chi2) gate is re-fitted with the BumpHunter window blinded, and
# it is that masked fit which was actually accepted - plotting the unmasked
# file unconditionally showed the REJECTED fit with nothing saying so
# (KNOWN_ISSUES.md issue 48). This plots whichever fit was accepted, and the
# label says which that is.
_select_postfit() {
    local folder=$1 pars=$2
    postfit_to_plot=${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root
    postfit_label="unmasked fit"
    if [[ -f ${folder}/PostFit_anaFit_${pars}Par_bkgOnly_masked.root ]]; then
        postfit_to_plot=${folder}/PostFit_anaFit_${pars}Par_bkgOnly_masked.root
        postfit_label="masked fit - BumpHunter window blinded"
    fi
}

_make_plots() {
    local postfit_to_plot=$1 folder=$2 channel=$3 label=$4 pars=$5
    python python/plotPostFit.py -i "$postfit_to_plot" \
                                 -o ${folder}/postFit.pdf -c "$channel" \
                                 -l "$label"

    root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\", \"$channel\")"
}

# Fires on ANY non-zero anafit_failed, not only a failed p(chi2) gate - a
# traceback or the rebin-pair ValueError says the same thing it does
# (KNOWN_ISSUES.md issue 47). Not fixed here, only moved.
#
# The final `( exit ... )` is what reports the fit's own verdict as this
# script's status: not `exit`, because the header says to source this script
# and tests/repro.py runs it with `bash` - a subshell exit sets $? for both
# without killing an interactive shell. It relies on this call being the last
# statement in the driver's `{ ... }` block, so its own exit status becomes
# the block's.
_report_failure() {
    local anafit_failed=$1 out_dir=$2
    if [[ -n $anafit_failed ]]; then
        echo
        echo "ERROR: run_anaFit.py exited $anafit_failed - the fit did not pass p(chi2) even with"
        echo "       the BumpHunter window masked, so this result must not be used. The plots in"
        echo "       $out_dir are diagnostics only. See KNOWN_ISSUES.md issue 38."
    fi
    ( exit ${anafit_failed:-0} )
}
