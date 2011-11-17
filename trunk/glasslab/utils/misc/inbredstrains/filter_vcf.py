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
    
    strains = (14, 19, 21) # BALB, NOD, DBA
    inc_reference = (16, 14, 19, 21)
    
    atg_index = 0 # Varies with vcf version?
    format_field_count = 9
    for line in f:
        fields = line.split('\t')
        if line[:4] == '#CHR':
            # Header
            write_line(fields[:format_field_count] + [fields[i] for i in inc_reference], o1)
            continue
        elif line[0] == '#': continue #o1.write(line) #
        elif fields[16] != '.' and int(fields[16].split(':')[atg_index]) != 0: 
            # Format:  GT:ATG:MQ:HCG:GQ:DP
            # We want ATG == 0 for black6, since that means "of quality, and matches reference"
            # Or just a '.', which means, "No difference"
            continue
        else:
            for strain_of_interest in strains:
                fields_to_write = [] 
                try:
                    if fields[16] != '.' and int(fields[strain_of_interest].split(':')[atg_index]) > 0: 
                        # We want ATG == 1 for the strains, since that means "of quality, and doesn't match reference"
                        fields_to_write.append(strain_of_interest)
                except ValueError: pass
                
                # We only want to write indels to file if they passed the threshold; otherwise, include a '.'
                if fields_to_write:
                    write_line(fields[:format_field_count] + \
                               [i in fields_to_write and fields[i] or '.' for i in inc_reference], o1)

    o1.close()
    return output

def write_line(fields, output):
    if fields: output.write('\t'.join(fields) + '\n')
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1: file_name = sys.argv[1]
    else: file_name = '/Users/karmel/Downloads/20110602-callable-dinox-indels.vcf'
    if len(sys.argv) > 2: output_file = sys.argv[2]
    else: output_file = '/Users/karmel/Downloads/four_strain_cleaned.vcf'
    
    filter_variants(file_name, output_file)

