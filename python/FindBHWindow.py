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

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--inputfile', dest='inputfile', type=str, required=True, help='Root file with bkg and data histograms')
    parser.add_argument('--datahist', dest='datahist', type=str, default='data', help='data hist name')
    parser.add_argument('--bkghist', dest='bkghist', type=str, default='postfit', help='bkg hist name')
    parser.add_argument('--outputjson', dest='outputjson', type=str, default='BHresults.json', help='Name of output file with BH results')
    parser.add_argument('--usebinnumbers', dest='usebinnumbers', action='store_true', help='Use bin numbers instead of observable for BlindRange')

    args = parser.parse_args(args)

    # Open the file
    with uproot.open(args.inputfile) as file:
        # Background
        bkg_th1 = file[args.bkghist]
        bkg, bins = bkg_th1.to_numpy()

        # Data
        data_th1 = file[args.datahist]
        data,bins_data = data_th1.to_numpy()

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

    # Create a BumpHunter1D class instance
    hunter = BH.BumpHunter1D(
        width_min=1,
        width_max=6,
        width_step=1,
        scan_step=1,
        npe=10000,
        nworker=1,
        seed=666,
        bins=bins)

    # Call the bump_scan method
    print("####bump_scan call####")
    begin = datetime.now()
    hunter.bump_scan(data, bkg, is_hist=True)
    end = datetime.now()
    print(f"time={end - begin}")
    print("")

    # Print bump
    hunter.print_bump_info()
    hunter.print_bump_true(data, bkg, is_hist=True)

    # Get and save tomography plot
    # hunter.plot_tomography(data, is_hist=True, filename="tomography.png")

    # Get and save bump plot
    bumpname=args.outputjson.replace(".json", "_bump.png")
    hunter.plot_bump(data, bkg, is_hist=True, filename=bumpname)

    # Get and save statistics plot
    statname=args.outputjson.replace(".json", "_statistics.png")
    hunter.plot_stat(show_Pval=True, filename=statname)

    state = hunter.save_state()

    out_dict = {}
    out_dict["pyBHresult"] = state

    if args.usebinnumbers:
        out_dict["MaskMin"] = firstbindata+state["min_loc_ar"][0]
        out_dict["MaskMax"] = firstbindata+state["min_loc_ar"][0]+state["min_width_ar"][0]
    else:
        out_dict["MaskMin"] = bins[state["min_loc_ar"][0]]
        out_dict["MaskMax"] = bins[state["min_loc_ar"][0]+state["min_width_ar"][0]]

    out_dict["BlindRange"] = "%d,%d" % (out_dict["MaskMin"], out_dict["MaskMax"])

    with open(args.outputjson, 'w') as f:
        json.dump(out_dict, f, cls=NpEncoder)

    print(len(out_dict["pyBHresult"]["res_ar"]))
    print(len(out_dict["pyBHresult"]["bins"]))
    print(out_dict["pyBHresult"]["res_ar"][0])
    print(out_dict["pyBHresult"]["res_ar"])

    print(out_dict["BlindRange"])

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
