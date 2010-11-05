#!/usr/bin/Rscript

# Load GO-Seq library
library('goseq')

# Load PostgreSQL library
library('RdbiPgSQL')

# Establish connection to DB-- passed in as host, port, dbname, user, pass
args = commandArgs(trailingOnly=TRUE)
conn <- Rdbi::dbConnect(PgSQL(),host=args[1],port=args[2],dbname=args[3],user=args[4],password=args[5])

# Set up query and retrieve-- one RefSeq ID for each gene, 
# plus binary indicator of whether it appears in our peaks
query = paste('SELECT DISTINCT trim(gene.gene_name) as gene_identifier, ',
		'MAX(CASE WHEN tag_seq.sequence_transcription_region_id > 50 THEN \'1\' ',
		'ELSE \'0\' END) AS expressed FROM "',
		args[6], '" gene JOIN "', args[7], 
		'" seq ON gene.sequence_identifier_id = seq.id JOIN "', args[8], 
		'" reg ON reg.sequence_identifier_id = seq.id LEFT OUTER JOIN (',
		'SELECT count(sequence_transcription_region_id), sequence_transcription_region_id ',
		' FROM "', args[9], '" GROUP BY sequence_transcription_region_id) ',
		' tag_seq on reg.id = tag_seq.sequence_transcription_region_id ',
		'GROUP BY gene.gene_name;', sep='');
enriched_genes <- Rdbi::dbGetQuery(conn,query);

# Take each column as a vector, using the gene identifiers as names for the binary vector
vals <- as.integer(enriched_genes$expressed)
labels <- enriched_genes$gene_identifier
names(vals) <- labels

# Removed 'r' representing masked status of genome if it exists,
# as GOSeq only supports the standard, unmasked set.
genome <- gsub("r", "", args[10])

# Set up the probability weighting function that relates length of gene
# to likelihood of enrichment.
pwf <- nullp(vals, genome, 'geneSymbol', bias.data=NULL,plot.fit=FALSE)

# Save plot of PWF
png(paste(args[11],'/',args[12],'_plotted_PWF.png', sep=''))
plotPWF(pwf, binsize=200)
dev.off()

# Get enriched go terms.
# This method returns a three-column matrix-- GO ID | p-val of enrichment | p-val of under-enrichment
enriched_go <- goseq(pwf, genome, 'geneSymbol')

# Create table to hold our enriched GO IDs
# Note that we create unique index and table names to avoid index name conflicts in the DB
table_name = paste('"',args[9],'_goseq','"', sep='')
random_suffix = as.integer(runif(1,0,999999))
id_name = paste('"',args[9],'_goseq_id_',random_suffix,'"', sep='')
primary_key_name = paste('goseq_analysis_primary_key_',random_suffix, sep='')
create_sql = paste(
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