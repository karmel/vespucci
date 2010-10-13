'''
Created on Oct 1, 2010

@author: karmel
'''
from __future__ import division
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
from operator import itemgetter
from random import randint
from glasslab.utils.parsing.delimited import DelimitedFileParser

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
        for i,row in enumerate(enriched_array):
            row[2] = float(row[2]) + randint(-99,99)/100.0 
            # And annotate with terms
            ax1.text(float(row[4]), float(row[2]), row[1], fontsize=8, withdash=True)
            
        # Plot all points
        ax1.plot(numpy.float_(enriched_array[:,4]), numpy.float_(enriched_array[:,2]), 'o')
        
        pyplot.savefig(os.path.join(output_dir,'%s_GO_enriched_terms_graph' % file_name))
        
    def get_gene_names_from_current_peaks(self):
        '''
        Pull gene names/symbols from set of Current Peaks.
        '''
        where = ['"%s".sequence_identifier_id = "%s".id' \
                            % (GeneDetail._meta.db_table, TranscriptionStartSite._meta.db_table),
                 '"%s".transcription_start_site_id = "%s".id' \
                            % (CurrentPeak._meta.db_table, TranscriptionStartSite._meta.db_table),]
        tables = [CurrentPeak._meta.db_table, TranscriptionStartSite._meta.db_table]
        gene_names = GeneDetail.objects.extra(where=where, tables=tables
                                    ).values_list('gene_name', flat=True).distinct()
        return map(lambda x: x.strip(), list(gene_names))
        
if __name__ == '__main__':
    gene_names = ['Hbs1l','Tle2','Pwp1','4930444G20Rik','Gm6251','Scyl2','Aldh8a1','Gm8580','Dos','Gng7','Unc5b','Sarnp','Esr1','Srgn','Pcsk4','3110056O03Rik','Mif4gd','Brca1','Ifi47','Krt10','Map3k14','1700113I22Rik','Lrrc45','Per1','Pus10','Ppp2ca','Slc22a21','Adora2b','Osbpl7','Snap47','Hsd17b1','3010026O09Rik','Nme2','Nme1','4933400C05Rik','Slc43a2','Helz','Arhgap27','Prss38','Rnf157','Plcd4','Plscr3','Trim65','Scarf1','Ccdc157','Nlrp1a','Tac4','Ddx42','Cd34','Pgam2','Zfp652','Foxk2','Cabp7','Erlec1','Fzd7','Abcb6','Arg2','Arl4c','C130039O16Rik','Zc3h14','Fam110c','Rhoj','Prkch','5830403L16Rik','Casp8','Glrx2','Ndufs6','Srd5a1','Fars2','Nln','Hist1h2an','C030044B11Rik','Zfp58','Tppp','Icos','Zfp367','Tmem170b','Mxd3','Hist1h3f','Bcs1l','Ptcd2','Ppyr1','Sorbs3','Eaf1','Nfatc4','6720463M24Rik','Phyhip','E330020D12Rik','Gm4902','Gm3646','Dph3','Ncoa4','Grid1','C030002c11rik','Uchl3','Dpysl2','Cbx6','Chadl','Eif3e','Srebf2','Ncaph2','Ttc33','Lalba','Prickle1','Fam118a','Nhp2l1','Copz1','Fam134b','Slamf9','Dusp28','Nudcd1','Carf','Arl13b','Heg1','Cldn14','Gm5483','Dnajb11','Zbtb41','Gfer','Srf','Ppt2','Gm4455','H2-Oa','Zfp799','Pdxk-ps','Ly6g6f','Cyp4f41-ps','4930432O21Rik','Gm16386','Sik1','Trerf1','Ptk7','Ccdc75','Gnptg','Cul9','Msh6','Pknox1','H2-Eb2','Fbxo38','Lipg','Proc','Tmem173','Tcof1','Cenpl','Mir1949','Cdca5','Acta2','Rpp30','Slc25a45','Snx15','Cyp2c44','Prdx3','Cwf19l1','Lipm','Ndufv1','Unc50','Rab1b','Frmd8','Hectd2','Ndor1','Elmo2','Scai','Zswim3','Foxs1','Ttc30b','Dhx35','Actr5','Pfdn4','Immp1l','Dhrs9','Il1rn','Ddb2','Myo3a','Ankrd16','Slc27a4','2700094K13Rik','Pfdn4','Sh3glb2','Gm3230','BC005624','Il1f9','Rxra','Eid1','Hbxip','Syde2','A730020M07Rik','Bbs7','Tars2','Lrriq3','Ndufb5','Dnajc11','Fhad1','Plk3','Inpp5b','Thap3','Tnfsf15','Fsd1l','2610002D18Rik','Gabrr2','Rars2','Ldlrap1','Txlna','Epb4.1','Ggh','Mir697','Nmnat1','Eno1','Gm13124','Ppcs','Mir101a','Eps15','Pink1','Denr','Mapre3','Ift172','Zfp512','0610040B10Rik','Insig1','Tmem120b','Gm4741','Rufy3','N4bp2l1','Zfp113','Exoc1','Wbscr22','Hipk2','Pcgf1','Necap1','Mrpl19','Akr1b3','Cdkn1b','Asprv1','Iffo1','Caprin2','Ahcyl2','Impdh1','Vmn1r39','Chchd4','Akr1b10','Xpc','Ppfibp2','Cnot3','Rrm1','BC053749','Phrf1','Parva','Klc3','Clns1a','Olfr525','Gprc5b','Tarm1','Zfp541','Arfip2','Gltscr1','Nsmce4a','Zfp580','Ppfia1','Zscan22','Pou2f2','Ppfibp2','Slc25a22','Ppp2r2d','Zfp768','Mark4','Zfp606','Prmt3','Rnaseh2a','Helt','Terf2ip','D030016E14Rik','Exoc8','1810029B16Rik','Rfx1','Gsr','Slc7a2','Gipc1','Gm10333','Ints10','Gatad2a','1700067K01Rik','3930402G23Rik','Mri1','Cope','Fcho1','Adat1','Mst1r','Rrp9','Rnf123','Cd276','Gm8884','Exosc7','Vps26b','Kbtbd3','Rab39','Trcg1','Rwdd2a','Maml2','1110032A03Rik','Trim29','Hdac6','Nono','Magee2','Uprt','Prdx4','Idh3g','Pgk1','Pin4','Mcart6','Ppp1r3f','Fam46d','A230072E10Rik','BC023829','Fam199x','Gnl3l','4933403O08Rik','Mid2']
    analyzer = EnrichedOntologiesAnalyzer()
    analyzer.output_go_enriched_ontology('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/all_kla', 
                                         'wt_kla_only', 'mm9', gene_names)
    analyzer.graph_terms('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/all_kla', 
                                         'wt_kla_only', 'mm9', gene_names)