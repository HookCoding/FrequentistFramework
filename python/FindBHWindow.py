import argparse
import json
import sys

import numpy as np


# from https://stackoverflow.com/a/57915246
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="%prog [options]")
    parser.add_argument(
        "--inputfile",
        dest="inputfile",
        type=str,
        required=True,
        help="Root file with bkg and data histograms",
    )
    parser.add_argument(
        "--datahist", dest="datahist", type=str, default="data", help="data hist name"
    )
    parser.add_argument(
        "--bkghist", dest="bkghist", type=str, default="postfit", help="bkg hist name"
    )
    parser.add_argument(
        "--outputjson",
        dest="outputjson",
        type=str,
        default="BHresults.json",
        help="Name of output file with BH results",
    )
    parser.add_argument(
        "--inputxmlcard",
        dest="inputxmlcard",
        type=str,
        help="Path of xmlAnaWSBuilder card to insert BlindRange into",
    )
    parser.add_argument(
        "--outputxmlcard",
        dest="outputxmlcard",
        type=str,
        help="Output path of modified xmlAnaWSBuilder card",
    )
    parser.add_argument(
        "--usebinnumbers",
        dest="usebinnumbers",
        action="store_true",
        help="Use bin numbers instead of observable for BlindRange",
    )
    return parser.parse_args(argv)


def load_histograms(input_file, bkghist, datahist):
    # Deferred here, not top-level: this is the only function that needs
    # uproot, and this repository's own pytest dev venv cannot import it
    # at all - confirmed directly, matching every other deferred-import
    # module in this plan.
    import uproot

    with uproot.open(input_file) as file:
        bkg_th1 = file[bkghist]
        bkg, bins = bkg_th1.to_numpy()

        data_th1 = file[datahist]
        data, bins_data = data_th1.to_numpy()

    return bkg, bins, data, bins_data


def crop_data_to_background_range(bins, bins_data, data):
    firstbindata = 0
    lastbindata = 0

    for i, b in enumerate(bins_data):
        if b >= bins[0]:
            firstbindata = i
            break
    for i, b in enumerate(bins_data):
        if b <= bins[-1]:
            lastbindata = i

    return data[firstbindata:lastbindata], firstbindata


def run_bump_hunter(data, bkg, bins):
    # Deferred here, not top-level: this is the only function that needs
    # pyBumpHunter, and this repository's own pytest dev venv cannot
    # import it at all - confirmed directly.
    from datetime import datetime

    # pyBumpHunter's own BumpHunter1D implementation imports
    # matplotlib.pyplot at module load, which locks in whatever
    # backend is active at that moment. The original, pre-refactor
    # script called matplotlib.use("Agg") before importing pyBumpHunter
    # for exactly this reason (confirmed by reading its own module-
    # level import order) - selecting Agg here, before the import
    # below, preserves that ordering exactly (GitHub Copilot review,
    # PR #7). save_bump_plots()'s own matplotlib.use("Agg") call stays
    # too - a harmless no-op once Agg is already active - so this
    # function still needs no matplotlib import of its own beyond
    # this one, defensive line.
    import matplotlib

    matplotlib.use("Agg")

    import pyBumpHunter as BH

    # Hardcoded scan parameters preserved exactly, not promoted to CLI
    # flags (guardrail 11 forbids adding capability not already present).
    hunter = BH.BumpHunter1D(
        width_min=2,
        width_max=3,
        width_step=1,
        scan_step=1,
        npe=10000,
        nworker=1,
        seed=666,
        bins=bins,
    )

    print("####bump_scan call####")
    begin = datetime.now()
    hunter.bump_scan(data, bkg, is_hist=True)
    end = datetime.now()
    print(f"time={end - begin}")
    print("")

    hunter.bump_info(data, is_hist=True)

    return hunter


def save_bump_plots(hunter, data, bkg):
    # Deferred here, not top-level: this is the only function that needs
    # matplotlib, and this repository's own pytest dev venv cannot import
    # it at all - confirmed directly. Hardcoded, cwd-relative filenames
    # preserved exactly, not parameterized.
    import matplotlib

    matplotlib.use("Agg")

    hunter.plot_bump(data, bkg, is_hist=True, filename="bump.png")
    hunter.plot_stat(show_Pval=True, filename="BH_statistics.png")


def compute_mask_window(state, bins, firstbindata, use_bin_numbers):
    out_dict = {}
    out_dict["pyBHresult"] = state

    # The two formulas below are genuinely distinct, not aliases of each
    # other - preserved as two separate branches, not merged.
    if use_bin_numbers:
        out_dict["MaskMin"] = firstbindata + state["min_loc_ar"][0]
        out_dict["MaskMax"] = firstbindata + state["min_loc_ar"][0] + state["min_width_ar"][0]
    else:
        out_dict["MaskMin"] = bins[state["min_loc_ar"][0]]
        out_dict["MaskMax"] = bins[state["min_loc_ar"][0] + state["min_width_ar"][0]]

    # "%d,%d" truncates rather than rounds even though MaskMin/MaskMax may
    # originate as numpy floats - preserved exactly.
    out_dict["BlindRange"] = "%d,%d" % (out_dict["MaskMin"], out_dict["MaskMax"])

    return out_dict


def write_mask_window_json(out_dict, outputjson):
    with open(outputjson, "w") as f:
        json.dump(out_dict, f, cls=NpEncoder)


def main(argv=None):
    args = parse_args(argv)

    bkg, bins, data, bins_data = load_histograms(args.inputfile, args.bkghist, args.datahist)
    data, firstbindata = crop_data_to_background_range(bins, bins_data, data)

    hunter = run_bump_hunter(data, bkg, bins)
    save_bump_plots(hunter, data, bkg)

    state = hunter.save_state()
    out_dict = compute_mask_window(state, bins, firstbindata, args.usebinnumbers)
    write_mask_window_json(out_dict, args.outputjson)

    print(out_dict["BlindRange"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
