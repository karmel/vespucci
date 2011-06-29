'''
Created on Jun 16, 2011

@author: karmel
'''
from scipy.cluster.vq import whiten, kmeans, vq
import numpy
from glasslab.glassatlas.analysis.machinelearning.base import MLSetup
import os

class GlassKMeansClusterer(object):
    
    def cluster_rows(self, data, k=10):
        ''' 
        Each row is a feature vector, with measurements across samples as the points.
        
        return -- list of 2D arrays.  Each array contains the data points that belong to a specific cluster.
        
        Uses kmeans algorithm to find the clusters. 
        '''
        # Whiten the data to attain unit variance
        wh_data = whiten(data)
        # Cluster the data, obtaining the code_book of clusters
        code_book,dist = kmeans(wh_data,k)
        # Obtain the cluster id for each row of data
        code_ids, distortion = vq(wh_data,code_book)
        # Group the original data by cluster
        original_ordering = list(xrange(0,data.shape[0]))
        clusters = []
        for i in xrange(len(code_book)):
            cluster = (numpy.compress(code_ids == i,original_ordering,0),
                       numpy.compress(code_ids == i,data,0))
            clusters.append(cluster)
        return clusters
    
    
    ##########################################################
    # Illustration methods
    ##########################################################
    def draw_heat_map(self, output_dir, prefix, raw_data, features, clusters, fields, include_pos=False):
        '''
        Draws a color-coded HTML heat-map based on the fold variation of 
        the samples by gene. Generate a Django-template-based HTML table
        with opacity of colors dependent on the fold.
        
        .. warning: Requires an install of Django.
        
        '''
        table_cells = self._generate_table_cells(raw_data, features, clusters)
        self._output_heat_map(output_dir, prefix, table_cells, fields, include_pos=include_pos)
    
    def _generate_table_cells(self, raw_data, fields, clusters):            
        # For each gene to display, set up row with gene_name and 
        # a tuple of (color-class, opacity), with color defined by up- or down-regulation.
        table_cells = []
        for cluster_i, cluster in enumerate(clusters):
            selected_ids, data_rows = cluster
            
            row_class = cluster_i % 2 == 0 and 'even' or 'odd' # For row coloring
            for i, log_vals in enumerate(data_rows):
                cell_values = []
                for log_val in log_vals:
                    cell_values.append(self._format_for_value(log_val))
                
                # Assemble all into a cell
                orig_data_i = selected_ids[i]
                row = [row_class, 
                       self._clean_text(raw_data[orig_data_i][fields.index('admin_link')]), 
                       self._clean_text(raw_data[orig_data_i][fields.index('chr_name')]), 
                       self._clean_text(raw_data[orig_data_i][fields.index('transcription_start')]), 
                       self._clean_text(raw_data[orig_data_i][fields.index('transcription_end')]), 
                       self._clean_text(raw_data[orig_data_i][fields.index('strand')]),
                       self._clean_text(raw_data[orig_data_i][fields.index('ucsc_link_mm9')]), 
                       self._clean_text(raw_data[orig_data_i][fields.index('gene_names')]), 
                       cell_values] 
                table_cells.append(row)
                
        return table_cells
    
    def _format_for_value(self, val):
        if val > 0: color = 'up-regulated' 
        elif val < 0: color = 'down-regulated' 
        else: color = 'zero-regulated'
        # Opacity is 0 for log_val = 0, 100 for log_val = 3, linear in between
        opacity = '%.2f' % (min(abs(val),3)/3)
        title = 'Log FC: %.2f' % val
        return color, opacity, title
    
    def _clean_text(self, val):
        return val.strip().strip('"').strip('{').strip('}').replace('""','"')
    
    def _output_heat_map(self, output_dir, prefix, table_cells, fields, include_pos=False):
        context = {'table_cells': table_cells, 
                   'fields':fields,
                   'include_pos': include_pos}
        filename = '%sheat_map_output.html' % (prefix and prefix + '_' or '')
        
        self._output_file(output_dir, 'heat_map.html', context, filename)
        
    def _output_file(self, output_dir, template_name, context, filename):
        from django.template.loader import render_to_string
        from django.conf import settings
        
        # Set up templates
        templates_dir = os.path.join(os.path.dirname(__file__),'templates')
        # Enable using Django templates without the DJANGO_SETTINGS_MODULE setup
        try: settings.configure(TEMPLATE_DIRS = (templates_dir,))
        except RuntimeError:
            # 'Settings already configured'
            settings.TEMPLATE_DIRS = (templates_dir,)
        # Render html string
        context['base_url'] = templates_dir + '/'
        html = render_to_string(template_name,context)
        
        # Save generated HTML to file
        f = open(output_dir + '/' + filename,'w')
        f.write(html)
        f.close()

def for_ligands(data, fields, erna):
    data = setup.filter_data_refseq(data,fields)
    data = setup.filter_data_score(data,fields)
    data = setup.filter_data_notx_tags(data,fields)
    
    # Select columns
    selected = ['rosi_4h_fc','mrl24_4h_fc','gw3965_4h_fc','qw0072_4h_fc',]#'dex_4h_fc']
    feat_data, indices = setup.get_selected_vectors(data, fields, selected)
    
    feat_data = setup.filter_data_has_change(feat_data,fields, change=.6)
    
    clusterer = GlassKMeansClusterer()
    clusters = clusterer.cluster_rows(feat_data)
    
    output_dir = '/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/clustering/kmeans/ligands/'
    clusterer.draw_heat_map(output_dir, 'ligands%s' % (erna and '_erna' or ''), setup.text_data, setup.text_fields, clusters, selected)
    
def for_dex(data, fields, erna):
    if not erna: 
        #data = setup.filter_data_notx_tags(data,fields, tags=5000)
        data = setup.filter_data_refseq(data,fields)
        data = setup.filter_data_score(data,fields)
        #data = setup.filter_data_kla_upreg(data,fields)
    
    # Select columns
    selected = ['dex_2h_fc','dex_4h_fc','dex_kla_fc',]
    feat_data, indices = setup.get_selected_vectors(data, fields, selected)
    
    
    feat_data = setup.filter_data_has_change(feat_data,fields, change=[1,1,.8])
    
    clusterer = GlassKMeansClusterer()
    clusters = clusterer.cluster_rows(feat_data, k=6)
    
    output_dir = '/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/clustering/kmeans/dex/'
    clusterer.draw_heat_map(output_dir, 'dex%s' % (erna and '_erna' or ''), setup.text_data, setup.text_fields, clusters, selected, include_pos=True)
    
if __name__ == '__main__':
    erna = False
    
    setup = MLSetup()
    text_fields_file = '/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/%sgene_names.txt' \
                        % (erna and 'erna/' or '')
    data, fields = setup.get_data_from_file(file_name='/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/%sfold_change_vectors.txt' \
                                            % (erna and 'erna/' or ''),
                                            text_file_name=text_fields_file, header=True)
    for_dex(data, fields, erna)
    
    