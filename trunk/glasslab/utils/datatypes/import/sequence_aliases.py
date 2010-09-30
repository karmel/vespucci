'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import SequenceAlias, SequenceIdentifier, GenomeType
from django.db import connection
import sys

def import_file(file_path='',genome_name=''):
    genome_type = GenomeType.objects.get(genome_type=genome_name)
            
    data = DelimitedFileParser(file_path).get_array()
    data = data[:532878]
    data = data[::-1]
    for row in data:
        try:
            # alias \t other id \t Unigene \t RefSeq \t Ensembl
            if not row[3].strip(): continue
            seq, created = SequenceIdentifier.objects.get_or_create(genome_type=genome_type,
                                                                    sequence_identifier=str(row[3]).strip())
            alias, created = SequenceAlias.objects.get_or_create(genome_type=genome_type,
                                                                alias=str(row[3]).strip(),
                                                                sequence_identifier=seq)
            if row[0].strip() != row[3].strip():
                alias, created = SequenceAlias.objects.get_or_create(genome_type=genome_type,
                                                                    alias=str(row[0]).strip(),
                                                                    sequence_identifier=seq)
            
            cursor = connection.cursor()
            cursor.close()
        except: 
            raise
        
if __name__ == '__main__':
    genome_name = len(sys.argv) > 1 and sys.argv[1] or 'Mus musculus'
    file_name = len(sys.argv) > 2 and sys.argv[2] or 'mouse'
    import_file('/Volumes/Unknowme/homer/data/accession/%s2gene.tsv' % file_name,genome_name)