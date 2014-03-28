'''
Looks up taxonomic information from NCBI's taxonomy database given a taxon id list.

Will download the taxonomy id database dump files from NCBI to a folder called
data in the current working directory.

This is a modified version of ncbi_taxonomy by Ben Morris (https://github.com/bendmorris/ncbi_taxonomy)


'''

import urllib2
import os
import tarfile
import sys
import argparse
import re

col_delimiter = '\t|\t'
row_delimiter = '\t|\n'
url = 'ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz'
tree_filename = 'ncbi_taxonomy.newick'
data_dir = 'data/'
linnean=["superkingdom", "kingdom", "phylum", "class", "order", "family", "genus", "species"]

def readargs():
    '''
    Read in program arguments
    '''

    parser = argparse.ArgumentParser(description="Looks up the Genbank taxon ID and returns rankings")
    parser.add_argument("FILE", help="input file with the taxon IDs.", type=str)
    parser.add_argument("-c", "--column", help="the column in the input file with the taxon IDs (default: 1)", default=1, type=int)
    parser.add_argument("-r", "--ranks", help="ranks to output. Options: all, linnean, named (for all that are NOT \'no rank\') or a list of ranks given in quotes.  Examples: -r all; -r \"superkingdom order genus\" ", default="linnean", type=str)
    parser.add_argument("-d", "--download", help="force a re-download of the current taxonomy database (WILL OVERWRITE PREVIOUS VERSION)", action="store_true")
    
    args = parser.parse_args()
    if args.ranks == "linnean":
        args.ranks = "superkingdom kingdom phylum class order family genus species"
    args.ranks = re.split('[\s,]+',args.ranks) #split rank list on commas or spaces
    args.ranks = [x.lower() for x in args.ranks] #convert to lowercase- all ranks in the taxanomy db are lowercase
    
    
    return args

def downloadtax():
    '''
    Download and extract ncbi taxonomy database dump
    from ncbi_taxonomy by Ben Morris (https://github.com/bendmorris/ncbi_taxonomy)
    '''
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    
    #Delete old versions if they're present
    if os.path.isfile(data_dir+"nodes.dmp"): os.remove(data_dir+"nodes.dmp")
    if os.path.isfile(data_dir+"names.dmp"): os.remove(data_dir+"names.dmp")
    if os.path.isfile(data_dir+"taxdump.tar.gz"): os.remove(data_dir+"taxdump.tar.gz")
    
    
    # download the taxonomy archive
    filename = os.path.join(data_dir, url.split('/')[-1])
    sys.stderr.write('Downloading %s...\n' % filename)
    r = urllib2.urlopen(urllib2.Request(url))
    assert r.geturl() == url
    with open(filename, 'wb') as output_file:
        output_file.write(r.read())
    r.close()

    # extract the text dump
    for extract in ('nodes.dmp', 'names.dmp'):
        sys.stderr.write('Extracting %s from %s...\n' % (extract, filename))
        archive = tarfile.open(name=filename, mode='r:gz')
        archive.extract(extract, path=data_dir)
        archive.close()

def readintaxa (taxa):
    '''
    from ncbi_taxonomy by Ben Morris (https://github.com/bendmorris/ncbi_taxonomy)
    '''
    # get names for all tax_ids from names.dmp
    sys.stderr.write('Reading names...\n')
    with open(os.path.join(data_dir, 'names.dmp')) as names_file:
        for line in names_file:
            line = line.rstrip(row_delimiter)
            values = line.split(col_delimiter)
            tax_id, name_txt, _, name_type = values[:4]
            if name_type == 'scientific name':
                taxa[tax_id] = {}
                taxa[tax_id]['name'] = name_txt

    # read all node info from nodes.dmp
    sys.stderr.write('Reading taxonomy...\n')
    with open(os.path.join(data_dir, 'nodes.dmp')) as nodes_file:
        for line in nodes_file:
            line = line.rstrip(row_delimiter)
            values = line.split(col_delimiter)
            tax_id, parent_id, rank = values[:3]
            taxa[tax_id]['parent'] = parent_id
            taxa[tax_id]['rank'] = rank

def lookuptaxa(taxa, tax_id, rankings):
    '''
    Print name of tax_id and then get information on parent
    '''
    if tax_id in taxa:

        rankings.append({'rank':taxa[tax_id]['rank'], 'value':taxa[tax_id]['name']}) 

        #lookup info of parent unless at root
        if taxa[tax_id]['parent'] != tax_id:
            lookuptaxa(taxa, taxa[tax_id]['parent'], rankings)

def printranking(rankings, ranksToPrint):
    '''
    Print the generated ranking for the ranks selected
    '''
    for ranking in rankings:
        if "all" in ranksToPrint or ranking['rank'] in ranksToPrint or ("named" in ranksToPrint and ranking['rank'] != "no rank"):
            print "\t", ranking['value'],


def main():

    args = readargs()
    #print args
    
    taxonomyread = False
    
    #Parse input (filename given at program execution)
    endl = os.linesep
    linecount = 0
    with open(args.FILE, 'r') as f:
        for line in f:
            linecount += 1
            if not line.strip().startswith("#"):  #Ignore lines that start with #
                values = line.strip(endl).split("\t")
                if len(values) < args.column:
                    sys.exit("ERROR: You said to look in column "+str(args.column)+" for taxon IDs, but line "+str(linecount)+" doesn\'t have that many columns, it has "+str(len(values)))
                taxid = values[args.column-1].strip()
                
                #If a blast result has >1 taxon associated with it, BLAST returns a semicolon seperated list of taxon IDs. The script will use the first and give a warning
                if len(taxid.split(";")) > 1:
                    sys.stderr.write("WARNING: '"+str(taxid)+"' appears to contain >1 Taxon ID speperated by \';\', using the first\n")
                    taxid = taxid.split(";")[0]
                    taxid.strip()
                
                #Download and read taxonomy
                if not taxonomyread:
                    #Check that the input file exists before reading taxonomy (or exit)
                    if not os.path.isfile(args.FILE): sys.exit("ERROR: File \""+args.FILE+"\" does not exist")
    
                    #Download the taxonomy files if they're not present or user has chosen to re-download
                    if not os.path.isfile(data_dir+"names.dmp") or not os.path.isfile(data_dir+"nodes.dmp") or args.download: downloadtax()
                    taxa = {}
                    readintaxa(taxa)
                
                if taxid in taxa:
                    rankings=[]
                    lookuptaxa(taxa,taxid,rankings)
                    rankings.reverse()
                    print line.strip(endl),
                    printranking(rankings, args.ranks)
                    print
                else:
                    sys.stderr.write("Taxa ID '"+str(taxid)+"' not found\n")
                    print line.strip(endl)  #If Taxa ID isn't found, still output the original line
            else:
                print line.strip(endl)

if __name__ == '__main__':
    main()
