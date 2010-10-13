'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import ChromosomeLocationAnnotationFactory,\
    IntergenicDescription
from django.db import connection
import traceback
import sys
import os
import re

def import_file(file_path='',genome_name='', type='', start=0):
    data = DelimitedFileParser(file_path).get_array()
    model = ChromosomeLocationAnnotationFactory.get_model(genome=genome_name)
    for i,row in enumerate(data[start:]):
        try:
            record, created = model.objects.get_or_create(
                                        chromosome=str(row[1]),
                                        start=int(row[2]),
                                        end=int(row[3]),
                                        direction=int(row[4]),
                                        type=type,
                                        description=str(row[0]))
            cursor = connection.cursor()
            cursor.close()
        except: 
            print start,i,row
            print traceback.format_exc()
            raise

def import_file_intergenic(file_path='',genome_name='', type='', start=0):
    data = DelimitedFileParser(file_path).get_array()
    model = ChromosomeLocationAnnotationFactory.get_intergenic(genome=genome_name)
    for i,row in enumerate(data[start:]):
        try:
            desc, created = IntergenicDescription.objects.get_or_create(description=re.sub('-HOMER\d+','',str(row[0])))
            record, created = model.objects.get_or_create(
                                        chromosome=str(row[1]),
                                        start=int(row[2]),
                                        end=int(row[3]),
                                        direction=int(row[4]),
                                        description=desc)
            if not created: 
                # We've been here before.
                break
            cursor = connection.cursor()
            cursor.close()
        except: 
            print start,i,row
            print traceback.format_exc()
            raise
        
if __name__ == '__main__':
    genome_name = len(sys.argv) > 1 and sys.argv[1] or 'mm9'
    start_type = len(sys.argv) > 2 and sys.argv[2] or None
    start_file = len(sys.argv) > 4 and sys.argv[4] or None
    start_type_hit = False
    
    if start_type == 'Intergenic':
        dir_name = '/Volumes/Unknowme/homer/data/genomes/%s/annotations/repeats' % genome_name
        for file_name in os.listdir(dir_name): 
            full_path = os.path.join(dir_name,file_name)
            if os.path.exists(full_path):
                start_index = 0
                if start_file:
                    if file_name==start_file: 
                        start_type_hit = True
                        start_index = len(sys.argv) > 3 and int(sys.argv[3]) or 0
                    if not start_type_hit: continue
                 
                import_file_intergenic(full_path,genome_name, start_type, start_index)
    else:
    
        for file_name, type in (('introns','Intron'),('exons','Exon'),
                                ('promoters','Promoter'),('cpgIsland','CpG Island'),
                                ('utr3',"3' UTR"),('utr5',"5' UTR")):
            start_index = 0
            if start_type:
                if type==start_type: 
                    start_type_hit = True
                    start_index = len(sys.argv) > 3 and int(sys.argv[3]) or 0
                if not start_type_hit: continue
                
        
            import_file('/Volumes/Unknowme/homer/data/genomes/%s/annotations/basic/%s.ann.txt' % (genome_name,file_name),
                        genome_name, type, start_index)