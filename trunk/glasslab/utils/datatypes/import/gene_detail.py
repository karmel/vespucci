'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import GeneDetail,\
    GenomeType, SequenceIdentifier
import sys

def import_file(file_path='',genome_name=''):
    genome_type = GenomeType.objects.get(genome_type=genome_name)
    
    data = DelimitedFileParser(file_path).get_array()
    for row in data:
        try:
            if row[0] == 'GeneID': continue
            if not row[2] and not row[3]: continue
            if not row[2] and row[3]: row[2] = row[3]
            try: seq = SequenceIdentifier.get_with_fallback(genome_type=genome_type, sequence_identifier=str(row[2]))
            except SequenceIdentifier.DoesNotExist:
                print 'Could not find sequence record for row: %s' % '\t'.join(row)
                continue
            
            record, created = GeneDetail.objects.get_or_create(sequence_identifier=seq,
                                                               unigene_identifier=str(row[1]),
                                                               ensembl_identifier=str(row[3]),
                                                               gene_name=str(row[4]),
                                                               gene_alias=str(row[5]),
                                                               gene_description=str(row[8]))
            record.refseq_gene_id=int(row[0])
            record.save()
            
        except: 
            print row
            pass
        
if __name__ == '__main__':
    genome_name = len(sys.argv) > 1 and sys.argv[1] or 'Mus musculus'
    file_name = len(sys.argv) > 2 and sys.argv[2] or 'mouse'
    import_file('/Volumes/Unknowme/homer/data/accession/%s.description' % file_name,genome_name)