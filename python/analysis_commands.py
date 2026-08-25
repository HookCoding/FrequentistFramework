from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable


def build_xmlreader_command(topfile: str, outputfile: str | None = None) -> str:
    """Build the established XMLReader command for a generated top card."""
    del outputfile
    command = (
        "xmlAnaWSBuilder/build/bin/XMLReader -x %s " '-o "logy integral" --minimizerStrategy 0'
    )
    return command % topfile


def build_quickfit_command(
    wsfile: str,
    poi: str | None,
    maskrange: tuple[int, int] | None,
    outputfile: str,
) -> tuple[str, str]:
    """Build the established quickFit command and its log path."""
    poi_argument = "-p %s" % poi if poi else ""
    fit_range = "--range SBLo_Run3TLA,SBHi_Run3TLA" if maskrange else ""
    logfile = outputfile.replace("FitResult", "quickFitLog").replace(".root", ".log")
    command = (
        "quickFit/build/quickFit --chi2fit 1 --poissonerror 1 -f %s -d combData %s "
        "--checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 "
        "--saveErrors 1 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 "
        "--minTolerance 1E-6 %s -o %s &> %s"
    ) % (wsfile, poi_argument, fit_range, outputfile, logfile)
    return command, logfile


def execute(cmd: str) -> int:
    """Execute an external command and return its exit status."""
    print("EXECUTE:", cmd)
    sys.stdout.flush()
    return subprocess.call(cmd, shell=True)


def execute_required(
    cmd: str,
    description: str,
    expected_outputs: tuple[str, ...] | list[str] = (),
    execute_fn: Callable[[str], int] = execute,
) -> bool:
    """Run a command and assert exit status plus required file outputs."""
    rtv = execute_fn(cmd)

    if rtv != 0:
        print(f"ERROR: {description} failed with exit code {rtv}.")
        return False

    missing_outputs = [
        output_path for output_path in expected_outputs if not os.path.isfile(output_path)
    ]
    if missing_outputs:
        print(f"ERROR: {description} returned success but did not create required output files:")
        for output_path in missing_outputs:
            print(f"  - {output_path}")
        return False

    return True
