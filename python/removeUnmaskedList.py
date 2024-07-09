#!/bin/env python

from __future__ import print_function
import sys, argparse
import copy

#suffix to search:
suffix = "_masked"
#suffix to remove:
suffix_rm = ""

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options] INPUT')
    parser.add_argument('--keepUnmasked', dest='keepUnmasked', action='store_true', help='Remove masked results instead.')
    args, paths = parser.parse_known_args(args)

    for path in paths:
        print(path)
        with open(path, 'r') as f:
            lines = f.read().splitlines()

        lines_out=copy.deepcopy(lines)
            
        for l in lines:
            parts = l.split(".")
            #do this regardless of whether the file ends on .json, .root, ...
            extension = parts[-1]
            basename = ''.join(parts[:-1])
            if basename.endswith(suffix):
                if args.keepUnmasked:
                    lines_out.remove(l)
                else:
                    _l = l.replace(suffix, suffix_rm)
                    try:
                        lines_out.remove(_l)
                    except:
                        print("WARNING: '%s' not in input file" % _l)

        if args.keepUnmasked:
            outpath = path.replace(".txt", "_keepUnmasked.txt")
        else:
            outpath = path.replace(".txt", "_keepMasked.txt")

        with open(outpath, 'w') as f:
            f.writelines([line + '\n' for line in lines_out])

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
