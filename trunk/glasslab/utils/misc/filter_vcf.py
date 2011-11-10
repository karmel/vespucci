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
    
    strains = (14, 19, 21)
    inc_reference = (14, 16, 19, 21)
    for line in f:
        fields = line.split('\t')
        if line[:4] == '#CHR':
            # Header
            write_line(fields[:5] + [fields[i] for i in inc_reference], o1)
            continue
        elif line[0] == '#': continue
        elif int(fields[16].split(':')[1]) != 0: 
            # Format:  GT:ATG:MQ:HCG:GQ:DP
            # We want ATG == 0 for black6, since that means "of quality, and matches reference"
            continue
        else:
            for strain_of_interest in strains: # BALB, NOD, DBA
                try:
                    if int(fields[strain_of_interest].split(':')[1]) > 0: 
                        # We want ATG == 1 for the strains, since that means "of quality, and doesn't match reference"
                        write_line(fields[:5] + [fields[i] for i in inc_reference], o1)
                        break
                except ValueError: pass

    o1.close()
    return output

def write_line(fields, output):
    if fields: output.write('\t'.join(fields) + '\n')
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1: file_name = sys.argv[1]
    else: file_name = '/Users/karmel/Downloads/20110602-final-snps.vcf'
    if len(sys.argv) > 2: output_file = sys.argv[2]
    else: output_file = '/Users/karmel/Downloads/20110602-final-snps_strain_only_cleaned.vcf'
    
    filter_variants(file_name, output_file)

