'''
Created on Sep 8, 2010

@author: karmel

Makes SQL queries to the `GeneOntology Database`_<http://www.geneontology.org/> 
and returns results, parsed.

'''
import MySQLdb
from glasslab.utils.datatypes.genome_reference import GenomeType, SequenceDetail
from glasslab.utils.datatypes.gene_ontology_reference import BackgroundGOCount

# DB connection params
HOST = 'mysql.ebi.ac.uk'
USER = 'go_select'
PASSWD = 'amigo'
DB = 'go_latest'
PORT = 4085

class GOAccessor(object):
    connection = None
    
    def get_terms_for_ids(self, id):
        '''
        For given GO category ID(s), term labels.
        '''
        query = '''
        SELECT
         term.acc,term.name
        FROM term
        WHERE
         term.acc %s ; ''' \
            % (isinstance(id,list) and ('IN (' + ','.join(['%s']*len(id)) + ')') or '= %s')
        
        cursor = self.connect_to_go_db()
        cursor.execute(query, (isinstance(id,list) and id or [id]))
        result = cursor.fetchall()
        self.close_connection()
        return result
    
    def get_gene_names_for_category(self, id):
        '''
        For a given GO category ID, get all associated Homo Sapiens
        gene names in a tuple.
        '''
        query = '''
        SELECT DISTINCT
         gene_product.symbol
        FROM term
         INNER JOIN graph_path ON (term.id=graph_path.term1_id)
         INNER JOIN association ON (graph_path.term2_id=association.term_id)
         INNER JOIN gene_product ON (association.gene_product_id=gene_product.id)
         INNER JOIN species ON (gene_product.species_id=species.id)
         INNER JOIN dbxref ON (gene_product.dbxref_id=dbxref.id)
        WHERE
         term.acc %s
         AND (species.species = 'sapiens'
         OR species.species = 'musculus'); ''' \
            % (isinstance(id,list) and ('IN (' + ','.join(['%s']*len(id)) + ')') or '= %s')
        
        cursor = self.connect_to_go_db()
        cursor.execute(query, (isinstance(id,list) and id or [id]))
        result = cursor.fetchall()
        self.close_connection()
        return zip(*result)[0]
    
    def get_generic_ancestors(self, id):
        return self.get_ancestors(id, distance_from_root=4)
    
    def get_ancestors(self, id, distance=None, distance_from_root=None, type=None):
        '''
        Returns a list of tuples of ancestor labels according to the passed parameters
        for a given GO ID.
        '''
        query = '''
        SELECT DISTINCT
        ''' + (distance_from_root is not None and '''
        path_to_root.distance, 
        ''' or '') + '''
          ancestor.name
        FROM 
          term
            INNER JOIN graph_path ON (term.id=graph_path.term2_id)
            INNER JOIN term AS ancestor ON (ancestor.id=graph_path.term1_id)
        ''' + (distance_from_root is not None and '''
            INNER JOIN graph_path AS path_to_root ON (ancestor.id=path_to_root.term2_id)
            INNER JOIN term AS root_term ON (root_term.id=path_to_root.term1_id)
            ''' or '') \
        + ' WHERE term.acc=%s ' \
        + (distance is not None and '''
                AND graph_path.distance = %s ''' or '') \
        + (distance_from_root is not None and '''
                AND root_term.is_root = %s
                AND path_to_root.distance <= %s 
                AND path_to_root.distance != 0 ''' or '') \
        + (type is not None and '''
                AND ancestor.term_type = %s ''' or '') \
        + ';'
        
        parameters = ['GO:' + str(id).rjust(7,'0')]
        if distance is not None: parameters.append(distance)
        if distance_from_root is not None: parameters += ['1', distance_from_root]
        if type is not None: parameters.append(type)
    
        cursor = self.connect_to_go_db()
        cursor.execute(query, parameters)
        result = cursor.fetchall()
        self.close_connection()
        return result
    
    def get_ancestors_for_genes(self, genes, batch_size=1000, min_count=5):
        '''
        Returns a dictionary of tuples of distance from root, ancestor label, count
        for the passed list of gene symbols, indexed by GO ID::
        
            {'GO:123': ('GO:123','nuclear activity',5,23)}
        
        Limits to Homo sapiens or Mus musculus trees from the UniProt KB db.
        
        Note that we use a derived table such that we can get one term and one count per
        gene and per term. So, if a gene has several entries for a single term--
        for example, TGM2 and TGM1 each have several different term paths to 
        "acyltransferase activity"-- we still only get one count per gene per term,
        rather than potentially several per gene per term. This allows us to 
        calculate statistics and repeat terms more accurately.
        
        '''
        # Make sure we only have one string symbol per gene
        genes = list(set(genes))
        
        # Batch out the requests
        results = {}
        for x in xrange(0, len(genes), batch_size):
            subset = genes[x:(x+batch_size)]
            if subset: sub_results = self._get_ancestors_in_batches(subset, min_count=min_count)
            for sub_result in sub_results:
                try: 
                    # If GO ID already exists, just add in the count; other data is the same.
                    results[sub_result[0]][-1:][0] += sub_result[-1:][0]
                except KeyError: results[sub_result[0]] = list(sub_result)
        return results 
            
    def _get_ancestors_in_batches(self, genes, min_count=5):
        
        query = '''
        SELECT 
            derived.*,
            count(derived.acc) as count
        FROM
            (SELECT
              ancestor.acc,
              ancestor.name,
              path_to_root.distance 
            FROM term
            JOIN association
              ON association.term_id = term.id
            JOIN gene_product gene
              ON gene.id = association.gene_product_id
            JOIN dbxref db
              ON db.id = gene.dbxref_id
            JOIN species
              ON species.id = gene.species_id
            JOIN graph_path 
              ON term.id = graph_path.term2_id
            JOIN term AS ancestor 
              ON ancestor.id = graph_path.term1_id
            JOIN graph_path AS path_to_root 
              ON ancestor.id = path_to_root.term2_id
            JOIN term AS root_term
              ON root_term.id = path_to_root.term1_id
            WHERE
              gene.symbol IN (%s)
              AND association.is_not = '0'
              AND root_term.is_root = '1'
              AND db.xref_dbname = 'UniProtKB'
              AND (species.species = 'sapiens' OR species.species = 'musculus')
              AND path_to_root.distance > '1'
            GROUP BY ancestor.acc, gene.symbol
        ) AS derived
        GROUP BY derived.acc
        HAVING count >= %s
        ;
        ''' % (','.join(['%s'] * len(genes)),
               min_count)
        
        cursor = self.connect_to_go_db()
        cursor.execute(query, genes)
        result = cursor.fetchall()
        self.close_connection()
        return result
    
    def connect_to_go_db(self):
        self.connection = MySQLdb.connect(host=HOST,
                                     port=int(PORT),
                                     user=USER,
                                     passwd=PASSWD,
                                     db=DB)
        cursor = self.connection.cursor()
        return cursor

    def close_connection(self):
        if self.connection: 
            self.connection.close()
            self.connection = None
    
