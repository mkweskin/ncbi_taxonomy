##General use
This script will download the NCBI taxonomy and then report the taxonomy of a given list of taxonomy IDs.

The taxonomy database will be downloaded automatically from NCBI via FTP into a subfolder called "data".

The input file can be a list of taxonomy ID codes or a tab separated file (e.g. BLAST output in tabular format). For tab separated files, you can specify the column with the taxonomy IDs with the `--column` argument.

Currently the output is returned to stdout with the input original input line followed by the specified ranks separated by tabs.

Lines in the input file starting with # are output unmodified (e.g. BLAST output with comment lines)

You can choose what ranks to return with `--ranks`:

- all: All ranks
- linnean: only "superkingdom, kingdom, phylum, class, order, family, genus, species"
- named: If a rank has a formal name (i.e. excludes 'no rank')
- custom: A list of ranks to include. The ranks are based on what is included in the NCBI taxonomy database. Ranks are output in descending order regardless of order they are entered in here. The ranks should be enclosed in quotes (e.g. "family genus species") seperated by commas with no spaces (e.g. family,genus,species).

You can download a fresh copy of the taxonomy database with `--download`

Usage:

        usage: ncbi_taxonomy.py [-h] [-c COLUMN] [-r RANKS] [-d] FILE
        
        Looks up the Genbank taxon ID and returns rankings
        
        positional arguments:
          FILE                  input file with the taxon IDs.
          
        optional arguments:
          -h, --help            show this help message and exit
          -c COLUMN, --column COLUMN
                                the column in the input file with the taxon IDs
                                (default: 1)
          -r RANKS, --ranks RANKS
                                ranks to output. Options: all, linnean, named (for all
                                that are NOT 'no rank') or a list of ranks given in
                                quotes. Examples: -r all; -r "superkingdom order
                                genus"
          -d, --download        force a re-download of the current taxonomy database
                                (WILL OVERWRITE PREVIOUS VERSION)

##How to use NCBI BLAST with this
This is one example of how to blast a fasta file to produce a file compatible with this taxonomy script:

        blastn -remote -task megablast -db nt -evalue .001 -outfmt '7 qseqid sseqid pident length staxids salltitles ' -max_target_seqs 5 -query FILE.fasta >FILE.blast-out 2>/dev/null
        python ncbi_taxonomy.py -c 5 FILE.blast-out >FILE-with-taxonomy.out
