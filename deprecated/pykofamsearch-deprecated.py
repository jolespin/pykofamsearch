#!/usr/bin/env python
import sys, os, glob, gzip, warnings, argparse, pickle
from collections import defaultdict
from multiprocessing import cpu_count
from tqdm import tqdm
from pyhmmer.plan7 import HMMFile
from pyhmmer.easel import SequenceFile, TextSequence, Alphabet
from pyhmmer import hmmsearch

__program__ = os.path.split(sys.argv[0])[-1]
__version__ = "2024.4.9"

# Filter 
def filter_hmmsearch_threshold(
    hit, 
    threshold,
    score_type, 
    ):


    if score_type:
        if score_type == "domain":
            score = hit.best_domain.score
        else:
            score = hit.score
        if score >= threshold:
            evalue = hit.evalue
            return (threshold, score, evalue)
    # else:
    #     score = hit.score
    #     evalue = hit.evalue
    #     return ("", score, evalue)

def main(args=None):
    # Path info
    script_directory  =  os.path.dirname(os.path.abspath( __file__ ))
    script_filename = __program__
    # Path info
    description = """
    Running: {} v{} via Python v{} | {}""".format(__program__, __version__, sys.version.split(" ")[0], sys.executable)
    usage = "{} -i <proteins.fasta> -o <output.tsv> -d ".format(__program__)
    epilog = "Copyright 2023 Josh L. Espinoza (jol.espinoz@gmail.com)"

    # Parser
    parser = argparse.ArgumentParser(description=description, usage=usage, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    # Pipeline
    parser.add_argument("-i","--proteins", type=str, default="stdin", help = "path/to/proteins.fasta. [Default: stdin]")
    parser.add_argument("-o","--output", type=str, default="stdout", help = "path/to/output.tsv [Default: stdout]")
    parser.add_argument("-p","--n_jobs", type=int, default=1,  help = "Number of threads to use [Default: 1]")
    parser.add_argument("-e","--evalue", type=float, default=0.1,  help = "E-value threshold [Default: 0.1]")
    parser.add_argument("-d", "--database_directory", type=str, help="path/to/kofam_database_directory/ cannot be used with -s/-serialized_database")
    parser.add_argument("-r", "--serialized_database", type=str, help="path/to/database.pkl cannot be used with -d/--database_directory")
    # parser.add_argument("-b","--sequences_per_block", type=int, help = "Sequences per block.  If None is provided then all sequences are used at once [Default: None]")
    parser.add_argument("--no_header", action="store_true", help = "No header")
    # parser.add_argument("--stream", action="store_true", help = "Stream input protein sequences and do not load all sequences into memory. Much slower.")

    # Options
    opts = parser.parse_args()
    opts.script_directory  = script_directory
    opts.script_filename = script_filename

    # Threads
    if opts.n_jobs < 0:
        opts.n_jobs = cpu_count()

    # Database
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
                print("Must either provide -d/--database_directory, -s/--serialized_database or set `KOFAM_DATABASE` environment variable")
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

        if opts.missing_kos:
            with open(opts.missing_kos, "w") as f:
                for id_ko in sorted(missing_kos):
                    print(id_ko, file=f)



    # Output
    if opts.output == "stdout":
        f_output = sys.stdout 
    else:
        f_output = open(opts.output, "w")

    if not opts.no_header:
        print("id_protein", "id_ko", "threshold", "score", "e-value", "definition", file=f_output)

    # Input
    # if opts.stream:
    #     from Bio.SeqIO.FastaIO import SimpleFastaParser

    #     if opts.proteins == "stdin":
    #         f_input = sys.stdin
    #     else:
    #         if opts.proteins.endswith(".gz"):
    #             f_input = gzip.open(opts.proteins, "rt")
    #         else:
    #             f_input = open(opts.proteins, "r")

    #     for header, seq in tqdm(SimpleFastaParser(f_input), f"Parsing sequences from {f_input}"):
    #         id = header.split(" ")[0]
    #         digital_sequence = TextSequence(sequence=seq, name=id.encode()).digitize(Alphabet.amino())
    #         proteins = [digital_sequence]

    #         # Run HMMSearch  
    #         for hits in hmmsearch(name_to_hmm.values(), proteins, cpus=opts.n_jobs, E=opts.evalue):
    #             id_ko = hits.query_name.decode()
    #             data = ko_to_data[id_ko]
    #             threshold = data["threshold"]
    #             score_type = data["score_type"]
    #             definition = data["definition"]
    #             for hit in hits:
    #                 if hit.included:
    #                     result = filter_hmmsearch_threshold(hit, threshold, score_type)
    #                     if result:
    #                         threshold, score, evalue = result
    #                         print(
    #                             hit.name.decode(), 
    #                             id_ko, 
    #                             threshold, 
    #                             "{:0.3e}".format(score), 
    #                             "{:0.5e}".format(evalue), 
    #                             definition, 
    #                         sep="\t", 
    #                         file=f_output,
    #                         )
    #     f_input.close()

    # else:
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
    for hits in tqdm(hmmsearch(name_to_hmm.values(), proteins, cpus=opts.n_jobs, E=opts.evalue), desc="Performing HMMSearch", total=len(name_to_hmm)):
        id_ko = hits.query_name.decode()
        data = ko_to_data[id_ko]
        threshold = data["threshold"]
        score_type = data["score_type"]
        definition = data["definition"]
        for hit in hits:
            if hit.included:
                result = filter_hmmsearch_threshold(hit, threshold, score_type)
                if result:
                    threshold, score, evalue = result
                    print(
                        hit.name.decode(), 
                        id_ko, 
                        threshold, 
                        "{:0.3e}".format(score), 
                        "{:0.5e}".format(evalue), 
                        definition, 
                    sep="\t", 
                    file=f_output,
                    )


    if f_output != sys.stdout:
        f_output.close()

if __name__ == "__main__":
    main(sys.argv[1:])
