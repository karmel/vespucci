'''
Created on Nov 16, 2011

@author: karmel

We want to update each SNP/Indel with its location within the genome 
of the target strain, rather than just the reference. We track through
the generated genome of the strain in order to get updated coordinates.
'''
from __future__ import division
import os
from glasslab.utils.datatypes.genetics import InbredStrainVariation,\
    InbredStrain
import sys
from glasslab.utils.database import execute_query
from glasslab.utils.misc.inbredstrains.generate_genomes_from_reference import get_nucleotides_and_header,\
    sort_by_chr

    
def main(strain='BALB'):
    source_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37/'
    files = [file for file in os.listdir(source_dir) if file[-3:] == '.fa']
    files.sort(key=sort_by_chr)

    strain_obj = InbredStrain.objects.get(name=strain)
    
    for file_id, file in enumerate(files):
        chr_id = file_id + 1 # Files are sorted, but we don't want chromosomes zero-indexed
        #if chr_id < 10: continue
        
        source_file = os.path.join(source_dir, file)
        print 'Using source file %s.' % source_file
        f = open(source_file)
        nucleotides, header = get_nucleotides_and_header(f)
        
        variants = InbredStrainVariation.objects.raw('''
            SELECT "genetics"."inbred_strain_variation_%d"."id", 
            "genetics"."inbred_strain_variation_%d"."chromosome_id", 
            "genetics"."inbred_strain_variation_%d"."inbred_strain_id", 
            "genetics"."inbred_strain_variation_%d"."inbred_variant_id", 
            "genetics"."inbred_strain_variation_%d"."alternate", 
            "genetics"."inbred_variant_%d"."reference", 
            "genetics"."inbred_variant_%d"."start" as ref_start
            FROM "genetics"."inbred_strain_variation_%d" 
            INNER JOIN "genetics"."inbred_variant_%d" 
            ON ("genetics"."inbred_strain_variation_%d"."inbred_variant_id" = "genetics"."inbred_variant_%d"."id") 
            WHERE "genetics"."inbred_strain_variation_%d"."inbred_strain_id" = %d
            --AND "genetics"."inbred_strain_variation_%d".strain_start IS NULL
            ORDER BY "genetics"."inbred_variant_%d"."start" ASC''' % \
                tuple([chr_id]*12 + [strain_obj.id] + [chr_id, chr_id]))
        
        
        last_index = 0
        # We want to keep a record of what the position in the new genome is
        # so that we can update the variants accordingly. 
        new_position = 0
        query_string = ''
        for i,var in enumerate(list(variants)):
            start = var.ref_start

            if start < last_index:
                # This shouldn't happen in theory, but does in a rare set of cases
                # where the indels happen to overlap in the original vcf files.
                # For example:
                # chr    pos            ref                                alt
                # 1    13571830    .    ACAGATCCTCAGGATGAAGGGCGGCCTACCCT    A    
                # 1    13571861    .    T                                    TA    
                # In the above case, the T of the latter indel is the same as the last T in the 
                # first indel... really it should be one indel that goes from the reference to ATA.
                # We want ATA, though, so we will "rewind" last_index to align with the
                # overlapping start.
                last_index = start
                
            # Sanity check
            if nucleotides[start:start + len(var.reference)] != var.reference:
                raise Exception('ERROR: Reference does not match expected. Expected: %s vs. found: %s.\nContext: %s' \
                                % (var.reference, nucleotides[start:start + len(var.reference)],
                                   nucleotides[start-20:start + len(var.reference) + 20]))
                
            
            # Update variant record with position in the new genome
            new_start = new_position + (start - last_index)
            new_end = new_start + len(var.alternate) - 1 # Subtract 1 because end is inclusive
            
            # Run query manually for the sake of speed.
            query_string += '''UPDATE "%s_%d" 
                set "strain_start" = %d,
                    "strain_end" = %d, 
                    "strain_start_end" = public.make_box(%d, 0, %d, 0)
                    WHERE id = %d;
                    ''' % (InbredStrainVariation._meta.db_table,
                          chr_id, new_start, new_end,
                          new_start, new_end, var.id)
                    
            
            # Skip to end of reference segment
            last_index = start + len(var.reference)
            new_position = new_start + len(var.alternate)
            
            # Batch so that we don't have to hit the DB so many times
            if i % 1000 == 0:  
                execute_query(query_string)
                query_string = ''
                print "Processed variant %d with position %d." % (i, start)
        
        # Get the last batch
        if query_string:
            execute_query(query_string)
            query_string = ''
            print "Processed variant %d with position %d." % (i, start)
        
if __name__=='__main__':
    if len(sys.argv) > 1: strain = sys.argv[1]
    else: strain = 'BALB'
    print 'Updating genomic coordinates for variants for %s.' % strain
    main(strain)
        
                
