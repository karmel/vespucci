'''
Created on Jun 7, 2012

@author: karmel

The COMPETE software from the Hartemink group outputs tab-separated
files, indicating TF occupancy probabilities at each bp of a given
region::

    background    pu1    cebp    nfkb    ap1    nuc_padding    nucleosome
    0.00194804459828135774    0.00001895573012159096    0.00010494929930757033    0.00000910990526225708    0.00014946780552019275    0.26100737835884330051    0.73676209430266514921
    0.06127864230576939020    0.00000089676466491985    0.00010097572221135492    0.00000008312207222229    0.00013828056951110558    0.23032810361114330888    0.70815301790462947817

We want to graph those probabilities.
'''
from __future__ import division
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import pandas
from matplotlib import pyplot
import os
import yaml
import subprocess
from glasslab.utils.datatypes.genetics import InbredStrainVariation,\
    InbredVariant, InbredStrain
from glasslab.utils.datatypes.genome_reference import Chromosome

class CompeteGrapher(SeqGrapher):
    compete_dir = '/Applications/bioinformatics/compete.0.9.0'
    compete_wrapper = 'wrapper_mammal.rb'
    ref_strain = 'C57BL'
    alt_strain = 'BALB'
    
    def configure(self, chr_name, pos_start, pos_end, basename, dirpath):
        '''
        Set up configuration for COMPETE. This will encoded as a YAML 
        file to be read in by the COMPETE wrapper.
        '''
        tf_conc = dict(pu1=0.04, cebp=0.03, nfkb=0.03, ap1=0.02)
        concentrations = dict(nuc=40.0, unbound=1.0)
        concentrations.update(tf_conc)
        
        # Make very descriptive file name.
        conc_string = '_'.join(map(lambda x: str(x).replace('.','-'),concentrations.values()))
        file_string = '{0}_{1}'.format(basename, conc_string)
        
        yaml_config = {'chr': 'other/MGSC37/{0}'.format(chr_name.lower()),
                       'chr_alt': 'other/{1}_MGSC37/{0}'.format(chr_name.lower(), self.alt_strain),
                       'range': [pos_start, pos_end],
                       'nuc': True,
                       'motifs': tf_conc.keys(),
                       'conc': concentrations,
                       'inverse_temp': 1.0,
                       'output_image': os.path.join(dirpath, 'graphs', file_string),
                       'output_basename': os.path.join(dirpath, 'output', file_string + '_' + self.ref_strain),
                       'output_filename': os.path.join(dirpath, 'output', file_string + '_' + self.ref_strain + '.txt'),
                       'output_basename_alt': os.path.join(dirpath, 'output', file_string + '_' + self.alt_strain),
                       'output_filename_alt': os.path.join(dirpath, 'output', file_string + '_' + self.alt_strain + '.txt'),
                       }
        
        return yaml_config
    
    def update_yaml(self, yaml_config, alt_start, alt_end):
        '''
        Update YAML config for run with second strain.
        '''
        yaml_config['range_ref'] = yaml_config['range'][:]
        yaml_config['range'] = [int(alt_start), int(alt_end)]
        
        for key in ('chr','output_basename','output_filename'):
            yaml_config[key + '_ref'] = yaml_config[key]
            yaml_config[key] = yaml_config[key + '_alt']
            
        return yaml_config
    
    def run_compete(self, yaml_config):
        '''
        Run using the wrapper_mammal.rb and the passed YAML config.
        
        COMPETE outputs a tab-separated value file at the location
        specified in the YAML config.
        '''
        filename = yaml_config['output_basename'] + '.yaml'
        f = open(filename, 'w')
        yaml.dump(yaml_config, f)
        f.close()
        
        # The COMPETE scripts are written without absolute or relative paths,
        # and just assume you're in the same dir. 
        # CD into that dir before running
        cmd = 'cd {0} && {1} < {2}'. format(self.compete_dir,
                                            os.path.join(self.compete_dir, self.compete_wrapper), 
                                            filename) 
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        output_name = yaml_config['output_basename'] + '_output.txt'
        f = open(output_name, 'w')
        f.write(result)
        f.close()
                
    def draw_graph(self, filename, peak_id, chr_name, pos_start, pos_end, 
                   strain_name='', subplot=121, ax=None):
        data = pandas.read_table(filename, sep='\t', header=0)
    
        ax = self.set_up_plot(subplot=subplot, ax=ax)
        basepairs = range(1,len(data) + 1) # 1-indexed for easier plotting
        colors = self.get_colors(len(data.columns))
        for i, col in enumerate(data.columns):
            probs = data[col].tolist()
            # Alternate line type for readability
            line_type = i % 2 and '-' or '--'
            pyplot.plot(basepairs, probs, line_type, color=colors[i], label=col)
            ax.fill_between(basepairs, 0, probs, color=colors[i], alpha=0.5)
        
        pyplot.xlim(basepairs[0],basepairs[-1:][0])
        title = 'Region {0}: {1}, {2}: {3} - {4}'.format(peak_id, strain_name,
                                                        chr_name, pos_start, pos_end)
        self.add_title(title, ax)
        self.add_axis_labels('Position (Basepair)', 'Probability')
        pyplot.legend()
        return ax
    
    def create_paired_plot(self, peak_id, chr_name, pos_start, pos_end, dirpath):
        '''
        Given a chromosomal location, create a plot with C57 and BALB
        predictions.
        '''
        basename = '{0}_nucleosome_occupancy_{1}_{2}_{3}'.format(
                                        peak_id, chr_name, pos_start, pos_end)
    
        yaml_config = grapher.configure(chr_name, pos_start, pos_end, basename, dirpath)
        
        # With first strain
        grapher.run_compete(yaml_config)
        ax = grapher.draw_graph(yaml_config['output_filename'], 
                                peak_id, chr_name, pos_start, pos_end, 
                                strain_name=self.ref_strain, subplot=121)
        
        # With second strain
        alt_start, alt_end = self.get_alt_position(chr_name, pos_start, pos_end)
        yaml_config = self.update_yaml(yaml_config, alt_start, alt_end)
        
        grapher.run_compete(yaml_config)
        ax = grapher.draw_graph(yaml_config['output_filename'], 
                                peak_id, chr_name, alt_start, alt_end, 
                                strain_name=self.alt_strain, subplot=122, ax=ax)
        
        grapher.save_plot(yaml_config['output_image'] + '.png')
        #grapher.show_plot()
        
    def get_alt_position(self, chr_name, pos_start, pos_end):
        '''
        Given the position in the reference, get the corresponding position
        in the alternate strain.
        
        We do this by finding the closest SNP/Indel record on either side
        of the reference region, and subtracting the differences between
        the reference and the alt to get the alt position.
        '''
        
        chrom = Chromosome.objects.get(name=chr_name.lower())
        snp_q = '''SELECT i_var.id, i_var.strain_start, i_var.strain_end,
                        variant.start, variant."end"
                FROM "{0}_{1}" i_var
                JOIN "{2}_{1}" variant
                ON i_var.inbred_variant_id = variant.id                
                JOIN "{3}" strain
                ON i_var.inbred_strain_id = strain.id
                WHERE strain.name = '{4}' 
                '''.format(InbredStrainVariation._meta.db_table, 
                           chrom.id,
                           InbredVariant._meta.db_table, 
                           InbredStrain._meta.db_table,
                           self.alt_strain)
                
        preceding_snp_q = snp_q + '''
                AND variant."end" <= {0}
                ORDER BY variant."end" DESC
                LIMIT 1;
                '''.format(pos_start)
                
        following_snp_q = snp_q + '''
                AND variant."start" >= {0}
                ORDER BY variant."start" ASC
                LIMIT 1;
                '''.format(pos_end)
                
        preceding_snp = InbredStrainVariation.objects.raw(preceding_snp_q)[0]
        following_snp = InbredStrainVariation.objects.raw(following_snp_q)[0]
        
        # New position is reference + difference at nearest SNP
        new_start = pos_start + (preceding_snp.strain_end - preceding_snp.end)
        new_end = pos_end + (following_snp.strain_start - following_snp.start)
        
        return new_start, new_end
    
    def check_sequence(self, chr_name, pos_start, pos_end, alt_start, alt_end):
        '''
        Sanity check to make sure we're pulling the same region...
        Not run normally; this is an incredibly inefficient way of doing this.
        
        Just want to make sure all looks good the first time around.
        '''
        fasta_dir = '/Users/karmel/GlassLab/Data/Genomes/MGSC37'
        fasta_dir_alt = '/Users/karmel/GlassLab/Data/Genomes/BALB_MGSC37'
        ref_fa = file(os.path.join(fasta_dir,chr_name + '.fa'))
        alt_fa = file(os.path.join(fasta_dir_alt,chr_name + '.fa'))
        ref_fa = ''.join(map(lambda x: x[:-1], list(ref_fa.readlines())[1:]))
        alt_fa = ''.join(map(lambda x: x[:-1], list(alt_fa.readlines())[1:]))
        if ref_fa == alt_fa: print 'Same sequence at {0}: {1} - {2}'.format(chr_name, pos_start, pos_end)
        print 'Ref seq:'
        print ref_fa[pos_start:pos_start+50]
        print 'Alt seq:'
        print alt_fa[alt_start:alt_start+50]
        
        
if __name__ == '__main__':
    dirpath = '/Users/karmel/Glasslab/Notes_and_Reports/Inbred_strains/Compete'
    
    data = pandas.read_table(os.path.join(dirpath,'validation_peaks.txt'), sep='\t')
    grapher = CompeteGrapher()
    
    for _, row in data.iterrows():
        grapher.create_paired_plot(row['peak_id'], row['chr_name'], 
                                   row['start'], row['end'], dirpath)
        
    