'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import Genome, ChromosomeLocationAnnotation
from django.db import connection
import traceback
import sys

def import_file(file_path='',genome_name='', type=''):
    data = DelimitedFileParser(file_path).get_array()
    genome = Genome.objects.get(genome=genome_name)
    start = False
    for i,row in enumerate(data):
        try:
            if row[0] == 'exon (NM_013720, exon 8 of 24)': start = True
            if not start: continue
            record, created = ChromosomeLocationAnnotation.objects.get_or_create(
                                                            genome=genome,
                                                            chromosome=str(row[1]),
                                                            start=int(row[2]),
                                                            end=int(row[3]),
                                                            direction=int(row[4]),
                                                            type=type,
                                                            description=str(row[0]))
            cursor = connection.cursor()
            cursor.close()
        except: 
            print i,row
            raise
        
if __name__ == '__main__':
    genome_name = sys.argv and sys.argv[1] or 'mm9'
    for file_name, type in (('introns','Intron'),('exons','Exon'),
                            ('promoters','Promoter'),('cpgIsland','CpG Island'),
                            ('utr3',"3' UTR"),('utr5',"5' UTR")):
        import_file('/Volumes/Unknowme/homer/data/genomes/%s/annotations/basic/%s.ann.txt' % (genome_name,file_name),genome_name)