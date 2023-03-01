from pathlib import Path
import argparse

from Bio.SeqIO.FastaIO import SimpleFastaParser
from numpy import random


def get_default_fasta_dir():
    # Get ROOT path
    root_dir = Path(__file__).parents[1]

    # Package src dir
    src_dir = root_dir / "src"

    # Names based on config file
    with open(src_dir.joinpath("config.yaml"), "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
        
    # Genetic data dirs
    genetic_dir = root_dir.joinpath("data") / config["genetic"]["dir"]["main"]
    snp_dir = genetic_dir / config["genetic"]["dir"]["gbs_full"]
    snp_trim_dir = genetic_dir / config["genetic"]["dir"]["gbs_trimmed"]

    return config, snp_dir, snp_trim_dir

def indir_path(in_path):
    in_dir = Path(in_path)
    if in_dir.is_dir():
        return in_dir
    else:
        raise argparse.ArgumentTypeError(f"{in_dir} is not a valid path")
    
def outdir_path(out_path):
    out_dir = Path(out_path)
    # Create out_dir if needed
    if not out_dir.exists():
        out_dir.mkdir()
        return out_dir
    else:
        return out_dir
    
def get_seq_len(fasta_files, concat=False): 
    # Parse multiple single sequence fasta files
    if not concat:
        count_seq = len(fasta_files)
        
        length_seq = []
        for fasta_file in fasta_files:
            with open(fasta_file, "r") as f:
                for title, seq in SimpleFastaParser(f):
                    length_seq.append(len(seq))
        min_seq_length = min(length_seq)            
        return count_seq, min_seq_length
    
    # Parse a single multifasta
    else:
        if len(fasta_files) != 1:
            raise IOError(f"More than a single multi fasta file in the in_dir : {fasta_files}")
        count_seq = 0
        length_seq = []
        with open(fasta_files[0], "r") as f:
            for title, seq in SimpleFastaParser(f):
                count_seq += 1
                length_seq.append(len(seq))
            min_seq_length = min(length_seq)
        return count_seq, min_seq_length


def get_start_pos(startpos_percent, seq_length, trim_length):
    if startpos_percent is None:
        startpos = random.randint(0, (seq_length - trim_length))   # Stay inside array boundaries 
        return startpos
        
    else:
        startpos = round((startpos_percent / 100) * seq_length)
        # Determine length of sequence from startpos to end of sequence
        start_to_end_length = seq_length - startpos
        if trim_length > start_to_end_length:
            raise ValueError(
                f"Starting position of {startpos_percent}% too high for trimmed length of {trim_length}. Lower starting position"
            )
        return startpos
    
def concatenate_fasta_files(in_dir, fasta_files, out_dir, concat_filename):
    if len(fasta_files) < 2:
        raise ValueError(
            """
            Must have more at least more than 1 file to perform concatenation.
            If trying to perform fasta trimming from a single multi fasta file, use the --concat flag.
            """
        )
    else:
        if in_dir.is_dir():    # Second sanity check
            outdir_path = in_dir / out_dir
            outdir_path.mkdir(exist_ok=True)    # Create nested dir for concat
            concat_file = outdir_path / concat_filename
            concat_file.unlink(missing_ok=True)    # Proper overwrite
            with open(concat_file, "w") as cf:
                count_seq = 0
                for fasta_file in fasta_files:
                    with open(fasta_file, "r") as ff:
                        for title, seq in SimpleFastaParser(ff):
                            count_seq += 1
                            title = f">{title}\n"
                            cf.write(title)
                            # Newline every 60th
                            for i, nucleotide in enumerate(seq):
                                            if i % 60 == 0 and i > 0:
                                                cf.write(f"\n{nucleotide}")
                                            else:
                                                cf.write(nucleotide)
                        cf.write(f"\n")
            return count_seq
        else:
            raise NotADirectoryError

def trim_fasta(in_dir, fasta_files, startpos, trim_length, out_dir, out_concat_trim_fasta, from_concat):
    if not out_dir.exists():    # Second check for outdir
        out_dir.mkdir() 
    if not in_dir.is_dir():    # Third check for indir
        raise NotADirectoryError
        
    # From multiple single fasta files
    if not from_concat:
        count_seq = 0
        for fasta_file in fasta_files:    # Read from each then write to file
            if not fasta_file.is_file():
                raise FileNotFoundError
            with open(fasta_file, "r") as fasta_full:
                for title, seq in SimpleFastaParser(fasta_full):
                    count_seq += 1
                    title = f">{title}\n"
                    trimmed_seq = seq[startpos:startpos + trim_length]
                # Save to new dir/file with _trimmed tag
                out_trimmed = out_dir / f"{fasta_file.stem}_trimmed{trim_length}{fasta_file.suffix}"
                out_trimmed.unlink(missing_ok=True)
                with open(out_trimmed, "w") as ot:
                    ot.write(title)
                    # Newline every 60th
                    for i, nucleotide in enumerate(trimmed_seq):
                                    if i % 60 == 0 and i > 0:
                                        ot.write(f"\n{nucleotide}")
                                    else:
                                        ot.write(nucleotide)
        print(f"Finished trimming all {count_seq} fasta files and saved to {out_dir}/ directoy")
        
        # Create a concatenation of trimmed fasta files in seperate dir
        # out_dir_trimmed_concat = out_dir / "trimmed_concat"
        # out_dir_trimmed_concat.mkdir(exist_ok=True)
        trimmed_fastas = [file for file in out_dir.iterdir() if file.is_file() and ".fasta" in file.suffixes]
        concatenate_fasta_files(in_dir=out_dir, out_dir="trimmed_concat", fasta_files=trimmed_fastas, concat_filename="trimmed_fasta_concat.fasta")


    # From single multi fasta file
    else:
        if len(fasta_files) != 1:
            raise ValueError(f"Directory {in_dir} must contain only a single multifasta file")
        out_concat_trim_fasta = Path(out_concat_trim_fasta)
        out_concat_trimmed = out_dir / f"{out_concat_trim_fasta.stem}_trimmed{trim_length}{out_concat_trim_fasta.suffix}"
        (out_concat_trimmed).unlink(missing_ok=True)    # Proper overwrite
        with open(out_concat_trimmed, "w") as out_ctf:
            count_seq = 0
            for multi_fasta in fasta_files:
                if not multi_fasta.is_file():
                    raise FileNotFoundError
                with open(multi_fasta, "r") as mf:
                    for title, seq in SimpleFastaParser(mf):
                        count_seq += 1
                        title = f">{title}\n"
                        out_ctf.write(title)
                        trimmed_seq = seq[startpos:startpos + trim_length]
                        # Newline every 60th
                        for i, nucleotide in enumerate(trimmed_seq):
                                        if i % 60 == 0 and i > 0:
                                            out_ctf.write(f"\n{nucleotide}")
                                        else:
                                            out_ctf.write(nucleotide)
                        out_ctf.write(f"\n")
               
        print(f"Finished trimming all {count_seq} fasta sequences from and to a single file : {out_concat_trimmed}")

def _build_arg_parser(trim_default, out_default):

    parser = argparse.ArgumentParser(
    description = 
    """
    Takes multiple pre-aligned fasta files (or a single multifasta)
    and concatenates them in a single file.\n 
    Then trims all the sequences to a given length from either a random seed or a given start position.
    Also outputs a concatenated multi fasta of all trimmed files.

    Choose the length of the trim with the -l, --length flag.
    Choose the start position of the trim with -sp, --startpos flag.
    Use the --concat flag is starting from a single multi-fasta file.
    """,
    epilog = "Output can be used for tests in phylogenetic tree building with smaller sets for lower computing time"
    )

    parser.add_argument(
        "in_dir",
        # nargs=1,
        type=indir_path,
        help="Directory name that contains the fasta files"
    )

    parser.add_argument(
        "out_dir",
        nargs="?",
        type=outdir_path,
        default=out_default,
        help="Directory name that contains the trimmed fasta files"
    )

    parser.add_argument(
        "-l", "--length",
        nargs="?",
        type=int,
        default=trim_default,
        help="Length(int) of the sequence to trim. [Default = %(default)s]."
    )

    parser.add_argument(
        "-sp", "--startpos",
        nargs="?",
        metavar="N",
        type=int,
        choices=range(0,100),
        default=None,
        help="Start position from pth percentile of sequence instead of random. Choose from 0 to 99. [Default = %(default)s for random]"
    )

    parser.add_argument(
        "-c", "--concat",
        action="store_true",
        help="Add if input fasta is a single file that is already concatenated"
    )
    
    return parser

def main():
    # Construct the arguments object with defaults
    root_dir = Path(__file__).parent
    out_dir_default = root_dir / "trimmed_fasta"
    trim_default = 1000

    parser = _build_arg_parser(trim_default=trim_default, out_default=out_dir_default)
    args = parser.parse_args()


    # All SNP containing files in in_indir
    fasta_filepaths = [file for file in args.in_dir.iterdir() if file.is_file() and ".fasta" in file.suffixes]
    
    # Calculate minimal length of sequence(s) and validate single/multi IO
    count_seqs, min_seq_length = get_seq_len(fasta_filepaths, args.concat)
    print(f"Total of {count_seqs} sequence(s) with minimal sequence length of {min_seq_length:,} bp")

    # Trim_length pos-int + vs. seq_len checker
    if args.length <= 0:
        raise ValueError("Length of trimmed sequence must be greather than 0.")
    elif args.length > min_seq_length:
        raise ValueError(f"Trim length {args.length:,} bp is greather than smallest fasta length {min_seq_length:,}")
    
    # Get startpos for trimmed sequence
    start_pos = get_start_pos(
        startpos_percent=args.startpos, 
        seq_length=min_seq_length,
        trim_length=args.length
    )  
    end_pos = start_pos + args.length
    
    if args.startpos is None:
        print(f"Trimming {args.length:,} bp starting from a random position of {start_pos:,} bp up to {end_pos:,} bp...")
    else:
        print(f"Trimming {args.length:,} bp from the {args.startpos:,}th% of the full sequence ({start_pos:,} bp) up to {end_pos:,} bp...")

    # Concatenate files for multiple single fasta
    outfile_full_concat = "full_fasta_concat.fasta"
    if not args.concat:    # Create a single concat of full sequences when necessary
        num_concat = concatenate_fasta_files(
            in_dir=args.in_dir, 
            fasta_files=fasta_filepaths,
            out_dir="full_concat",
            concat_filename=outfile_full_concat
        )
        print(f"Concatenated {num_concat} fasta files to {args.in_dir} directory as full_fasta_concat.fasta")

    # Trim for both one multi fasta or multiple individual fasta files based on --concat
    outfile_trimmed_concat = "trimmed_fasta_concat.fasta"
    trim_fasta(
        in_dir=args.in_dir,
        fasta_files=fasta_filepaths,
        startpos=start_pos,
        trim_length=args.length,
        out_dir=args.out_dir,
        out_concat_trim_fasta=outfile_trimmed_concat,
        from_concat=args.concat
)
                        
if __name__ == "__main__":
    main()