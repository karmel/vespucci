# Troubleshooting

## Installation

#### I launched the Amazon Image, but I don't know where to find the URL for my instance.

The URL for your instance can be found on the Amazon AWS web listing for your instance as the **Public DNS**:

<a href="/documentation/images/finding_AWS_URL_large.png" target="_blank"><img alt="Screenshot of AWS interface" src="/images/finding_AWS_URL.png" /></a>

#### I added my SAM file to the database, but it was really fast, and no rows were added to the table.

Are you sure you uncompressed the file before you loaded it in? Does the file suffix indicate the file type (*.sam)? If not, did you specify --input_file_type=sam when running the `add_tags.sh` command? Is the SAM file corrupted in any way? Vespucci limits reads to those that are uniquely mapped; does your sample include only repeat data?

#### I am trying to add proto-transcripts, but I keep getting a fatal error from PostgreSQL, and the database restarts.

There are many possible causes for this, but the one that we have seen during Vespucci setup is a result of the database running out of storage space. Have you used up all the space on your server? If so, you should delete large unused files (for example, SAM and BAM files that have already been loaded into the database), or expand the space available to you on your server (<a href="http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-expand-volume.html" target="_blank">this is easy to do for the Amazon Images</a>).

#### Scoring reveals no trans

#### I want to try building Vespucci with different parameters. Do I have to restart?

#### I killed a process while it was in the middle of running. What do I do?


## Using Vespucci

#### All these raw tag tables take up a lot of space. Can I delete them?

Yes; once the raw tag tables have been converted to proto-transcripts, they are no longer used. We find keeping raw tag tables around can be useful for other purposes, but if you don't need them, feel free to drop them. This is easy to do using the PostgresSQL Studio interface that comes with the Amazon instance:

<a href="/documentation/images/drop_table_large.png" target="_blank"><img alt="Dropping a tag table in pgstudio" src="/images/drop_table.png" /></a>


#### I loaded all my data. Now what?