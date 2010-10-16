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
    gene_names = ['Hebp2','BC067068','Midn','Apba3','Cct2','4632428N05Rik','Herc4','Dse','Pcbd1','Arid5b','Gdf11','Stat6','Igf1','Btbd2','Rps12','Prep','Poc1b','Tyms-ps','Wdr18','Slc16a10','Atp5d','Ckap4','Bclaf1','Mir677','Mobkl2a','Fam54a','Tab2','Gipc3','1810014B01Rik','4930430F08Rik','Gpx4','Nrbf2','Adora2a','1600002K03Rik','Thap2','BC030307','Zbtb2','Eid3','Ccdc138','Lims1','Cd63','Rab3ip','Plekhg1','Glipr1','Sgpl1','Ccdc109a','Kiss1r','Stx7','Rnf146','Lims1','Tor3a','Usf1','Gm11435','Bcl11a','Actr2','Sox9','Vwc2','Ptrh2','Inpp1','Rpl37a','6330403A02Rik','Aftph','Krtap9-5','Cnp','Ywhae','0610010F05Rik','Nab1','Dhrs11','Kat2a','Tbc1d10a','Pafah1b1','Snord65','Traf4','Grin2c','Phospho1','Rpain','Itga2b','Tex14','Npb','Hint1','Sirt7','Rffl','Nmt1','Slc22a21','Zfp238','Hormad2','Sh3d20','Inpp5k','Tmigd1','Tmem93','Slc43a2','Fbf1','Nr1d1','Morc2a','Zzef1','Msl1','Pik3r6','Evi2a','Cryba1','Pitpna','Myl4','Abr','Mgat1','Samd14','Morc2a','Stat5b','Slfn5','Rtn4','P2rx1','1810010H24Rik','2810442I21Rik','D630032N06Rik','Pfkfb2','Spag9','Nufip2','Rnf135','Hexdc','Snord91a','Slc5a10','Rasl10b','Utp18','Fam196b','Gm11978','Mir338','Zfp207','Zbtb4','Krt23','Atp2a3','Rnd2','Urgcp','Smcr7','Timm22','Mir1933','Gpr75','Plek','Sost','Sec14l1','Hnrnpab','Maml1','BC003331','Trp53i13','Limd2','Cdk5r1','Akap10','Steap3','AF251705','Naglu','Trpv2','Aebp1','Glt25d2','Il1r2','Fbxo36','Zbtb25','Nek9','Slamf6','Pnn','Ppm1a','Pqlc3','Smek1','Greb1','B930059L03Rik','Adam21','Tmbim1','Mterfd2','Esrrg','Tex22','Rps6kl1','Evl','Scarna3b','Coch','Rdh12','Prpf39','Mir1938','Cd84','Prkch','Adam17','Adipor1','Pea15a','Fam72a','Casp8','Fancm','Ap4s1','Gm5069','Gls','Actr1b','Psen2','Brp44','Mir7-1','1110007C09Rik','Fst','Otp','Serpinb6c','Zcchc6','Tmem171','Slc35b3','Caml','Tagln2','Hist1h1c','Larp4b','Nol7','Hist1h4m','Rala','Erbb2ip','C130071C03Rik','Bhmt','Mirlet7d','Fn1','Hist1h1a','Hist1h1t','C130036L24Rik','Sykb','Ptprc','Adcy2','Cflar','Prdm14','B4galt7','Il1r1','B3gat2','Arhgap30','A530098C11Rik','Mir26b','Mir181b-1','Mir29b-2','Pbk','Gtf2f2','Zmym5','Supt16h','Dusp13','BC061237','4921530L21Rik','Stab1','Chrna2','Bnip3l','Ints6','Tkt','Cdk5r2','Mudeng','Lpar6','Ccdc122','Anxa7','Tspan14','Mapk1ip1l','Ttc18','Cenpj','Mir15a','Kctd4','Tcea1','Arl11','Ptk2b','Cacna2d3','Hmbox1','Fut11','Lect1','A330023F24Rik','Elf1','Ercc6','Ube2e2','Ncoa4','Mir664','Fam78b','2310016M24Rik','Csf2rb2','Pabpc1','Ccnt1','Ncf4','Ubr5','Cyth4','St3gal1','Zfp641','Tatdn1','Rrm2b','Nfam1','Syngr1','Rnasen','Sub1','Rpl30','Ddn','Sla','Nckap1l','Tbrg3','Dcaf13','Arhgap39','Mir30b','Slc48a1','Snord72','Snora2b','Pphln1','Sepp1','Map3k12','Zfr','Copa','Tarbp2','Rictor','Lgals1','Ppil3','Ormdl1','2310037I24Rik','C030006K11Rik','Med15','Smg7','Naa50','Ypel1','1700037C18Rik','Tmem186','Btla','Tnk2','Pigp','Gart','5730403B10Rik','Bcl6','Cyp2ab1','Snord66','Fgd4','Fgd4','Mgrn1','Psmg1','Nr1i2','BC031361','Stx19','Ccdc58','Popdc2','Prdm15','Mir185','Il10rb','Bfar','Dlg1','Mir1947','Glyr1','Slc12a8','Crybg3','Ptplb','Snx4','Mkl2','Arpc5','Soat1','Coro7','Psen2','Ntan1','Solh','Ldhal6b','AI314976','Rhoq','H2-M2','Gm3435','Igf2r','Tcfeb','Map4k3','Srsf3','Abcg5','Atp6v1h','Fam173a','Rnps1','Mas1','Ipo9','Tap2','Chd1','Bat2','Ticam1','9030025P20Rik','Ppm1b','Fbxo11','Vmn2r103','Arhgap28','Brpf3','Ncrna00085','Safb','Trim39','0610007P22Rik','Thoc6','Prepl','Vav1','Olfr115','Fpr-rs3','Olfr111','Mdc1','AA388235','Vapa','Ddah2','H2-DMa','Synj2','Bat1a','Mrps18b','Vmn1r233','Snora20','Rftn1','Kctd5','Hsp90ab1','Pcdhgc5','Traf5','Bin1','Kdm3b','Cndp1','Ppic','Tshz1','Onecut2','Slmo1','Rbm22','Smad2','Scarna17','Csf1r','Zbed6','Mir122a','Etf1','Snora74a','Atg12','Gm6225','Mir1-2-as','Diap1','Scyl3','Snx24','Farsb','Arl8a','Eif3a','Scgb1a1','Cfl1','Ubtd1','Nanos1','Loxl4','Kank1','Cnih2','B3gat3','Mbl2','Sgms1','Hnrnpul2','Dak','Cyp26c1','Tm9sf3','Cd274','Tnks2','Slc15a3','Pgam1','Unc93b1','Naa40','E030024N20Rik','Trak2','Mms19','Tcfcp2l1','Cyp17a1','Mus81','Myof','Ssh3','Ptprcap','Rtn3','Idh1','Tor2a','Dnajc5','Catsper2','Acp2','1700026L06Rik','Olfr1256','Gpr21','Olfr341','Prpf40a','Gfra4','Ppp4r1l-ps','Ckap2l','Pla2g4b','Ss18l1','B230120H23Rik','Tank','Tspyl3','Bcl2l1','Ccdc148','Rapsn','Dpp7','Gabpb1','Usp50','0610011L14Rik','Madd','Rabgap1','Gnas','Dhrs9','Sp3','Ttbk2','Samhd1','Frmd4a','Spag4','Pabpc1l','Emilin3','Arl6ip6','Taf3','Slc23a2','Lcmt2','Pcif1','Mafb','A730017L22Rik','Uckl1','Baz2b','Fbxw2','Hspa14','Mrpl41','Mir674','5430413K10Rik','Gle1','Ppp2r4','Eif2ak4','1700003F12Rik','4930426L09Rik','Rrbp1','Lmo2','Nelf','Adig','Med22','Fam83c','Ptprj','Chn1','Itgb6','Kbtbd4','Ptpra','Rc3h2','Olfr1164','Thbd','Polr1b','Pik3ca','Psmb4','15-Sep','Nras','Ugt8a','Gstm1','Srsf11','Wdr77','Ank2','Mapksp1','Gatad2b','Ghsr','Anxa5','Hist2h2be','Rusc1','Phf17','Mllt11','Celf3','Capza1','Bank1','6330549D23Rik','Snord45b','Lmo4','Mir186','Adamtsl4','Prpf38b','Gm6649','4933434E20Rik','LOC100233207','Fbxw7','Mtx1','Fam63a','Celsr2','Extl2','Lmna','Larp7','Wdr47','Phtf1','S100a11','Mnd1','Dnajb4','Cd53','2010016I18Rik','2500003M10Rik','0610031J06Rik','Ythdf3','Dram2','2810046L04Rik','Sf3b4','Tpm3','Fubp1','Rg9mtd2','S100a10','Nadk','Eya3','Rnf19b','Dnaja1','Dnaic1','Padi6','Sepn1','Rragc','Rps20','Rod1','Zyg11b','Gm5151','Stoml2','Tstd2','Ccne2','Tmem67','D4Ertd22e','Fblim1','Snx30','Nans','Matn1','Slc31a1','Sdcbp','Tpm2','6330407A03Rik','1110017D15Rik','Gm12603','Angptl7','Pnrc1','C1qb','Mir32','Mrps15','A3galt2','Akr7a5','Artn','Atg4c','Tekt2','Slc24a2','Ythdf2','Pgd','Guca2a','Orc3l','Orm2','Bmp8a','Ybx1','Csf3r','Eif2c1','2210012G02Rik','Pex10','Hmgcl','Eps15','Thrap3','Cdk11b','Daglb','Rplp0','Tesc','Pi4k2b','Dnajb6','Kcnip4','Slc24a6','Sh2b3','Por','Slc15a4','4930471M23Rik','Mapkapk5','Ankrd17','Rpl9','Slc10a4','Rac1','Ppargc1a','3110082I17Rik','Mpv17','Mfsd10','Magi2','Grsf1','Zfp655','Naa25','Hsd17b11','Fgfr3','Aff1','Ficd','3110047P20Rik','Rpl5','Sh3bp2','Gm10240','U90926','Zcwpw1','Zfp644','Spon2','Gusb','Gm3414','Arl6ip4','Ankrd13a','Stk32b','Trafd1','Cd38','Polr2j','Rbm47','Cyp51','Scfd2','Psph','Golga3','Tchp','Steap4','Aff1','Snrnp35','Tec','Selplg','2410003K15Rik','Luc7l2','C1galt1','Casc1','Rab19','Gt(ROSA)26Sor','A130022J15Rik','Mrpl53','Asb15','4833442J19Rik','Etv6','Gp9','Mitf','Dgki','H1fx','Wnt5b','Dysf','Grip2','Irf5','Bola3','D6Wsu116e','Il23r','Foxp2','Gabarapl1','Bcl2l14','Parp12','Tsen2','Gprc5d','Pparg','Cd69','Gng12','Mir200c','Mir29b-1','Nap1l5','Mxd1','Isy1','Hnrnpf','Cnbp','Mitf','Htra2','Hipk2','Spsb2','Cops7a','Nrf1','Nagk','Kcmf1','Cd9','Ing4','Krcc1','Zfml','Rassf8','Zc3hav1l','Cnot3','B3gnt6','Dpf1','Rps11','4933405O20Rik','U2af2','Tmem143','Art2b','Parva','Bbc3','Ech1','Grin2d','Cox7a1','Stk32c','Fbrs','Pycard','Itgax','Leng1','1110007A13Rik','Pold1','Rps17','Dbp','Orai3','Psmd8','Scube2','6430526N21Rik','3110040N11Rik','Gltscr1','Lin7b','Ypel3','Zfp646','Cln3','Zc3h4','Mesdc2','Arl6ip1','Kcnq1ot1','Hif3a','Zik1','Ldha','Zranb1','Zfp143','Snora3','Slc27a5','Catsperg1','Olfr566','5830432E09Rik','Pcf11','2310014L17Rik','Leng9','Capn12','Ldhc','D030047H15Rik','Lysmd4','Ctbp2','Plekhb1','Zfp710','Cd37','Tgfb1','St5','Irgc1','Cd79a','Hcst','Prr19','Ftl1','1810020D17Rik','Emp3','Akt2','Lyrm1','F10','Lamp1','Isyna1','Lyl1','Cotl1','Ptger1','Junb','Lrrc29','Ddhd2','Mfhas1','Agrp','Sh2d4a','Tom1','Sc4mol','Gatad2a','Plekha2','1700029H14Rik','Cyb5b','Irf2','Pkn1','1700018L24Rik','Neil3','Tssk6','Pdf','Cyld','Adcy7','Use1','Ankrd37','Whsc1l1','4933407C03Rik','Mir23a','Znrf1','B930053N02Rik','Tpm4','Mir1903','Rbpms','Stxbp2','Rasa3','Orc6l','BC088983','Atxn1l','Cln8','Snx20','Timm44','Trappc2l','Rad23a','Kcnj1','Alg9','Ube4a','Aplp2','Bnip2','Myo5a','Fam96a','P4htm','Arih1','St14','Isl2','Mcam','Senp6','Nptn','Cep57','Manf','Mtap4','Rbp1','Birc3','Ei24','Grinl1a','Hyal3','Rab8b','Pkm2','Epm2aip1','Snora62','Myo5c','Uchl4','Myo6','Rwdd2a','Fam46a','Bcl2a1b','Dalrd3','4930581F22Rik','Stmn1-rs1','Myo9a','Ick','Mns1','Eif3g','Slc26a6','Slc37a2','Ccnb2','Nktr','Taf1d','Olfr920','Qrich1','Bace1','Arpp19','Il10ra','Myo1e','Qtrt1','Shroom2','Zrsr2','Magee1','Kdm5c','Mpp1','Tmem164','Rpl36a','Gm6121','Snx12','Eif1ax','Tcfe3','Gm14458','Flna','Btk','Mtap7d3','Snora70','Sh3kbp1','Slc6a8','Akap14','F630028O10Rik','Gucy2f','Naa10','Klhl4','Rps4x','Mtmr1','Agtr2','Alas2','Ddx3y']
    analyzer = EnrichedOntologiesAnalyzer()
    analyzer.output_go_enriched_ontology('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/all_notx', 
                                         'ncor_ko_notx_only', 'mm9', gene_names)
    analyzer.graph_terms('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/all_notx', 
                                         'ncor_ko_notx_only', 'mm9', gene_names)