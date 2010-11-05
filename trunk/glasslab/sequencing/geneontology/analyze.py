'''
Created on Oct 1, 2010

@author: karmel
'''
from __future__ import division
import numpy
from glasslab.utils.datatypes.genome_reference import Genome, SequenceDetail,\
    SequenceTranscriptionRegion
from glasslab.utils.datatypes.gene_ontology_reference import BackgroundGOCount
from django.db.models.aggregates import Sum
from scipy.stats import binom_test
import os
from matplotlib import pyplot
from operator import itemgetter
from random import randint
#from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.geneannotation.gene_ontology import GOAccessor
from glasslab.sequencing.datatypes.tag import GlassTagSequence

class EnrichedOntologiesAnalyzer(object):
    max_p_val = .05
    
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
        #results_array = DelimitedFileParser('/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/analysis/MRL24-GO/less_pparg.tsv').get_array()
        #self.foreground_ontologies = dict(zip(results_array[:,0],results_array))
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
                                                    ).aggregate(Sum('appearance_count'))['appearance_count__sum']
        
        enriched = {}
        for go_id, fg_info in self.foreground_ontologies.items():
            try: 
                go_term = BackgroundGOCount.objects.get(genome_type=genome_type, go_term_id=str(go_id))
                bg_info = [go_term.go_term_id, go_term.go_term, 
                           go_term.distance_from_root, go_term.appearance_count]
            except BackgroundGOCount.DoesNotExist:
                # Term didn't make the cut for the background. 
                # Assume the appearance in the foreground is the only occurrence in the background 
                bg_info = fg_info
            bg_appearance = bg_info[-1:][0]/self.background_term_count
            p_val = binom_test(fg_info[-1:][0], n=self.foreground_term_count, p=bg_appearance)
            if p_val <= self.max_p_val:
                enriched[go_id] = fg_info + [p_val]
        self.enriched_terms = enriched
        
    def output_go_enriched_ontology(self, output_dir, file_name, genome, gene_names=None):
        '''
        Retrieve GO enrihed terms as compared to background and output tsv file.
        '''
        if not self.enriched_terms:
            # Get list of (term id, term, distance from root, count, p val) tuples
            genome_type = Genome.objects.get(genome=genome).genome_type
            self.set_enriched_genes(genome_type, gene_names=gene_names)
        
        # Sort according to p-val
        enriched_terms = sorted(self.enriched_terms.values(),key=itemgetter(4))
        
        # Output tsv
        header = 'GO Term ID\tGO Term\tDistance from root\tAppearance Count\tP-value\n'
        output_tsv = header + '\n'.join(['\t'.join(map(lambda x: str(x).strip(), row)) for row in enriched_terms])
        file_path = os.path.join(output_dir,'%s_GO_enriched_terms.tsv' % file_name)
        file = open(file_path, 'w')
        file.write(output_tsv)
    
    def graph_terms(self, output_dir, file_name, genome, gene_names=None):
        if not self.enriched_terms:
            # Get list of (term id, term, distance from root, count, p val) tuples
            genome_type = Genome.objects.get(genome=genome).genome_type
            self.set_enriched_genes(genome_type, gene_names=gene_names)
        
        # Sort according to p-val
        enriched_terms = sorted(self.enriched_terms.values(),key=itemgetter(4))
        enriched_array = numpy.array(enriched_terms)
        
        fig = pyplot.figure(figsize=(16,10))
        ax1 = fig.add_subplot(111)
        pyplot.ylabel('Distance from the root of the GO Term Tree')
        pyplot.xlabel('Log P-Value')
        ax1.set_xscale('log')
        
        # Add some noise to the distance from root column so that
        # the points on the graph are sufficiently spaced out.
        for row in enriched_array:
            row[2] = float(row[2]) + randint(-99,99)/100.0 
            # And annotate with terms
            ax1.text(float(row[4]), float(row[2]), row[1], fontsize=8, withdash=True)
            
        # Plot all points
        ax1.plot(numpy.float_(enriched_array[:,4]), numpy.float_(enriched_array[:,2]), 'o')
        
        pyplot.savefig(os.path.join(output_dir,'%s_GO_enriched_terms_graph' % file_name))
       
    def get_gene_names_from_matched_tags(self):
        '''
        Pull gene names/symbols from set of GlassTagSequences.
        '''
        where = ['"%s".sequence_identifier_id = "%s".sequence_identifier_id' \
                            % (SequenceDetail._meta.db_table, SequenceTranscriptionRegion._meta.db_table),
                 '"%s".sequence_transcription_region_id = "%s".id' \
                            % (GlassTagSequence._meta.db_table, SequenceTranscriptionRegion._meta.db_table),]
        tables = [SequenceTranscriptionRegion._meta.db_table, GlassTagSequence._meta.db_table]
        gene_names = SequenceDetail.objects.extra(where=where, tables=tables
                                    ).values_list('gene_name', flat=True).distinct()
        return map(lambda x: x.strip(), list(gene_names))
     
if __name__ == '__main__':
    gene_names = ['Daxx','Slc20a1','Gtf2f1','Haus8','Trappc1','Nfil3','Purb','Lat','Pdcd7','Rbm3','Psmb4','Rpl19','Ino80e','2700099C18Rik','Atf5','Ccdc58','Rplp1','Ptger1','Cycs','4632415K11Rik','Dnajc17','Terf2ip','1110049F12Rik','Brip1','Bap1','Parvg','Wdr76','Recql5','Cnnm4','Fam195b','Pomgnt1','Kctd18','C1galt1c1','Wibg','Tmx1','Pomt1','Atg9a','Uqcrfs1','Dtwd2','Cecr5','D9Ertd402e','Zfyve19','4930481A15Rik','Cops5','Nsmce1','Casc1','Mfap1b','Nudt16','Gin1','Rpl34','Eral1']
    analyzer = EnrichedOntologiesAnalyzer()
    analyzer.output_go_enriched_ontology('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/bucket_distribution/GO_analysis', 
                                         'notx_1h', 'mm9', gene_names)
    analyzer.graph_terms('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/bucket_distribution/GO_analysis', 
                                         'notx_1h', 'mm9', gene_names)