#################################################
# Asynchronous data collection
#################################################
    def set_background_ontologies(self, batch_size=1000, min_count=5):
        '''
        We want to have a distribution of expected GO term appearances to compare 
        sample data to.
        
        Here, we collect GO data for all genes we have in the database, 
        and save the expected appearance count, to save time in distribution 
        comparisons later.
        '''
        genome_types = GenomeType.objects.all().filter(genome_type='Mus musculus')
        for genome_type in genome_types:
            self._set_background_ontologies_for_genome(genome_type, 
                                                       batch_size=batch_size, 
                                                       min_count=min_count)
            
    def _set_background_ontologies_for_genome(self, genome_type, batch_size=1000, min_count=5):
        # Get all refseq ids
        gene_names = SequenceDetail.objects.filter(sequence_identifier__genome_type=genome_type
                                            ).exclude(gene_name='', gene_name__isnull=True
                                            ).values_list('gene_name', flat=True).distinct()
        
        # Retrieve GO dictionaries
        go_terms = self.get_ancestors_for_genes(map(lambda x: x.strip(), list(gene_names)))
        
        # Save to model with term, count, distance from root.
        for go_id, counts in go_terms.items():
            go_count, created = BackgroundGOCount.objects.get_or_create(genome_type=genome_type,
                                                                        go_term_id=go_id)
            go_count.go_term            = counts[1]
            go_count.distance_from_root = counts[2]
            go_count.appearance_count   = counts[3]
            go_count.save()
        
