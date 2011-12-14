'''
Created on Nov 19, 2011

@author: karmel

Test to make sure the motif mappings are accurate.

Note that we don't try to match motifs to the reference when there
are variants inside that motif.

Alos, note that Homer is called by this script, and it does
not run more than instance well due to the way in which
Homer creates and removes temp files.
'''
from __future__ import division
import os
import sys
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.misc.inbredstrains.generate_genomes_from_reference import get_nucleotides_and_header
from glasslab.utils.datatypes.motif import BindingSite, Motif
import subprocess

def main(strain='BALB'):
    motif_db_table = Motif._meta.db_table
    binding_site_db_table = BindingSite._meta.db_table
    Motif._meta.db_table = Motif._meta.db_table.replace('homer_motifs','homer_motifs_%s' % strain.lower()) 
    BindingSite._meta.db_table = BindingSite._meta.db_table.replace('homer_motifs','homer_motifs_%s' % strain.lower())
    
    ref_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37/'
    source_dir = '/Users/karmel/GlassLab/Data/Genomes/%s_MGSC37/' % strain
    motif_dir = '/Users/karmel/GlassLab/Notes and Reports/Inbred strains/Motifs/'
    motif_file = os.path.join(motif_dir, 'union_h3k4me2_peaks.motif')
    
    to_test = 100
    for chr in Chromosome.objects.filter(id__lt='22'):
        matches, discrepancies = 0,0
    
        # Get file data
        ref_file = os.path.join(ref_dir, chr.name + '.fa')
        source_file = os.path.join(source_dir, chr.name + '.fa')
        ref_f = open(ref_file)
        f = open(source_file)
        
        tmp_file = os.path.join(motif_dir, '%s_test_motifs_%d.fa' % (strain, chr.id))
        
        print 'Using source file %s.' % source_file
        ref_n, header = get_nucleotides_and_header(ref_f)
        nucleotides, header = get_nucleotides_and_header(f)
        
        # Choose a set of random SNPs/indels
        sites = BindingSite.objects.raw('''
                SELECT site."id", 
                site."chromosome_id", 
                site."motif_id", 
                site."start", 
                site."end", 
                site."strain_start", 
                site."strain_end", 
                site."strain_start_end",
                motif.description
                FROM "%s_%d" site 
                JOIN "%s" motif
                on site.motif_id = motif.id
                ORDER BY RANDOM()
                LIMIT %d''' % \
                    (BindingSite._meta.db_table, chr.id, 
                     Motif._meta.db_table, to_test))
        
        
        for site in sites:
            # Get start of motif, plus one extra char so that Homer recognizes it. 
            ref_region = ref_n[site.start:site.end+2]
            region = nucleotides[site.strain_start:site.strain_end+2]
            
            # Wrte to temp file for Homer input
            tmp_fa = open(tmp_file, 'w')
            tmp_fa.write('> Test_%d\n' % site.id)
            tmp_fa.write(ref_region +'\n')
            tmp_fa.write(region)
            tmp_fa.close()
            
            command = '/Applications/bioinformatics/homer/bin/homer2 find -i "%s" -m "%s"' % (tmp_file, motif_file)
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = proc.stdout.read()
            
            if ref_region == region:
                expect_to_find = 2 # SNP inside motif
            else: expect_to_find = 1
            
            if output.count('\t%s\t' % region[:-1]) < expect_to_find \
                or output.count(site.description) < expect_to_find:
                    print 'Could not find expected motif at %d on %s.\nExpected: %s: %s\nFound:\n%s.' \
                        % (site.start, chr.name, site.description, region[:-1], output)
                    discrepancies += 1
            else:
                matches += 1
                
        os.remove(tmp_file)
        f.close()
    
        print 'Found %d matches and %d discrepancies in %s.' % (matches, discrepancies, chr.name)
    Motif._meta.db_table = motif_db_table
    BindingSite._meta.db_table = binding_site_db_table
        
        
if __name__=='__main__':
    if len(sys.argv) > 1: strain = sys.argv[1]
    else: strain = 'DBA'
    print 'Testing motif locations for %s.' % strain
    main(strain)