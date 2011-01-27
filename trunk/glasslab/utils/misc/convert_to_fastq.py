'''
Created on Jan 26, 2011

@author: karmel
'''

import sys

def convert_eland_export_to_fastq(input_file, output_file):
    # Eland:
    # HWUSI-EAS286    4       2       1       0       52      0       1       NNNNNNNACCTCAAACNNNNAAAAATCACCAATNAA    BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB    QC                                                                                      N
    # Fastq:
    # @HWUSI-EAS286:3:1:3:866#0/1
    # CTTCCACCACANGGGTCTTGGGGCTTGAACTTGGGT
    # +HWUSI-EAS286:3:1:3:866#0/1
    # abbabbbabaYD^aa^aabaa\aa`a^aaaa\`^a_
    
    out_file = open(output_file, 'w')
    for i, line in enumerate(file(input_file).readlines()):
        try:
            parts = line.split('\t')
            ident = ':'.join(parts[:6]) + '#' + parts[6] + '/' + parts[7]
            out_file.write('@' + ident + '\n')
            out_file.write(parts[8] + '\n')
            out_file.write('+' + ident + '\n')
            out_file.write(parts[9] + '\n')
        except Exception: 
            print 'FAILED on line %d: %s' % (i, line)
            raise
    
if __name__ == '__main__':
    input_file = sys.argv[1]
    output_file = input_file.split('.')[0] + '.fq'
    convert_eland_export_to_fastq(input_file, output_file)