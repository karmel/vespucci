'''
Created on Sep 10, 2010

@author: karmel
'''
from __future__ import division
import os
from glasslab.utils.geneannotation.genbank import GeneAnotator
import numpy

class MicroarrayVisualizer(object):
    '''
    Methods for illustrating MicroarrayAggregator results.
    
    .. warning::
    
        This is not a standalone object. This is intended to be a
        partial interface, implemented by the aggregator,
        separated for ease of code use.
    
    '''
    
    ##########################################################
    # Illustration methods
    ##########################################################
    def draw_heat_map(self, output_dir='', prefix='',
                      clustered=True, include_differentials=False,
                      include_annotation=False):
        '''
        Draws a color-coded HTML heat-map based on the fold variation of 
        the samples by gene. Generate a Django-template-based HTML table
        with opacity of colors dependent on the fold.
        
        .. warning: Requires an install of Django.
        
        '''
        samples, table_cells = self._generate_table_cells(clustered, 
                                                          include_differentials,
                                                          include_annotation)
        self._output_heat_map(output_dir, prefix, clustered, include_annotation,
                          samples, table_cells)
    
    def _generate_table_cells(self, clustered, include_differentials, include_annotation):
        # Get relevant samples for display
        samples = []
        for analyzer in self.subset_analyzers:
            if analyzer.test_samples is None: analyzer.split_samples()
            samples.append((analyzer.test_samples[0],analyzer.control_samples[0]))
        
        # Include differential data if desired
        if include_differentials: self.set_log_differentials()
            
        # Get all genes with > 2-fold transformation to draw; sort as clusters
        if clustered: clusters = self.cluster_genes()
        else:
            genes, data_rows, selected_ids = self.filter_rows()
            clusters = [(genes,data_rows,selected_ids)]
            
        # For each gene to display, set up row with gene_name and 
        # a tuple of (color-class, opacity), with color defined by up- or down-regulation.
        table_cells = []
        for cluster_i, cluster in enumerate(clusters):
            genes, data_rows, selected_ids = cluster
            
            # Annotate gene data
            if include_annotation: 
                try: genes = GeneAnotator().annotate_genes(genes, overwrite=False)
                except Exception: pass
            
            genes, data_rows, selected_ids = self.sort_rows(genes, data_rows, selected_ids)
            
            row_class = cluster_i % 2 == 0 and 'even' or 'odd' # For row coloring
            for i, log_vals in enumerate(data_rows):
                cell_values = []
                for log_val in log_vals:
                    cell_values.append(self._format_for_value(log_val))
                # Get differentials, if desired
                diffs = self._format_differentials(include_differentials, selected_ids[i])
                # Assemble all into a cell 
                table_cells.append((row_class, genes[i], cell_values, diffs))
        return samples, table_cells
    
    def _format_for_value(self, val):
        if val > 0: color = 'up-regulated' 
        elif val < 0: color = 'down-regulated' 
        else: color = 'zero-regulated'
        # Opacity is 0 for log_val = 0, 100 for log_val = 3, linear in between
        opacity = '%.2f' % (min(abs(val),3)/3)
        return color, opacity
    
    def _format_differentials(self, include_differentials, i):
        '''
        Return empty list or list of log_differential (percent change%) strings.
        '''
        if not include_differentials: return []
        return ['%.4f (%.2f%%)' % (diff, (2**diff)*100) for diff in self.differentials[i]]
    
    def _output_heat_map(self, output_dir, prefix, clustered, include_annotation, samples, table_cells):
        context = {'samples': samples, 
                 'table_cells': table_cells,
                 'compared_samples': self.compared_samples,
                 'include_annotation': include_annotation,}
        filename = '%sheat_map_output%s.html' % (prefix and prefix + '_' or '',
                                                  clustered and '_clustered' or '')
        
        self._output_file(output_dir, prefix, 'heat_map.html', context, filename)
        
    def draw_enriched_ontologies(self, output_dir='', prefix=''):
        '''
        Taking advantage of the gene ontology categorization
        interface assumed on this class, draw a graph of enriched genes,
        with distance from root on the y-axis, p-value on the x-axis,
        and appearance count represented by color.
        '''
        # Enriched is a dict of go id: [go id, term, distance, count, p val]
        enriched = self.get_enriched_genes()
        enriched_array = numpy.array(enriched.values())
        # Pull out numeric values for sorting.
        val_array = numpy.float_(enriched_array[:,-3:])
        
        # Sort by distance ascending, p val ascending
        ordered_indices = numpy.argsort(val_array.view(','.join(['float64']*val_array.shape[1])), 
                                        order=['f0','f1'], axis=0)
        enriched_array = enriched_array[ordered_indices]
        
        min_distance = enriched_array[0][2]
        max_distance = enriched_array[-1:][0][2]
        min_count = enriched_array[0][3]
        max_count = enriched_array[-1:][0][3]
        min_p = enriched_array[0][4]
        max_p = enriched_array[-1:][0][4]
        
        for_display = []
        for data_row in enriched_array:
            # Modify to get display percentages for each val
            dist_percent = data_row[2]/(max_distance - min_distance)
            count_percent = data_row[3]/(max_count - min_count)
            p_percent = data_row[4]/(max_p - min_p)
            for_display.append(data_row.tolist() + [dist_percent, count_percent, p_percent])
            
        context = { 'enriched': for_display, 
                   'min_distance': min_distance,
                   'max_distance': max_distance,
                   'min_p': min_p,
                   'max_p': max_p,
                   }
        filename = '%senrichment_graph_output.html' % (prefix and prefix + '_' or '')
        
        self._output_file(output_dir, prefix, 'enrichment_graph.html', context, filename)
        
    def _output_file(self, output_dir, prefix, template_name, context, filename):
        from django.template.loader import render_to_string
        from django.conf import settings
        from glasslab import microarrays
        
        # Set up templates
        main_pkg_dir = os.path.relpath(os.path.dirname(microarrays.__file__),__file__)
        templates_dir = os.path.join(main_pkg_dir,'templates')
        # Enable using Django templates without the DJANGO_SETTINGS_MODULE setup
        try: settings.configure(TEMPLATE_DIRS = (templates_dir,))
        except RuntimeError:
            # 'Settings already configured'
            settings.TEMPLATE_DIRS = (templates_dir,)
        # Render html string
        context['base_url'] = templates_dir + '/'
        html = render_to_string(template_name,context)
        
        # Set up output directory
        output_loc = os.path.join(main_pkg_dir,'html_output')
        if prefix:
            output_loc = output_loc + '/' + (output_dir or prefix)
            if not os.path.exists(output_loc): os.mkdir(output_loc)
        # Save generated HTML to file
        f = open(output_loc + '/' + filename,'w')
        f.write(html)
        f.close()
