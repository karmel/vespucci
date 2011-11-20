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
import sys
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.misc.inbredstrains.generate_genomes_from_reference import get_nucleotides_and_header

def main(strain='BALB'):
    ref_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37/'
    source_dir = '/Users/karmel/GlassLab/Data/Genomes/%s_MGSC37/' % strain
    
    strain_obj = InbredStrain.objects.get(name=strain)
    
    to_test = 100
    for chr in Chromosome.objects.exclude(name='chrM'):
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
                variant."reference", variant."start" 
                FROM "genetics"."inbred_strain_variation_%d" 
                INNER JOIN (
                    -- Limit to variants that are not next to others
                    SELECT var1.* FROM "genetics"."inbred_variant_%d" var1
                    LEFT OUTER JOIN "genetics"."inbred_variant_%d" var2
                    ON var1.start < var2.start
                    AND var1.start + 20 > var2.start
                    WHERE var2.id IS NULL) variant 
                ON ("genetics"."inbred_strain_variation_%d"."inbred_variant_id" = variant."id") 
                WHERE "genetics"."inbred_strain_variation_%d"."inbred_strain_id" = %d
                ORDER BY RANDOM()
                LIMIT %d''' % \
                    tuple([chr.id]*10 + [strain_obj.id] + [to_test]))
        
        for var in variants:
            index = var.start - 1
            
            # Get the region in the reference
            ref_region = ref_n[index:index + len(var.reference) + (20 - len(var.reference))]
            expected_match = ref_region.replace(var.reference, var.alternate, 1)
            
            # Look in same general area, but with a wide margin,
            # as indices get shifted every time we make a change
            found_match = nucleotides.find(expected_match, int(index*.95), int(index*1.05))
            if found_match > 0:
                matches += 1
            else: 
                print 'Found discrepancy for variation at position %d on %s: %s != %s.' \
                    % (var.start, chr.name, ref_region, expected_match)
                discrepancies += 1
        
        f.close()
    
        print 'Found %d matches and %d discrepancies in %s.' % (matches, discrepancies, chr.name)
    
        
        
if __name__=='__main__':
    if len(sys.argv) > 1: strain = sys.argv[1]
    else: strain = 'BALB'
    print 'Testing genome for %s.' % strain
    main(strain)