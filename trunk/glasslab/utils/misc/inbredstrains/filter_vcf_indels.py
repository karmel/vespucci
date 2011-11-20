'''
Created on Nov 4, 2011

@author: karmel

WARNING: This is not a robust script. This is intended for a single use case.
If the file format or column ordering or anything changes, this will
have to be updated!

'''

def filter_variants(file_name, output_file=None):
    f = file(file_name)
    output = output_file or (file_name + '.clean')
    o1 = file(output, 'w')
    
    strains = (14, 19, 21) # BALB, DBA, NOD
    inc_reference = (16, 14, 19, 21)
    
    format_field_count = 9
    for line in f:
        fields = line.split('\t')
        if line[:4] == '#CHR':
            # Header
            write_line(fields[:format_field_count] + [fields[i] for i in inc_reference], o1)
            continue
        elif line[0] == '#': o1.write(line) #continue 
        elif fields[16] != '.': 
            # Format:  GT:GQ
            # We want to ensure the reference matches the reference, as represented by a '.'
            continue
        else:
            fields_to_write = [] 
            for strain_of_interest in strains:
                try:
                    genotype, quality = fields[strain_of_interest].split(':')
                except ValueError: genotype, quality = fields[strain_of_interest], 40 # No Phred provided; assume good enough
                try:
                    if genotype[0] != genotype[2]: continue # Heterozygous
                    elif int(quality) < 40: continue # Phred score too low
                    elif int(genotype[0]) > 0:
                        # This is a legit indel; keep to write to file
                        fields_to_write.append(strain_of_interest)
                except IndexError: pass
                
            # We only want to write indels to file if they passed the threshold; otherwise, include a '.'
            # Info field (index 8) in this file is screwed up; leave out and insert a '.'
            if fields_to_write:
                # We remove the info field because the allele counts are all off, since we removed many mice strains
                write_line(fields[:format_field_count] + \
                           [i in fields_to_write and fields[i] or '0/0' for i in inc_reference], o1)

    o1.close()
    return output

def write_line(fields, output):
    if fields: output.write('\t'.join(fields) + '\n')
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1: file_name = sys.argv[1]
    else: file_name = '/Users/karmel/Downloads/20110602-callable-dinox-indels.vcf'
    if len(sys.argv) > 2: output_file = sys.argv[2]
    else: output_file = '/Users/karmel/Downloads/four_strain_indels.vcf'
    
    filter_variants(file_name, output_file)

