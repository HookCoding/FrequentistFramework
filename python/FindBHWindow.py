import matplotlib
matplotlib.use("Agg")
from datetime import datetime  # # Used to compute the execution time
import matplotlib.pyplot as plt
import uproot  # # Used to read data from a root file
import sys, re, os, argparse
import json
import numpy as np
import pyBumpHunter as BH

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

def _build_parser():
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--inputfile', dest='inputfile', type=str, required=True, help='Root file with bkg and data histograms')
    parser.add_argument('--datahist', dest='datahist', type=str, default='data', help='data hist name')
    parser.add_argument('--bkghist', dest='bkghist', type=str, default='postfit', help='bkg hist name')
    parser.add_argument('--outputjson', dest='outputjson', type=str, default='BHresults.json', help='Name of output file with BH results')
    parser.add_argument('--inputxmlcard', dest='inputxmlcard', type=str, help='Path of xmlAnaWSBuilder card to insert BlindRange into')
    parser.add_argument('--outputxmlcard', dest='outputxmlcard', type=str, help='Output path of modified xmlAnaWSBuilder card')
    parser.add_argument('--usebinnumbers', dest='usebinnumbers', action='store_true', help='Use bin numbers instead of observable for BlindRange')
    return parser

def _load_histograms(inputfile, bkghist, datahist):
    """Read the background and data histograms out of the postfit file.

    uproot's to_numpy() copies everything out before the file closes, so nothing returned here
    depends on the file staying open.
    """
    # Open the file
    with uproot.open(inputfile) as file:
        # Background
        bkg_th1 = file[bkghist]
        bkg, bins = bkg_th1.to_numpy()

        # Data
        data_th1 = file[datahist]
        data,bins_data = data_th1.to_numpy()

    return bkg, bins, data, bins_data

def _crop_data_to_bkg_range(data, bins_data, bins):
    """Cut the data array down to the bins the background histogram covers.

    firstbindata is the index of the first data edge at or above bins[0]. lastbindata is the
    index of the last data edge at or below bins[-1], used as an exclusive slice end. The two are
    consistent: the data bins lying wholly inside the background range are exactly those whose
    left-edge index is in [firstbindata, lastbindata), so the slice keeps all of them and no
    more.

    On both locked analyses this is a no-op. run_anaFit.py passes <channel>_rebinned/postfit and
    <channel>_rebinned/data, which come from the same rebinning call, so bins and bins_data are
    the same edges and the whole of data is returned.

    firstbindata is returned as well because _mask_window needs it to express the window in bin
    numbers rather than in observable values.
    """
    #crop data hist to bkg range
    firstbindata=0
    lastbindata=0

    for i,b in enumerate(bins_data):
        if b >= bins[0]:
            firstbindata = i
            break
    for i,b in enumerate(bins_data):
        if b <= bins[-1]:
            lastbindata = i

    data=data[firstbindata:lastbindata]

    return data, firstbindata

def _configure_hunter(bins):
    """Construct the BumpHunter instance with its fixed configuration.

    Every one of these changes the result, and tests/repro.py compares seed and npe exactly.
    nworker above 1 reorders the pseudo-experiments and moves global_Pval even at a fixed seed,
    which is why it is pinned at 1 rather than left to the machine.
    """
    # Create a BumpHunter1D class instance
    return BH.BumpHunter1D(
        width_min=2,
        width_max=3,
        width_step=1,
        scan_step=1,
        npe=10000,
        nworker=1,
        seed=666,
        bins=bins)

def _run_scan(hunter, data, bkg):
    """Run the scan, and report how long it took."""
    # Call the bump_scan method
    print("####bump_scan call####")
    begin = datetime.now()
    hunter.bump_scan(data, bkg, is_hist=True)
    end = datetime.now()
    print(f"time={end - begin}")
    print("")

def _mask_window(state, bins, firstbindata, usebinnumbers):
    """Turn the winning scan window into the two mask boundaries and the blind-range string.

    BlindRange is formatted with %d, which *truncates* rather than rounds. That string is what
    reaches the XML card, so the boundary the refit actually blinds is an integer even when the
    bin edge it came from is not.
    """
    if usebinnumbers:
        MaskMin = firstbindata+state["min_loc_ar"][0]
        MaskMax = firstbindata+state["min_loc_ar"][0]+state["min_width_ar"][0]
    else:
        MaskMin = bins[state["min_loc_ar"][0]]
        MaskMax = bins[state["min_loc_ar"][0]+state["min_width_ar"][0]]

    BlindRange = "%d,%d" % (MaskMin, MaskMax)

    return MaskMin, MaskMax, BlindRange

def _write_results(out_dict, outputjson):
    """Write the results as JSON, encoding numpy scalars and arrays on the way out."""
    with open(outputjson, 'w') as f:
        json.dump(out_dict, f, cls=NpEncoder)

def main(args):

    args = _build_parser().parse_args(args)

    bkg, bins, data, bins_data = _load_histograms(args.inputfile, args.bkghist, args.datahist)

    data, firstbindata = _crop_data_to_bkg_range(data, bins_data, bins)

    hunter = _configure_hunter(bins)

    _run_scan(hunter, data, bkg)

    # Print bump
    #hunter.print_bump_info()
    #hunter.print_bump_true(data, bkg, is_hist=True)
    hunter.bump_info(data,is_hist=True)

    # Get and save tomography plot
    # hunter.plot_tomography(data, is_hist=True, filename="tomography.png")

    # Get and save bump plot
    hunter.plot_bump(data, bkg, is_hist=True, filename="bump.png")

    # Get and save statistics plot
    hunter.plot_stat(show_Pval=True, filename="BH_statistics.png")

    state = hunter.save_state()

    out_dict = {}
    out_dict["pyBHresult"] = state

    out_dict["MaskMin"], out_dict["MaskMax"], out_dict["BlindRange"] = _mask_window(
        state, bins, firstbindata, args.usebinnumbers)

    _write_results(out_dict, args.outputjson)

    print(out_dict["BlindRange"])

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
