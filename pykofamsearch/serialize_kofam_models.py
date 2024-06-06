#!/usr/bin/env python
import sys, os, glob, gzip, warnings, argparse, pickle
from collections import defaultdict
from tqdm import tqdm
from pyhmmer.plan7 import HMMFile

__program__ = os.path.split(sys.argv[0])[-1]
__version__ = "2024.6.6"

def main(args=None):
    # Options
    # =======
    # Path info
    script_directory  =  os.path.dirname(os.path.abspath( __file__ ))
    script_filename = __program__
    description = """
    Running: {} v{} via Python v{} | {}""".format(__program__, __version__, sys.version.split(" ")[0], sys.executable)
    usage = "{} -d <path/to/kofam_profiles_database_directory/> -k <path/to/ko_list> -b <kofam_hmm_database.pkl.gz> -f name ".format(__program__)
    epilog = "Copyright 2024 New Atlantis Labs (jolespin@newatlantis.io)"

    # Parser
    parser = argparse.ArgumentParser(description=description, usage=usage, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbosity", type=int, default=1, help="Verbosity of missing KOfams [Default: 1]")

    # Pipeline
    parser_database = parser.add_argument_group('Database arguments')
    parser_database.add_argument("-d", "--profiles", required=True,  type=str, help="path/to/kofam_profiles_database_directory/ .  [Command: `wget -v -c ftp://ftp.genome.jp/pub/db/kofam/profiles.tar.gz -O - |  tar -xz`]")
    parser_database.add_argument("-k", "--ko_list", required=True, type=str, help="path/to/ko_list[.gz] . [Command: wget -v -O - ftp://ftp.genome.jp/pub/db/kofam/ko_list.gz | gzip -d > ko_list]")
    parser_database.add_argument("-b", "--serialized_database", required=True, type=str, help="path/to/database.pkl[.gz] will be tuple where first item is threshold dictionary and second item is dictionary of HMM models")

    opts = parser.parse_args()
    opts.script_directory  = script_directory
    opts.script_filename = script_filename
    
    # Database
    # ========
    # Load KOFAM thresholds
    ko_to_data = defaultdict(dict)
    if opts.ko_list.endswith(".gz"):
        f = gzip.open(opts.ko_list, "rt")
    else:
        f = open(opts.ko_list, "r")
        
    header = next(f).strip().split("\t")[1:]
    for line in f:
        line = line.strip()
        if line:
            id_ko, *fields = line.split("\t")
            
            for i, v in enumerate(fields):
                id_field = header[i]
                try:
                    v = float(v)
                except ValueError:
                    v = v
                if v == "-":
                    v = None
                ko_to_data[id_ko][id_field] = v
    f.close()
                    
    # Load HMMs
    assert os.path.isdir(opts.profiles), "--profiles must be a directory of HMM files.  If you need to download, use the following command: `wget -v -c ftp://ftp.genome.jp/pub/db/kofam/profiles.tar.gz -O - |  tar -xz`"

    name_to_hmm = dict()
    missing_kos = set()
    for id_ko in tqdm(ko_to_data, desc="Loading KOfam HMMs", total=len(ko_to_data)):
        ko_filepath = os.path.join(opts.profiles, f"{id_ko}.hmm")
        try:
            with HMMFile(ko_filepath) as f:
                for hmm in list(f):
                    name = hmm.name
                    name = name.decode()
                    assert name == id_ko, "Filename {} does not match KOfam name {}".format(os.path.split(ko_filepath)[1], name)
                    name_to_hmm[id_ko] = hmm
        except FileNotFoundError:
            missing_kos.add(id_ko)
        
    # Output
    # ======
    # Write serialized database
    if opts.serialized_database.endswith((".gz", ".pgz")):
        f_out = gzip.open(opts.serialized_database, "wb")
    else:
        f_out = open(opts.serialized_database, "wb")
    pickle.dump((ko_to_data, name_to_hmm), f_out)
    f_out.close()
    
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

if __name__ == "__main__":
    main(sys.argv[1:])
