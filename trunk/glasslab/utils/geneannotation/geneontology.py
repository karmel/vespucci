'''
Created on Sep 8, 2010

@author: karmel

Makes SQL queries to the `GeneOntology Database`_<http://www.geneontology.org/> 
and returns results, parsed.

'''
import MySQLdb

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
         term.name
        FROM term
        WHERE
         term.acc %s ; ''' \
            % (isinstance(id,list) and ('IN (' + ','.join(['%s']*len(id)) + ')') or '= %s')
        
        cursor = self.connect_to_go_db()
        cursor.execute(query, (isinstance(id,list) and id or [id]))
        result = cursor.fetchall()
        self.close_connection()
        return zip(*result)[0]
    
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
        
            {'GO:123': ('nuclear activity',5,23)}
        
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
            
    def _get_ancestors_in_batches(self, genes, min_count=10):
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
              AND (species.species = 'sapiens'
                OR species.species = 'musculus')
              AND path_to_root.distance > '1'
            GROUP BY ancestor.acc, gene.symbol
        ) AS derived
        GROUP BY derived.acc
        HAVING count >= %s
        ;
        ''' % (','.join(['%s'] * len(genes)), min_count)
        
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
        
if __name__ == '__main__':
    print GOAccessor().get_ancestors_for_genes('4930540L03Rik', '5730442P18Rik', '5930431H10', 'Abt1', 'Akap7','Zswim2')