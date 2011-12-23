'''
Created on Nov 19, 2011

@author: karmel

We have generated derivative genomes from SNPs, but now should be able to spot-check 
to make sure it looks decent...
'''
from __future__ import division
import os
from glasslab.utils.datatypes.genetics import InbredStrainVariation,\
    InbredStrain
import sys, re
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.misc.inbredstrains.generate_genomes_from_reference import get_nucleotides_and_header

def main(strain='BALB'):
    ref_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37/'
    source_dir = '/Users/karmel/GlassLab/Data/Genomes/%s_MGSC37/' % strain
    
    strain_obj = InbredStrain.objects.get(name=strain)
    
    to_test = 100
    for chr in Chromosome.objects.filter(id__lt='22'):
        matches, discrepancies = 0,0
    
        # Get file data
        ref_file = os.path.join(ref_dir, chr.name + '.fa')
        source_file = os.path.join(source_dir, chr.name + '.fa')
        ref_f = open(ref_file)
        f = open(source_file)
        
        print 'Using source file %s.' % source_file
        ref_n, ref_header = get_nucleotides_and_header(ref_f)
        nucleotides, header = get_nucleotides_and_header(f)
        
        # Choose a set of random SNPs/indels
        variants = InbredStrainVariation.objects.raw('''
                SELECT "genetics"."inbred_strain_variation_%d"."id", 
                "genetics"."inbred_strain_variation_%d"."chromosome_id", 
                "genetics"."inbred_strain_variation_%d"."inbred_strain_id", 
                "genetics"."inbred_strain_variation_%d"."inbred_variant_id", 
                "genetics"."inbred_strain_variation_%d"."alternate", 
                "genetics"."inbred_strain_variation_%d"."strain_start", 
                "genetics"."inbred_strain_variation_%d"."strain_end", 
                variant."reference", variant."start" as ref_start
                FROM "genetics"."inbred_strain_variation_%d" 
                JOIN "genetics"."inbred_variant_%d" variant 
                ON ("genetics"."inbred_strain_variation_%d"."inbred_variant_id" = variant."id") 
                WHERE "genetics"."inbred_strain_variation_%d"."inbred_strain_id" = %d
                ORDER BY RANDOM()
                LIMIT %d ''' % \
                    tuple([chr.id]*11 + [strain_obj.id] + [to_test]))
        
        for var in variants:
            index = var.ref_start
            
            # Get the region in the reference
            ref_region = ref_n[index:index + len(var.reference)]
            expected_match = ref_region.replace(var.reference, var.alternate, 1)
            
            if expected_match == nucleotides[var.strain_start:var.strain_end + 1]:
                matches += 1
            else: 
                print 'Found discrepancy for variation at reference position %d on %s: found %s vs. expected %s.' \
                    % (var.ref_start, chr.name, nucleotides[var.strain_start:var.strain_end+1], expected_match)
                discrepancies += 1
        
        f.close()
    
        print 'Found %d matches and %d discrepancies in %s.' % (matches, discrepancies, chr.name)
    
        
        
if __name__=='__main__':
    if len(sys.argv) > 1: strain = sys.argv[1]
    else: strain = 'BALB'
    print 'Testing genome for %s.' % strain
    main(strain)