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

We have included <a href="/documentation/sample_queries" target="_blank">many examples of queries</a>. Here are a few to get you started.

