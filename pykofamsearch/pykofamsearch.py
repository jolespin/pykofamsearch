#!/usr/bin/env python
import sys, os, glob, gzip, warnings, argparse, pickle
from collections import defaultdict
from multiprocessing import cpu_count
from tqdm import tqdm
from pyhmmer.plan7 import HMMFile
from pyhmmer.easel import SequenceFile, TextSequence, Alphabet
from pyhmmer import hmmsearch
# from . import __version__

# from pandas import notnull

__program__ = os.path.split(sys.argv[0])[-1]
__version__ = "2024.6.8"

# Filter 
def filter_hmmsearch_threshold(
    hit, 
    threshold:float,
    score_type:str, 
    return_failed_threshold:bool,
    ):
    # If there is no score_type value then there is no threshold or profile_type values

    if not return_failed_threshold:
        if score_type:
            if score_type == "domain":
                score = hit.best_domain.score
            else:
                score = hit.score
            if score >= threshold:
                evalue = hit.evalue
                return (threshold, score, evalue)
    else:
        score = hit.score
        if score_type:
            if score_type == "domain":
                score = hit.best_domain.score
        evalue = hit.evalue
        return (threshold, score, evalue)

def main(args=None):
    # Options
    # =======
    # Path info
    script_directory  =  os.path.dirname(os.path.abspath( __file__ ))
    script_filename = __program__
    description = """
    Running: {} v{} via Python v{} | {}""".format(__program__, __version__, sys.version.split(" ")[0], sys.executable)
    usage = "{} -i <proteins.fasta> -o <output.tsv> -d ".format(__program__)
    epilog = "Copyright 2024 New Atlantis Labs (jolespin@newatlantis.io)"

    # Parser
    parser = argparse.ArgumentParser(description=description, usage=usage, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)

    # Pipeline
    parser.add_argument("--verbosity", type=int, default=1, help="Verbosity of missing KOfams [Default: 1]")

    parser_io = parser.add_argument_group('I/O arguments')
    parser_io.add_argument("-i","--proteins", type=str, default="stdin", help = "path/to/proteins.fasta. stdin does not stream and loads everything into memory. [Default: stdin]")
    parser_io.add_argument("-o","--output", type=str, default="stdout", help = "path/to/output.tsv [Default: stdout]")
    parser_io.add_argument("--no_header", action="store_true", help = "No header")

    parser_utility = parser.add_argument_group('Utility arguments')
    parser_utility.add_argument("-p","--n_jobs", type=int, default=1,  help = "Number of threads to use [Default: 1]")
    # parser_utility.add_argument("--stream", action="store_true", help = "Stream input protein sequences and do not load all sequences into memory. Much slower and not recommended.")

    parser_hmmsearch = parser.add_argument_group('HMMSearch arguments')
    parser_hmmsearch.add_argument("-e","--evalue", type=float, default=0.1,  help = "E-value threshold [Default: 0.1]")
    parser_hmmsearch.add_argument("-a", "--all_hits", action="store_true", help="Return all hits and do not use curated threshold. Not recommended for large queries.")

    parser_database = parser.add_argument_group('Database arguments')
    parser_database.add_argument("-d", "--database_directory", type=str, help="path/to/kofam_database_directory/ cannot be used with -b/-serialized_database")
    parser_database.add_argument("-b", "--serialized_database", type=str, help="path/to/database.pkl cannot be used with -d/--database_directory")
    # parser_database.add_argument("-e", "--enzymes", action="store_true", help="Only use KOfam with Enzyme Commission identifiers")


    opts = parser.parse_args()
    opts.script_directory  = script_directory
    opts.script_filename = script_filename

    # Threads
    # =======
    cpus_available = cpu_count()
    if opts.n_jobs < 0:
        opts.n_jobs = cpus_available
    if opts.n_jobs > cpus_available:
        warnings.warn("--n_jobs {} but only {} cpus are available. Adjusting --n_jobs to {}".format(opts.n_jobs, cpus_available, cpus_available))
        opts.n_jobs = cpus_available

    # Database
    # ========
    if opts.serialized_database:
        print("Loading serialized KOFAM database", file=sys.stderr)
        # Load serialized database
        if opts.serialized_database.endswith((".gz", ".pgz")):
            f = gzip.open(opts.serialized_database, "rb")
        else:
            f = open(opts.serialized_database, "rb")
        ko_to_data, name_to_hmm = pickle.load(f)
        f.close()

    else:
        if not opts.database_directory:
            try:
                opts.database_directory = os.environ["KOFAM_DATABASE"]
            except KeyError:
                print("Must either provide -d/--database_directory, -b/--serialized_database or set `KOFAM_DATABASE` environment variable")
                sys.exit(1)

        # Load KOFAM thresholds
        ko_to_data = defaultdict(dict)
        with open(os.path.join(opts.database_directory, "ko_list"), "r") as f:
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
                
        # Load HMMs
        name_to_hmm = dict()
        missing_kos = set()
        for id_ko in tqdm(ko_to_data, desc="Loading HMMs", total=len(ko_to_data)):
            ko_filepath = os.path.join(opts.database_directory, "profiles", f"{id_ko}.hmm")
            try:
                with HMMFile(ko_filepath) as f:
                    for hmm in list(f):
                        name_to_hmm[hmm.name.decode()] = hmm
            except FileNotFoundError:
                missing_kos.add(id_ko)



    # Output
    # ======
    if opts.output == "stdout":
        f_output = sys.stdout 
    else:
        if opts.output.endswith(".gz"):
            f_output = gzip.open(opts.output, "wt")
        else:
            f_output = open(opts.output, "w")

    if not opts.no_header:
        print("id_protein", "id_ko", "threshold", "score", "e-value", "definition", sep="\t", file=f_output)
        
    # Input
    # =====
    if opts.proteins == "stdin":
        from Bio.SeqIO.FastaIO import SimpleFastaParser

        proteins = list()
        for header, seq in tqdm(SimpleFastaParser(sys.stdin), f"Parsing sequences from {sys.stdin}"):
            id = header.split(" ")[0]
            digital_sequence = TextSequence(sequence=seq, name=id.encode()).digitize(Alphabet.amino())
            proteins.append(digital_sequence)

    else:
        with SequenceFile(opts.proteins, format="fasta", digital=True) as f:
            proteins = f.read_block()#sequences=opts.sequences_per_block)

    # Run HMMSearch  
    # =============
    # Only hits that pass threshold
    if not opts.all_hits:
        for hits in tqdm(hmmsearch(name_to_hmm.values(), proteins, cpus=opts.n_jobs, E=opts.evalue), desc="Performing HMMSearch", total=len(name_to_hmm)):
            id_ko = hits.query_name.decode()
            data = ko_to_data[id_ko]
            threshold = data["threshold"]
            score_type = data["score_type"]
            definition = data["definition"]
            for hit in hits:
                if hit.included:
                    result = filter_hmmsearch_threshold(hit, threshold, score_type, return_failed_threshold=False)
                    if result:
                        threshold, score, evalue = result
                        print(
                            hit.name.decode(), 
                            id_ko, 
                            threshold, 
                            "{:0.3f}".format(score), 
                            "{:0.5e}".format(evalue), 
                            definition, 
                        sep="\t", 
                        file=f_output,
                        )

    # Consider all hits even those that do not pass threshold
    else:
        for hits in tqdm(hmmsearch(name_to_hmm.values(), proteins, cpus=opts.n_jobs, E=opts.evalue), desc="Performing HMMSearch", total=len(name_to_hmm)):
            id_ko = hits.query_name.decode()
            data = ko_to_data[id_ko]
            threshold = data["threshold"]
            score_type = data["score_type"]
            definition = data["definition"]
            for hit in hits:
                if hit.included:
                    result = filter_hmmsearch_threshold(hit, threshold, score_type, return_failed_threshold=True)
                    threshold, score, evalue = result
                    threshold = "" if threshold is None else threshold
                    print(
                        hit.name.decode(), 
                        id_ko, 
                        threshold, 
                        "{:0.3f}".format(score), 
                        "{:0.5e}".format(evalue), 
                        definition, 
                    sep="\t", 
                    file=f_output,
                    )

    # Output close
    if f_output != sys.stdout:
        f_output.close()
        
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
