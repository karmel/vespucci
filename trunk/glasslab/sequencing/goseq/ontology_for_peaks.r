# Load GO-Seq library
library('goseq')

# Load PostgreSQL library
library('RdbiPgSQL')

# Establish connection to DB-- passed in as host, port, dbname, user, pass
#args = commandArgs()
args = c('placeholder','localhost',63333,'glasslab','glass','monocyte',
		'genome_reference"."gene_detail','genome_reference"."sequence_identifier',
		'genome_reference"."transcription_start_site','genome_reference"."genome',
		'current_projects"."enriched_peaks_first_test_2010-09-28_19-16-55_691375',
		'mm9','/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/test',
		'testing_go_seq')
conn <- Rdbi::dbConnect(PgSQL(),host=args[2],port=args[3],dbname=args[4],user=args[5],password=args[6])

# Set up query and retrieve-- one RefSeq ID for each gene, 
# plus binary indicator of whether it appears in our peaks
query = paste('SELECT DISTINCT gene.refseq_gene_id, ',
		'MAX(CASE WHEN peak.transcription_start_site_id IS NOT NULL THEN \'1\' ',
		'ELSE \'0\' END) AS expressed FROM "',
		args[7], '" gene JOIN "', args[8], 
		'" seq ON gene.sequence_identifier_id = seq.id JOIN "', args[9], 
		'" tss ON tss.sequence_identifier_id = seq.id JOIN "', args[10],
		'" genome ON tss.genome_id = genome.id LEFT OUTER JOIN "',
		args[11], '" peak on peak.transcription_start_site_id = tss.id ',
		'WHERE (genome.genome = \'', args[12],
		'\' AND seq.genome_type_id = genome.genome_type_id)
		GROUP BY gene.refseq_gene_id;', sep='');
enriched_genes <- Rdbi::dbGetQuery(conn,query);

# Take each column as a vector, using the gene identifiers as names for the binary vector
vals <- as.integer(enriched_genes$expressed)
labels <- enriched_genes$refseq_gene_id
names(vals) <- labels

# Removed 'r' representing masked status of genome if it exists,
# as GOSeq only supports the standard, unmasked set.
genome <- gsub("r", "", args[12])

# Set up the probability weighting function that relates length of gene
# to likelihood of enrichment.
pwf <- nullp(vals, genome, "refGene", bias.data=NULL,plot.fit=FALSE)

# Save plot of PWF
png(paste(args[13],'/',args[14],'_plotted_PWF.png', sep=''))
plotPWF(pwf, binsize=200)
dev.off()

# Get enriched go terms.
# This method returns a three-column matrix-- GO ID | p-val of enrichment | p-val of under-enrichment
enriched_go <- goseq(pwf, genome, 'refGene')

# Create table to hold our enriched GO IDs
# Note that we create unique index and table names to avoid index name conflicts in the DB
table_name = paste('"',args[11],'_goseq','"', sep='')
random_suffix = as.integer(runif(1,0,999999))
id_name = paste('goseq_analysis_seq_id_',random_suffix, sep='')
primary_key_name = paste('goseq_analysis_primary_key_',random_suffix, sep='')
create_sql = paste('SET search_path TO "current_projects";',
		'DROP TABLE IF EXISTS ', table_name, '; ',
		'CREATE TABLE ',table_name, ' ( ',
		'id integer NOT NULL, ',
		'go_term_id character(20), ',
		'p_value_overexpressed float, ',
		'p_value_underexpressed float ',
		'); ',
		'CREATE SEQUENCE ', id_name,
		' START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1; ',
		'ALTER SEQUENCE ', id_name, ' OWNED BY ', table_name, '.id; ',
		'ALTER TABLE ', table_name, ' ALTER COLUMN id SET DEFAULT nextval(\'',id_name ,'\'::regclass); ',
		'ALTER TABLE ONLY ', table_name, ' ADD CONSTRAINT ', primary_key_name, ' PRIMARY KEY (id); ', sep='')
Rdbi::dbSendQuery(conn,create_sql)

# We save all values to a new table that is created based on the peak table.
# We can then assign terms, filter by p-value, etc. back in python.
insert_sql = paste('INSERT INTO ', table_name, 
		' (go_term_id, p_value_overexpressed, p_value_underexpressed) ',
		'VALUES ', sep='')
for (i in 1:nrow(enriched_go)) {
	row = enriched_go[i,]
	insert_sql = paste(insert_sql, "('", row$category, "','", row$upval, "','", row$dpval, "')", sep='')
	if (i != nrow(enriched_go)) { insert_sql = paste(insert_sql,',', sep='') }
}
insert_sql = paste(insert_sql, ';', sep='')
Rdbi::dbSendQuery(conn,insert_sql)