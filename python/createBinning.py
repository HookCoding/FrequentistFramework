import argparse


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", type=int, required=True, help="Start of bin range")
    parser.add_argument("-e", "--end", type=int, default=1000, help="End of bin range")
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="output file path and histogram name"
    )
    return parser.parse_args(argv)


def load_resolution_fit(input_path="Input/data/dijetisrTLA/resolutionFits.root"):
    # Deferred here, not top-level: parse_args()/resolve_bin_edges() are
    # ROOT-free (per doc/TIER3_COMPLETION_PLAN.md Chunk 13's own
    # decomposition table), and this repository's own pytest dev venv
    # cannot import ROOT at all - confirmed directly, matching every
    # other deferred-import module in this plan (run_fit.py,
    # run_provenance.py, run_templates.py).
    import ROOT

    # This "if not tfile" branch is currently unreachable in practice on
    # this repository's own installed PyROOT: ROOT.TFile.Open() itself
    # raises its own OSError (a different message than the one below) for
    # a missing/unopenable file before ever returning here - confirmed
    # directly. Preserved verbatim, not fixed or removed: it is
    # pre-existing behavior from the original single-scope script, moved
    # here unchanged, and it is not dead code in every PyROOT version -
    # some builds return a null TFile instead of raising, which is exactly
    # what this check guards against.
    tfile = ROOT.TFile.Open(input_path, "READ")
    if not tfile or tfile.IsZombie():
        raise OSError(f"Could not open {input_path}")
    reso_fit = tfile.Get("gsc_mjj_reso_fit")
    if not reso_fit:
        raise KeyError(f"ROOT object gsc_mjj_reso_fit not found in {input_path}")
    # Closing here rather than at the very end of the script (as the
    # original single-scope version did) is a verified-harmless reorder,
    # not a behavior change: a ROOT TF1 read back via TFile::Get() stays
    # evaluable after its owning file is closed - confirmed directly
    # (repeated .Eval() calls against a real fixture, both after the file
    # object merely fell out of scope and after an explicit .Close() call,
    # both still returned the correct value). Unlike python/plotPostFit.py's
    # TH1 objects (Chunk 10.B), a TF1 has no TDirectory-ownership lifetime
    # hazard here, so returning only the fit object (not the file too) is
    # safe.
    tfile.Close()
    return reso_fit


def resolve_bin_edges(reso_fit, rangelow, rangehigh):
    bin_edge = rangelow
    bin_edges = [rangelow]
    while bin_edge < rangehigh:
        resolution = reso_fit.Eval(bin_edge)
        up_edge = min(round(bin_edge + bin_edge * resolution), rangehigh)
        bin_edges.append(up_edge)
        bin_edge = up_edge
    return bin_edges


def build_binning_histogram(bin_edges):
    from array import array

    import ROOT

    edges = array("f", bin_edges)
    return ROOT.TH1F("mjjBinning", "", len(edges) - 1, edges)


def main(argv=None):
    import ROOT

    args = parse_args(argv)
    reso_fit = load_resolution_fit()
    bin_edges = resolve_bin_edges(reso_fit, args.start, args.end)
    outhist = build_binning_histogram(bin_edges)
    print("creating mjj resolution histogram ", args.output)
    outfile = ROOT.TFile.Open(args.output, "RECREATE")
    outfile.cd()
    outhist.Write()
    outfile.Close()


if __name__ == "__main__":
    main()
