'''
Created on Jun 7, 2012

@author: karmel

HOMER has motif position weight matrices with columns representing ACGT,
COMPETE wants them with rows representing ACGT, labeled.

This is a quick script to convert the HOMER motif files to pwm files
that COMPETE can read in.

NOTE: I also converted the .fa genome files as follows:

for f in ~/GlassLab/Data/Genomes/BALB_MGSC37/*.fa;
do
export out=`echo ${f} | sed -e 's/fa/txt/' | sed -e 's/Genomes/Genomes\/COMPETE/';`
/Applications/bioinformatics/compete.0.9.0/convert_seq.rb -H --alphabet ACGTN $f > $out;
done;


Symlink added to the chr directory under compete:
cmm171-164:compete.0.9.0 karmel$ ln -s /Users/karmel/Desktop/Projects/GlassLab/Data/Genomes/COMPETE/ chr/other

'''
import os
import pandas


if __name__ == '__main__':
    homer_dir = '/Applications/bioinformatics/homer/data/knownTFs/motifs'
    compete_dir = '/Applications/bioinformatics/compete.0.9.0/custom_motifs'
    
    nucleotides = 'ACGT'
    for filename in os.listdir(homer_dir):
        f = file(os.path.join(homer_dir, filename),'r')
        first_line = f.next()
        matrix = pandas.read_table(f, sep='\t', header=0, names=nucleotides)
        
        motif_name = filename.split('.')[0]
        output = open(os.path.join(compete_dir, motif_name + '.pwm'),'w')
        output.write(first_line)
        
        matrix = matrix.transpose()
        matrix.to_csv(output, sep='\t', header=False, index=True)
        
        output.close()