#!/usr/bin/env python
import sys, os, glob, gzip, warnings, argparse, pickle
from collections import defaultdict
from tqdm import tqdm
from pyhmmer.plan7 import HMMFile

__program__ = os.path.split(sys.argv[0])[-1]
__version__ = "2024.9.24"

def main(args=None):
    # Options
    # =======
    # Path info
    script_directory  =  os.path.dirname(os.path.abspath( __file__ ))
    script_filename = __program__
    description = """
    Running: {} v{} via Python v{} | {}""".format(__program__, __version__, sys.version.split(" ")[0], sys.executable)
    usage = "{} -i <path/to/identifiers.list> -b <kofam_hmm_database.pkl.gz> -s <subset_kofam_hmm_database.pkl.gz>".format(__program__)
    epilog = "Copyright 2024 New Atlantis Labs (jolespin@newatlantis.io)"

    # Parser
    parser = argparse.ArgumentParser(description=description, usage=usage, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", type=int, default=1, help="Verbosity of missing KOfams [Default: 1]")

    # Pipeline
    parser_database = parser.add_argument_group('Database arguments')
    parser_database.add_argument("-i", "--identifiers", default="stdin", type=str, help="path/to/identifiers.list where HMM identifiers are on a separate line")
    parser_database.add_argument("-b", "--serialized_database", required=True, type=str, help="path/to/database.pkl[.gz] will be tuple where first item is threshold dictionary and second item is dictionary of HMM models")
    parser_database.add_argument("-s", "--subset_serialized_database", required=True, type=str, help="path/to/subset-database.pkl[.gz] will be tuple where first item is threshold dictionary and second item is dictionary of HMM models")

    opts = parser.parse_args()
    opts.script_directory  = script_directory
    opts.script_filename = script_filename
    
    # Identifiers
    # ===========
    if opts.identifiers == "stdin":
        f_identifiers = sys.stdin
    else:
        if opts.identifiers.endswith(".gz"):
            f_identifiers = gzip.open(opts.identifiers, "rt")
        else:
            f_identifiers = open(opts.identifiers, "r")
            
    identifiers = set()
    for line in f_identifiers:
        id_ko = line.strip()
        if id_ko:
            identifiers.add(id_ko)
            
    # Database
    # ========
    
    # ======
    # Read serialized database
    if opts.serialized_database.endswith((".gz", ".pgz")):
        f_database = gzip.open(opts.serialized_database, "rb")
    else:
        f_database = open(opts.serialized_database, "rb")
    ko_to_data, name_to_hmm = pickle.load(f_database)
    
    ko_to_data__subset = dict()
    name_to_hmm__subset = dict()
    missing_kos = set()
    for id_ko in identifiers:
        try:
            ko_to_data__subset[id_ko] = ko_to_data[id_ko]
            name_to_hmm__subset[id_ko] = name_to_hmm[id_ko]
        except KeyError:
            missing_kos.add(id_ko)

    # Verbosity
    # =========
    if opts.verbosity == -1:
        opts.verbosity = 123456789
    if opts.verbosity > 0:
        print("------------------------", file=sys.stderr)
        print("Number of missing KOfams: {}".format(len(missing_kos)), file=sys.stderr)
        print("------------------------", file=sys.stderr)

        if opts.verbosity > 1:
            if len(missing_kos):
                for id_ko in missing_kos:
                    print(f"Missing KOfam: {id_ko}", file=sys.stderr)
                    
                    
    # Output
    # ======
    if any([
        len(ko_to_data__subset) == 0,
        len(name_to_hmm__subset) == 0,
        ]):
        raise KeyError("No identifiers from were in serialized database")
        
    # Write serialized database
    if opts.subset_serialized_database.endswith((".gz", ".pgz")):
        f_out = gzip.open(opts.subset_serialized_database, "wb")
    else:
        f_out = open(opts.subset_serialized_database, "wb")
    pickle.dump((ko_to_data__subset, name_to_hmm__subset), f_out)
    f_out.close()

if __name__ == "__main__":
    main(sys.argv[1:])
