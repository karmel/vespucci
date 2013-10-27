# Frequently Asked Questions

* [Installation](#installation)
* [Using Vespucci](#using-vespucci)

## Installation

#### I launched the Amazon Image, but I don't know where to find the URL for my instance.

The URL for your instance can be found on the Amazon AWS web listing for your instance as the **Public DNS**:

<a href="/documentation/images/finding_AWS_URL_large.png" target="_blank"><img alt="Screenshot of AWS interface" src="/images/finding_AWS_URL.png" /></a>

#### <span id="no-raw-tags">I added my SAM file to the database, but it was really fast, and no rows were added to the tag table.</span>

Are you sure you uncompressed the file before you loaded it in? Does the file suffix indicate the file type (*.sam)? If not, did you specify --input_file_type=sam when running the `add_tags.sh` command? Is the SAM file corrupted in any way? Vespucci limits reads to those that are uniquely mapped; does your sample include only repeat data?

Once you figure out what the cause is, you can drop the empty tag table and retry the `add_tags.sh` command with the fixed SAM file. This is easy to do using the <a href="/README.md#e-etc" target="_blank">PostgresSQL Studio interface that comes with the Amazon instance</a>:

<a href="/documentation/images/drop_table_large.png" target="_blank"><img alt="Dropping a tag table in pgstudio" src="/images/drop_table.png" /></a>

#### I am trying to add proto-transcripts, but I keep getting a fatal error from PostgreSQL, and the database restarts.

There are many possible causes for this, but the one that we have seen during Vespucci setup is a result of the database running out of storage space. Have you used up all the space on your server? If so, you should delete large unused files (for example, SAM and BAM files that have already been loaded into the database), or expand the space available to you on your server (<a href="http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-expand-volume.html" target="_blank">this is easy to do for the Amazon Images</a>).

#### Everything moves quickly, but then I get an error when building the Vespucci database that there are no rows in the Atlas Transcript Prep. What happened?

Chances are, you didn't load in data like you thought you did in one of the earlier steps. Check your raw tag tables; are they empty? If so, see the note about [empty raw tag tables above](#no-raw-tags).

If your raw tag tables have data, but that data didn't make it into the preparatory database, try re-assembling the prototranscripts using the `transcripts_from_tags.sh` command. Make sure that you have specified the schema name and tag table name correctly; the tag table name should be the project name you specified when loading the raw tag tables prepended with `tag_`. Note, too, that the project name should therefore preferably be lowercase with no spaces or unusual punctuation. 

#### I want to try building Vespucci with a different MAX_EDGE or DENSITY_MULTIPLIER. Do I have to restart from the beginning?

No. You can simply delete (or rename) the final Vespucci schema you built. For example, rename `atlas_mm9_default` to `atlas_mm9_default_max_edge_500` using the <a href="/README.md#e-etc" target="_blank">PostgreSQL Studio interface</a>: 

<a href="/documentation/images/drop_schema_large.png" target="_blank"><img alt="Drop schema controls in pgstudio" src="/images/drop_schema.png" /></a>

<a href="/documentation/images/rename_schema_large.png" target="_blank"><img alt="Renaming a schema in pgstudio" src="/images/rename_schema.png" /></a>

Then, you can set up the new database with the command:

	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_database.sh -g mm9 -c default --final

(Make sure to use the same genome and suffix specifier you used with the original build.) From there, you can reset the allowed edge and density multiplier with the `set_density` command, and then rebuild the final database all in one go:

	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --set_density --stitch_processes=1 --draw_edges --score --max_edge=1000 --density_multiplier=100000


## Using Vespucci

#### All these raw tag tables take up a lot of space. Can I delete them?

Yes; once the raw tag tables have been converted to proto-transcripts, they are no longer used. We find keeping raw tag tables around can be useful for other purposes, but if you don't need them, feel free to drop them. This is easy to do using the <a href="/README.md#e-etc" target="_blank">PostgresSQL Studio interface that comes with the Amazon instance</a>:

<a href="/documentation/images/drop_table_large.png" target="_blank"><img alt="Dropping a tag table in pgstudio" src="/images/drop_table.png" /></a>

#### I loaded all my data. Now what? 

Now, you can ask you data questions. What is the biological problem you are addressing? How can you formulate that as a SQL query over the data?

We have included <a href="/documentation/sample_queries" target="_blank">many examples of queries</a>. Here are a couple to get you started.

**Get all expressed RefSeq transcripts**

	-- RefSeq genes with transcript details
	SELECT refseq.sequence_identifier, t.*
	FROM atlas_mm9_default.atlas_transcript t
	JOIN atlas_mm9_default.atlas_transcript_sequence seq
	ON t.id = seq.atlas_transcript_id
	JOIN genome_reference_mm9.sequence_transcription_region reg
	ON seq.sequence_transcription_region_id = reg.id
	JOIN genome_reference_mm9.sequence_identifier refseq
	ON reg.sequence_identifier_id = refseq.id
	WHERE t.score >= 1
	AND t.parent_id IS NULL
	AND seq.major = true;


**Get all transcripts with RPKM in Sample 1 versus Sample 2**

	-- Get log fold change between runs
	SELECT log(2,rpkm(t, s1.tag_count, run1.total_tags)/rpkm(t, s2.tag_count, run2.total_tags)) as log_fold_change,
	rpkm(t, s1.tag_count, run1.total_tags) as rpkm1, 
	rpkm(t, s2.tag_count, run2.total_tags) as rpkm2
	FROM atlas_mm9_default.atlas_transcript t

	JOIN atlas_mm9_default.atlas_transcript_source s1
	ON t.id = s1.atlas_transcript_id
	JOIN genome_reference_mm9.sequencing_run run1
	ON s1.sequencing_run_id = run1.id
	AND run1.source_table = 'groseq"."tag_wt_notx_12h_1'

	JOIN atlas_mm9_default.atlas_transcript_source s2
	ON t.id = s2.atlas_transcript_id
	JOIN genome_reference_mm9.sequencing_run run2
	ON s2.sequencing_run_id = run2.id
	AND run2.source_table = 'groseq"."tag_wt_notx_12h_2'

	WHERE t.score >= 1
	AND t.parent_id IS NULL;

Note that you can view the loaded sequencing runs in the table `genome_reference_mm9.sequencing_run` (or the equivalent for the genome in question), as seen in the screenshot below.

<a href="/documentation/images/sequencing_runs_large.png" target="_blank"><img alt="Sequencing run table in pgstudio" src="/images/sequencing_runs.png" /></a>

With the result sets from your query of interest, you can do anything you want-- export to other tools; collect gene lists for further research; view regions of interest in the browser; correlate with other data sets to find enhancers and eRNA; and so on.