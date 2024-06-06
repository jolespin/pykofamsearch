#!/usr/bin/env python
import sys, os, argparse, gzip
from collections import defaultdict
from tqdm import tqdm
import pandas as pd


__program__ = os.path.split(sys.argv[0])[-1]
__version__ = "2024.6.6"

def main(args=None):
    # Path info
    script_directory  =  os.path.dirname(os.path.abspath( __file__ ))
    script_filename = __program__
    # Path info
    description = """
    Running: {} v{} via Python v{} | {}""".format(__program__, __version__, sys.version.split(" ")[0], sys.executable)
    usage = "{} -i <input.tsv> -o <output.tsv> -f <format> ".format(__program__)
    epilog = "Copyright 2024 New Atlantis Labs (jolespin@newatlantis.io)"

    # Parser
    parser = argparse.ArgumentParser(description=description, usage=usage, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    # Pipeline
    parser.add_argument("-i","--input", type=str, default="stdin", help = "path/to/input.tsv. The results of `pykofamsearch.py` must contain header [Default: stdin]")
    parser.add_argument("-k","--kegg_metadata", type=str, required=True, help = "path/to/kegg_metadata.tsv[.gz] containing `enzyme_commission` column")
    parser.add_argument("-o","--output", type=str, default="stdout", help = "path/to/output.tsv [Default: stdout]")
    parser.add_argument("-f", "--format", type=str, choices={"append", "slim"}, default="append", help="Output format [append: adds enzyme_commission column, trim: outputs [id_protein, id_ko, id_enzyme]] [Default: append]")
    # parser.add_argument("--no_header",action="store_true", help="Input does not have header")

    # Options
    opts = parser.parse_args()
    opts.script_directory  = script_directory
    opts.script_filename = script_filename

    # Output
    if opts.output == "stdout":
        opts.output = sys.stdout 

    # Input
    if opts.input == "stdin":
        opts.input = sys.stdin 
    
    df_meta_kegg = pd.read_csv(opts.kegg_metadata, sep="\t", index_col=0)
    ko_to_enzymes = dict()
    for id_ko, ecs in df_meta_kegg["enzyme_commission"].items():
        try:
            ecs = eval(ecs)
            ko_to_enzymes[id_ko] = ecs
        except TypeError:
            ko_to_enzymes[id_ko] = pd.NA

    df_pykofamsearch = pd.read_csv(opts.input, sep="\t", index_col=0)
    df_pykofamsearch["enzyme_commission"] = df_pykofamsearch["id_ko"].map(lambda x: ko_to_enzymes[x])

    if opts.format == "append":
        df_pykofamsearch.to_csv(opts.output, sep="\t")
    if opts.format == "slim":
        if opts.output != sys.stdout:
            if opts.output.endswith(".gz"):
                opts.output = gzip.open(opts.output, "wt")
            else:
                opts.output = open(opts.output, "w")
        for id_protein, (id_ko, ecs) in tqdm(df_pykofamsearch.loc[:,["id_ko", "enzyme_commission"]].iterrows(), desc="Processing enzymes"):
            if pd.notnull(ecs):
                for id_ec in ecs:
                    print(
                        id_protein,
                        id_ko,
                        id_ec,
                        sep="\t",
                        file=opts.output,
                    )
        if opts.output != sys.stdout:
            opts.output.close()



if __name__ == "__main__":
    main(sys.argv[1:])