if __name__ == '__main__':
    '''
    term_ids = ['GO:0005737','GO:0005515','GO:0006629','GO:0050873','GO:0005578','GO:0016740','GO:0008152','GO:0006631','GO:0008610','GO:0016491','GO:0005739','GO:0055114','GO:0006633','GO:0016020','GO:0003824','GO:0010811','GO:0030176','GO:0005829','GO:0008654','GO:0019915','GO:0046983','GO:0006099','GO:0048514','GO:0030111','GO:0030145','GO:0008415','GO:0050840','GO:0005743','GO:0005783','GO:0015986','GO:0005856','GO:0008289','GO:0009749','GO:0005794','GO:0030198','GO:0016301','GO:0005520','GO:0006979','GO:0009437','GO:0007005','GO:0005777','GO:0008483','GO:0001701','GO:0005604','GO:0016616','GO:0007507','GO:0006915','GO:0006635','GO:0048407','GO:0003846','GO:0006644','GO:0070374','GO:0006651','GO:0005792','GO:0008201','GO:0007006','GO:0003841','GO:0005504','GO:0004144','GO:0019904','GO:0006468','GO:0042383','GO:0008035','GO:0007155','GO:0002053','GO:0001892','GO:0031012','GO:0004768','GO:0006970','GO:0048008','GO:0017154','GO:0010898','GO:0001658','GO:0060425','GO:0043353','GO:0019433','GO:0030031','GO:0030307','GO:0007498','GO:0005790','GO:0045723','GO:0007179','GO:0005102','GO:0048762','GO:0005901','GO:0001755','GO:0005778','GO:0000159','GO:0030879','GO:0043565','GO:0046579','GO:0004597','GO:0005741','GO:0006641','GO:0046328','GO:0004806','GO:0060021','GO:0045786','GO:0009605','GO:0005811','GO:0016461','GO:0030049','GO:0000287','GO:0030276','GO:0015078','GO:0008360','GO:0005024','GO:0033267','GO:0004672','GO:0005518','GO:0016747','GO:0045449','GO:0045600','GO:0003995','GO:0019432','GO:0060666','GO:0005955','GO:0045540','GO:0004065','GO:0009636','GO:0009967','GO:0005488','GO:0003682','GO:0005576','GO:0045636','GO:0001525','GO:0001725','GO:0007275','GO:0042632','GO:0042476','GO:0051287','GO:0001503','GO:0046982','GO:0040015','GO:0005096','GO:0035265','GO:0016757','GO:0042310','GO:0016936','GO:0030324','GO:0060710','GO:0004675','GO:0000139','GO:0016717','GO:0007163','GO:0004792','GO:0006098','GO:0007178','GO:0030036','GO:0048589','GO:0043066','GO:0000082','GO:0008285','GO:0050872','GO:0043208','GO:0030517','GO:0019153','GO:0043388','GO:0016298','GO:0002526','GO:0004622','GO:0042511','GO:0015992','GO:0003007','GO:0005923','GO:0070555','GO:0051789','GO:0005798','GO:0007368','GO:0008301','GO:0005740','GO:0001558','GO:0002024','GO:0022627','GO:0004702','GO:0030218','GO:0005516','GO:0050544','GO:0018107','GO:0030060','GO:0000904','GO:0000187','GO:0001935','GO:0006376','GO:0016055','GO:0005925','GO:0006397','GO:0007264','GO:0032963','GO:0008453','GO:0005975','GO:0020027','GO:0005667','GO:0070427','GO:0046855','GO:0042474','GO:0001889','GO:0006499','GO:0018008','GO:0016829','GO:0001967','GO:0030913','GO:0006672','GO:0004450','GO:0006097','GO:0006102','GO:0007492','GO:0048755','GO:0030857','GO:0060712','GO:0004674','GO:0002018','GO:0002019','GO:0004609','GO:0001822','GO:0003712','GO:0003997','GO:0004660','GO:0071208','GO:0006370','GO:0004571','GO:0048738','GO:0048185','GO:0042787','GO:0009267','GO:0031175','GO:0006897','GO:0044262','GO:0010875','GO:0042594','GO:0032934','GO:0007635','GO:0004653','GO:0033209','GO:0048545','GO:0005784','GO:0006613','GO:0009792','GO:0060039','GO:0070063','GO:0019867','GO:0048146','GO:0045822','GO:0031966','GO:0001568','GO:0032808','GO:0033179','GO:0018193','GO:0043193','GO:0007098','GO:0030855','GO:0006402','GO:0045995','GO:0010891','GO:0031234','GO:0055089','GO:0015485','GO:0006925','GO:0030325','GO:0050700','GO:0045055','GO:0032324','GO:0001543','GO:0006002','GO:0030170','GO:0019834','GO:0030334','GO:0060048','GO:0051056','GO:0005026','GO:0042134','GO:0009083','GO:0048268','GO:0009791','GO:0008432','GO:0050509','GO:0060527','GO:0001729','GO:0004084','GO:0009081','GO:0009082','GO:0060174','GO:0007588','GO:0032091','GO:0005506','GO:0006094','GO:0060669','GO:0001516','GO:0008459','GO:0033177','GO:0010843','GO:0001547','GO:0043408','GO:0045941','GO:0051384','GO:0032868','GO:0034375','GO:0004535','GO:0006107','GO:0000268','GO:0007413','GO:0004926','GO:0045785','GO:0002026','GO:0050839','GO:0031225','GO:0043627','GO:0043589','GO:0046716','GO:0005543','GO:0048511','GO:0050662','GO:0006573','GO:0006916','GO:0003700','GO:0007267','GO:0022900','GO:0048468','GO:0007527','GO:0004709','GO:0019217','GO:0016209','GO:0031594','GO:0019395','GO:0005070','GO:0017133','GO:0033600','GO:0008109','GO:0050291','GO:0005089','GO:0048596','GO:0004859','GO:0030892','GO:0007520','GO:0004721','GO:0002790','GO:0006325','GO:0019229','GO:0045444','GO:0000188','GO:0033081','GO:0031663']
    # Get corresponding terms for human readability
    term_names_by_id = dict(GOAccessor().get_terms_for_ids(list(term_ids)))
    term_rows = zip(term_ids, [term_names_by_id.get(id,'') for id in term_ids])
    print term_rows
    '''
    GOAccessor().set_background_ontologies()