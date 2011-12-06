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
import os
from glasslab.utils.datatypes.genetics import InbredStrainVariation,\
    InbredStrain
import sys
from glasslab.utils.database import execute_query

def sort_by_chr(x):
    # Integers in order first, then X, Y.
    # Note that this doesn't work for M
    x = x.replace('chr','').replace('.fa','')
    try: return int(x)
    except ValueError: return ord(x)
    
def get_nucleotides_and_header(f):
    whole_text = f.read()
    header_end = whole_text.find('\n') + 1
    header = whole_text[:header_end]
    nucleotides = whole_text[header_end:]
    nucleotides = nucleotides.replace('\n','')
    return nucleotides, header
    
def main(strain='BALB'):
    source_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37/'
    files = [file for file in os.listdir(source_dir) if file[-3:] == '.fa']
    files.sort(key=sort_by_chr)

    output_dir = '/Users/karmel/GlassLab/Data/Genomes/%s_MGSC37/' % strain
    output_length = 70
    
    strain_obj = InbredStrain.objects.get(name=strain)
    
    for file_id, file in enumerate(files):
        chr_id = file_id + 1 # Files are sorted, but we don't want chromosomes zero-indexed
        
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
            ORDER BY "genetics"."inbred_variant_%d"."start" ASC''' % \
                tuple([chr_id]*12 + [strain_obj.id] + [chr_id]))
        
        tmp_dest_file = os.path.join(output_dir, 'tmp_' + file)
        print 'Using temp destination file %s.' % tmp_dest_file
        #tmp_output_file = open(tmp_dest_file, 'w')
        #output_file.write(header.replace('C57BL/6J', strain_obj.long_name) + '\n')
        
        last_index = 0
        # We want to keep a record of what the position in the new genome is
        # so that we can update the variants accordingly. 
        new_position = 0
        for i,var in enumerate(list(variants)):
            start = var.ref_start

            # Sanity check
            if nucleotides[start:start + len(var.reference)] != var.reference:
                raise Exception('ERROR: Reference does not match expected. Expected: %s vs. found: %s.\nContext: %s' \
                                % (var.reference, nucleotides[start:start + len(var.reference)],
                                   nucleotides[start-20:start + len(var.reference) + 20]))
                
            # Add in chars thus far
            #tmp_output_file.write(nucleotides[last_index:start])            
            
            # Add in variation segment
            #tmp_output_file.write(var.alternate)
            
            # Update variant record with position in the new genome
            new_start = new_position + (start - last_index)
            new_end = new_start + len(var.alternate) - 1 # Subtract 1 because end is inclusive
            
            # Run query manually for the sake of speed.
            execute_query('''UPDATE "%s_%d" 
                set "start" = %d,
                    "end" = %d, 
                    "start_end" = public.make_box(%d, 0, %d, 0)
                    WHERE id = %d;''' % (InbredStrainVariation._meta.db_table,
                                         chr_id, new_start, new_end,
                                         new_start, new_end, var.id)
                    )
            
            # Skip to end of reference segment
            last_index = start + len(var.reference)
            new_position = new_start + len(var.alternate)
            
            if i%10000==0: print "Processed variant %d with position %d." % (i, start)
        '''
        # Last bit
        tmp_output_file.write(nucleotides[last_index:])
        tmp_output_file.close()
        
        # Now just create as fixed-width file
        dest_file = os.path.join(output_dir, file)
        print 'Using destination file %s.' % dest_file
        output_file = open(dest_file, 'w')
        tmp_output_file = open(tmp_dest_file)
        
        output_file.write(header.replace('C57BL/6J', strain_obj.long_name))
        
        new_text = tmp_output_file.read().replace('\n','')
        rows = [new_text[i:i+output_length] for i in xrange(0,len(new_text),output_length)]
        output_file.write('\n'.join(rows))
        output_file.close()
        print 'Deleting temp file at %s.' % tmp_dest_file
        tmp_output_file.close()
        os.remove(tmp_dest_file)
        '''
        
if __name__=='__main__':
    if len(sys.argv) > 1: strain = sys.argv[1]
    else: strain = 'BALB'
    print 'Creating genome for %s.' % strain
    main(strain)
        
                
