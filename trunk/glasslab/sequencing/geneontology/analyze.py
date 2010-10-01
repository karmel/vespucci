'''
Created on Oct 1, 2010

@author: karmel
'''
import numpy
from glasslab.utils.geneannotation.gene_ontology import GOAccessor
from glasslab.utils.datatypes.genome_reference import GeneDetail,\
    TranscriptionStartSite, Genome
from glasslab.sequencing.datatypes.peak import CurrentPeak
from glasslab.utils.datatypes.gene_ontology_reference import BackgroundGOCount
from django.db.models.aggregates import Sum
from scipy.stats import binom_test
import os
from matplotlib import pyplot
import math
from matplotlib.axis import Axis

class EnrichedOntologiesAnalyzer(object):
    go_accessor = None
    foreground_ontologies = None
    background_term_count = None
    foreground_term_count = None

    enriched_terms = None
    def set_foreground_ontology(self, genes_names):
        '''
        For the passed set of genes of interest,
        get ontological terms from the GeneOntology database.
        '''
        if not self.go_accessor: self.go_accessor = GOAccessor()
        
        self.foreground_ontologies = self.go_accessor.get_ancestors_for_genes(genes_names)
        results_array = numpy.array(self.foreground_ontologies.values())
        self.foreground_term_count = sum(numpy.float_(results_array[:,-1]))
        
    def set_enriched_genes(self, genome_type, gene_names=None):
        '''
        Compare appearance counts and distributions of passed gene names 
        to the background counts for all genes of this genome type.
        '''
        if not gene_names:
            gene_names = self.get_gene_names_from_current_peaks()
            
        self.set_foreground_ontology(gene_names)
        if not self.background_term_count:
            self.background_term_count = BackgroundGOCount.objects.filter(genome_type=genome_type
                                                                ).aggregate(Sum('appearance_count'))
        
        enriched = {}
        for go_id, fg_info in self.foreground_ontologies.items():
            try: 
                go_term = BackgroundGOCount.objects.get(genome_type, genome_type, go_term_id=go_id)
                bg_info = [go_term.go_term_id, go_term.go_term, 
                           go_term.distance_from_root, go_term.appearance_count]
            except KeyError:
                # Term didn't make the cut for the background. 
                # Assume the appearance in the foreground is the only occurrence in the background 
                bg_info = fg_info
            bg_appearance = bg_info[-1:][0]/self.background_term_count
            p_val = binom_test(fg_info[-1:][0], n=self.foreground_term_count, p=bg_appearance)
            if p_val <= self.max_p_val:
                enriched[go_id] = fg_info + [p_val]
        self.enriched_terms = enriched
    
    def output_go_enriched_ontology(self, output_dir, file_name, genome):
        '''
        Retrieve GO enrihed terms as compared to background and output tsv file.
        '''
        if not self.enriched_terms:
            # Get list of (term id, term, distance from root, count, p val) tuples
            genome_type = Genome.objects.get(genome=genome).genome_type
            self.set_enriched_genes(genome_type)
        
        # Output tsv
        header = 'GO Term ID\tGO Term\tDistance from root\tAppearance Count\tP-value\n'
        output_tsv = header + '\n'.join(['\t'.join(map(lambda x: str(x).strip(), row)) for row in self.enriched_terms])
        file_path = os.path.join(output_dir,'%s_GO_enriched_terms.tsv' % file_name)
        file = open(file_path, 'w')
        file.write(output_tsv)
    
    def graph_terms(self, output_dir, file_name, genome):
        if not self.enriched_terms:
            # Get list of (term id, term, distance from root, count, p val) tuples
            genome_type = Genome.objects.get(genome=genome).genome_type
            self.set_enriched_genes(genome_type)
        
        # Convert to array for easy column reference
        enriched_array = numpy.array(self.enriched_terms.values())
        
        pyplot.autoscale(enable=True)
        pyplot.ylabel('Distance from the root of the GO Term Tree')
        pyplot.xlabel('Log P-Value')
        Axis.set_xscale(log=10)
        
        # Plot all points
        pyplot.plot(numpy.float_(enriched_array[:,4]), numpy.float_(enriched_array[:,2], 'o'))
        
        # And annotate with terms
        for row in enriched_array:
            pyplot.annotate(row[1], (float(row[4])+.2, float(row[2]) + .2))
        
        pyplot.savefig(os.path.join(output_dir,'%s_GO_enriched_terms_graph' % file_name))
        
    def get_gene_names_from_current_peaks(self):
        '''
        Pull gene names/symbols from set of Current Peaks.
        '''
        where = ['"%s".sequence_identifier_id = "%s".id' \
                            % (GeneDetail._meta.db_table, TranscriptionStartSite._meta.db_table),
                 '"%s".transcription_start_site = "%s".id' \
                            % (CurrentPeak._meta.db_table, TranscriptionStartSite._meta.db_table),]
        tables = [CurrentPeak._meta.db_table, TranscriptionStartSite._meta.db_table]
        gene_names = GeneDetail.objects.extra(where=where, tables=tables
                                    ).values_list('gene_name').distinct()
        return gene_names
        