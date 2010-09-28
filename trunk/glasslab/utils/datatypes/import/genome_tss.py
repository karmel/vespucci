'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import TranscriptionStartSite,\
    SequenceAlias, Genome, SequenceIdentifier
import sys

def import_file(file_path='',genome_name=''):
    data = DelimitedFileParser(file_path).get_array()
    genome = Genome.objects.get(genome=genome_name)
    for row in data:
        try:
            seq = SequenceIdentifier.get_with_fallback(genome_type=genome.genome_type, sequence_identifier=str(row[0]))
            record, created = TranscriptionStartSite.objects.get_or_create(
                                                            genome=genome,
                                                            sequence_identifier=seq,
                                                            chromosome=str(row[1]),
                                                            start=int(row[2]),
                                                            end=int(row[3]),
                                                            direction=int(row[4]))
            
        except: 
            print row
            pass
        
if __name__ == '__main__':
    genome_name = sys.argv and sys.argv[1] or 'mm9'
    print genome_name
    import_file('/Volumes/Unknowme/homer/data/genomes/%s/%s.tss' % (genome_name,genome_name),genome_name)