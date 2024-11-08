#!/usr/bin/env python
import sys, os, glob, gzip, warnings, argparse, pickle, subprocess, tarfile, shutil
from datetime import datetime
from collections import defaultdict
from urllib.request import urlopen
from tqdm import tqdm
from pyhmmer.plan7 import HMMFile

__program__ = os.path.split(sys.argv[0])[-1]
__version__ = "2024.11.7"

def check_mode(opts):
    if opts.output_directory and opts.serialized_database:
        raise ValueError("Ambiguous mode: specify either --serialized_database for offline mode or --output_directory for online mode, but not both.")
    elif opts.output_directory:
        return 'online'
    elif opts.serialized_database:
        return 'offline'
    else:
        raise ValueError("Invalid mode: either specify --output_directory for online mode or --serialized_database for offline mode.")
    

def download_kofam_data_from_ftp(output_directory, ko_list_url, profiles_url):
    # Create directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Download and decompress ko_list.gz
    print(f"Downloading ko_list.gz from {ko_list_url}", file=sys.stderr)
    ko_list_path = os.path.join(output_directory, "ko_list")
    
    with (
        urlopen(ko_list_url) as response,
        gzip.open(response, 'rb') as gz_file,
        open(ko_list_path, 'wb') as out_file,
        ):
            shutil.copyfileobj(gz_file, out_file)
    print("ko_list successfully downloaded and decompressed", file=sys.stderr)

    # Download and extract profiles.tar.gz
    print(f"Downloading profiles.tar.gz from {profiles_url}", file=sys.stderr)

    # Extract profiles.tar.gz    
    with (
        urlopen(profiles_url) as response,
        tarfile.open(fileobj=response, mode='r:gz') as tar,
        ): 
            tar.extractall(path=output_directory)
    print("profiles.tar.gz successfully downloaded and extracted", file=sys.stderr)
    
def parse_enzyme_commission_from_definition(definition:str):
    enzymes = set()
    if "[EC:" in definition:
        fields = definition.split("[EC:")
        if not len(fields) == 2:
            raise ValueError("Invalid definition: {}".format(definition))
        enzymes_unformatted = fields[-1][:-1]
        if not "." in enzymes_unformatted:
            raise ValueError("Invalid enzyme commission: {}".format(enzymes_unformatted))
        enzymes = set(enzymes_unformatted.split(" "))
    return enzymes

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
    parser_offline = parser.add_argument_group('Offline arguments')
    parser_offline.add_argument("-b", "--serialized_database",  type=str, help="path/to/database.pkl[.gz] will be tuple where first item is threshold dictionary and second item is dictionary of HMM models. Cannot be used with -o/--output_directory")
    parser_offline.add_argument("-d", "--profiles",  type=str, help="path/to/kofam_profiles_database_directory/ .  [Command: `wget -v -c ftp://ftp.genome.jp/pub/db/kofam/profiles.tar.gz -O - |  tar -xz`]")
    parser_offline.add_argument("-k", "--ko_list",  type=str, help="path/to/ko_list[.gz] . [Command: wget -v -O - ftp://ftp.genome.jp/pub/db/kofam/ko_list.gz | gzip -d > ko_list]")

    parser_online = parser.add_argument_group('Online arguments')
    parser_online.add_argument("-o", "--output_directory",  type=str, help="path/to/output_directory/.  Cannot be used with -b/--serialized_database")
    parser_online.add_argument("--ko_list_url",  type=str, default="ftp://ftp.genome.jp/pub/db/kofam/ko_list.gz", help="FTP URL for ko_list [Default: ftp://ftp.genome.jp/pub/db/kofam/ko_list.gz]")
    parser_online.add_argument("--profiles_url",  type=str, default="ftp://ftp.genome.jp/pub/db/kofam/profiles.tar.gz", help="FTP URL for profiles.tar.gz [Default: ftp://ftp.genome.jp/pub/db/kofam/profiles.tar.gz]")

    opts = parser.parse_args()
    opts.script_directory  = script_directory
    opts.script_filename = script_filename
    
    # Mode
    mode = check_mode(opts)
    
    if mode == "online":
        database_version = "v{}".format(datetime.now().strftime("%Y.%m.%-d"))

        # Download KOFAM data
        # ===================
        download_kofam_data_from_ftp(
            output_directory=os.path.join(opts.output_directory, "kofam_data"),
            ko_list_url=opts.ko_list_url,
            profiles_url=opts.profiles_url
        )
        opts.ko_list = os.path.join(opts.output_directory, "kofam_data", "ko_list")
        opts.profiles = os.path.join(opts.output_directory, "kofam_data", "profiles")
        opts.serialized_database = os.path.join(opts.output_directory, "database.pkl.gz")
        with open(os.path.join(opts.output_directory, "database.version"), "w") as f:
            print(database_version, file=f)
            
        
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
    
    # Add enzyme commission
    for id_ko in ko_to_data:
        ko_to_data[id_ko]["enzyme_commission"] = parse_enzyme_commission_from_definition(ko_to_data[id_ko]["definition"])
    if mode == "online":
        from pandas import DataFrame
        df = DataFrame(ko_to_data).T
        df.index.name = "id_ko"
        df.to_csv(os.path.join(opts.output_directory, "kegg-ortholog_metadata.tsv"), sep="\t")
    # Load HMMs
    if not os.path.isdir(opts.profiles):
        raise ValueError("--profiles must be a directory of HMM files.  If you need to download, use the following command: `wget -v -c ftp://ftp.genome.jp/pub/db/kofam/profiles.tar.gz -O - |  tar -xz`")

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
    assert len(name_to_hmm), "No HMM files detected in {}.  Are you sure this is a profiles/ directory?".format(opts.profiles)
        
    # Output
    # ======
    # Write serialized database
    print(f"Writing serialized KOfams: {opts.serialized_database}", file=sys.stderr)
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
