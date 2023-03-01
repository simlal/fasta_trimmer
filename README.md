# Fasta Trimmer
Trim fasta files (from single or multi-fasta) from a specific or random start position and a given trim length.

## Installation
Few depencies required with python > 3.7 so here are the simple installation steps:

`pip install biopython numpy`

## Usage
For help:

`python trim_fasta.py --help`

**Basic usage example**

To trim fasta files contained in `in_dir/` to `out_dir/` with a trim length of 2500 bp and starting position of 50% of the sequence length:

`python trim_fasta.py in_dir out_dir -l 2500 -sp 50`

This command will also create a concatened version (multifasta) for both full and trimmed files.

Note that you can also start from a multi fasta file with the `--concat` flag. However, there must be only 1 single file in the `in_dir` (see error handling). 