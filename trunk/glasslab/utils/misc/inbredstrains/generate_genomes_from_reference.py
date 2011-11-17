'''
Created on Nov 16, 2011

@author: karmel

Using the released SNPs and Indels, we want to create modified versions of the reference genome 
for each mouse strain of interest. The problem: billions of basepairs to sort through. The good news
is, we only have to do this a few times, and don't anticipate running this process often, so less
than optimal efficiency is acceptable.

Note that we're starting with the C57BL6 reference genome, and then using the cleaned records
of SNPs and Indels from the Wellcome Trust (http://www.sanger.ac.uk/resources/mouse/genomes/). "Cleaned" here indicates 

    * C57BL6 matches reference
    * ATG score == 1 for SNPs (homozygous, Phred >= 40, sufficient coverage)
    * Lacking ATG score, indels are homozygous and Phred >= 40

Reference files are split by chromosome, meaning we can read the whole thing into memory,
assuming this is being run on the Mac server with 16gb of RAM. We will take advantage of that convenience,
even though it is not a reliable assumption for all machines.
'''
from __future__ import division
import os, re
from glasslab.utils.datatypes.genetics import InbredStrainVariation
from math import floor

def sort_by_chr(x):
    # Integers in order first, then X, Y.
    # Note that this doesn't work for M
    x = x.replace('chr','').replace('.fa','')
    try: return int(x)
    except ValueError: return ord(x)
    
def main():
    strain = 'BALB'
    
    source_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37/'
    files = [file for file in os.listdir(source_dir) if file[-3:] == '.fa']
    files.sort(key=sort_by_chr)

    output_dir = '/Users/karmel/GlassLab/Data/Genomes/%s_MGSC37/' % strain
    output_length = 70
    
    variants = InbredStrainVariation.objects.filter(inbred_strain__name=strain)
    for chr_id, file in files:
        source_file = os.path.join(source_dir, file)
        f = open(source_file)
        header = ''
        
        chr_vars = variants.filter(chromosome__id=chr_id)
        reconstructed = []
        current_count = 0 # Keep track of number of nucleotides we've gone through
        for row_num, line in enumerate(f):
            if f[:2] == '>':
                header = line
                continue
            
            row_length = len(line)
            start_search = current_count + 1
            end_search = current_count + row_length
            vars = chr_vars.order_by('inbred_variant__start').extra(
                        where='start_end && public.make_box(%d, 0, %d, 0)' % (start_search, end_search))
            
            recon_line = ''
            last_index = 0
            for var in chr_vars:
                # Get position relative to this line of nucleotides
                start = var.start - start_search
                # Add in chars thus far
                recon_line += line[last_index:start]
                # Add in variation segment
                recon_line += var.alternate
                # Skip to end of reference segment
                last_index = start + len(var.inbred_variant.reference)
                
            # Finally, add to end of line
            recon_line += line[last_index:]
            
            reconstructed.append(recon_line)
        
        full_length = ''.join(reconstructed)
        output_file = open(os.path.join(output_dir, file), 'w')
        
        output_file.write(header)
        for index in xrange(0,len(full_length),output_length):
            output_file.write(full_length[index:(index + output_length)])
            
        output_file.close()
        
                
