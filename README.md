# Vespucci

### A system for building annotated databases of nascent transcripts

Code written by Karmel Allison. Questions? Comments? Concerns? Email karmel@arcaio.com.

## About

What does Vespucci do? Briefly, it **analyzes GRO-sequencing data and allows the integration of many different genomic data types**, including ChIP-seq data, annotated databases, repeats, and so on. For the complete story, read the paper at @todo.

The code is commented-- never as well as it should be, but better than not at all-- and the formal description of Vespucci has been published at @todo. Vespucci is still **a work in progress**, with code publicly available on [GitHub](https://github.com/karmel/vespucci/). I happily take pull requests.

## Citation

If you use Vespucci, please cite:

@todo

## Installation

There are several ways to install and run Vespucci. The **easy way** is to use one of the **pre-built Amazon AWS instances** (described in section I below). The hard way is to install the dependencies from scratch. Installing from scratch is described in section II below, but I make no guarantees for results in environments other than a standard Ubuntu box.

### I. Installing from a pre-built Amazon AWS instance

Amazon Images are available for Vespucci pre-built with the hg19 or mm9 genome data. For other genomes, we provide a pre-built Image with the base Vespucci databases and all dependencies installed, awaiting installation of data for a specific genome. 

Images are available at: @todo

* Base: 
* hg19: 
* mm9: 

For all three Image types, follow steps in sections A and B below. For the hg19 and mm9 Images, skip section C, and continue with sections D and E.

#### A. Launching the Image 

Use the Amazon AWS Launch Wizard to launch an instance using the selected Image. Vespucci should run on minimally an m1.small instance, and that is what was used for all of the data described in the paper.

Notes:

* If you are unfamiliar with Amazon EC2, I suggest looking first at Amazon's [Getting Started Guide](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html).
* When setting up the firewall, you will minimally want SSH access to your instance. I also recommend allowing access at port 5432 if you would like to use a local client to view and manage your database, and access at port 80 if you would like to host browser sessions from your instance. The Security Group I use opens three ports:
	* 22 (SSH): 0.0.0.0/0
	* 80 (HTTP): 0.0.0.0/0
	* 5432 (Postgres): 0.0.0.0/0
* When in doubt, the Wizard's default options should suffice.

#### B. Setting up your instance

1. Once your instance has been launched, log in as root:

	```
	ssh -i my_security_key.pem ubuntu@ec2-11-111-11-11.compute-1.amazonaws.com
	sudo su -
	```

1. Change the vespucci user password:

	```
	passwd vespucci
	```

1. Change the PostgreSQL user passwords:

	```
	sudo -u postgres psql postgres

	# At the psql prompt:
	\password postgres
	\password vespucci_user
	\q
	```

1. Change Vespucci's record of the PostgreSQL password to match the one you set for vespucci_user:

	```
	echo '[password for vespucci_user in psql]' > /home/vespucci/Repositories/vespucci/vespucci/.database_password
	```

#### C. Installing genome data

Note: skip this section if using an Image with the hg19 or mm9 genomes already installed.

The base image of Vespucci comes with the database set up, but no genome-specific schemas installed. **To install existing genome-specific schemas (hg19, mm9, or dm3):**

1. Log in as the vespucci user:

	```
	su -l vespucci
	```

1. Install the genome of interest. In this example, I am using 'mm9'; simply replace that with 'hg19' or 'dm3' as desired. The option '-c default' here will use a default schema name; if you wanted to specify cell type or some other option of interest, you could use any label here (i.e., '-c es_cell').

	```
	~/Repositories/vespucci/vespucci/vespucci/genomereference/pipeline/scripts/set_up_database.sh -g mm9 
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_refseq_database.sh -g mm9
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_database.sh -g mm9 -c default
	```

	After running the above three commands, your vespucci database will have four schemas, each with its own set of tables: genome_reference_mm9, atlas_mm9_refseq_prep, atlas_mm9_default_prep, and atlas_mm9_default.

	Note that if you want to see the full set of options for any of the Vespucci scripts used above, simply run the script with the '--help' option.

If you want **to install a genome that is not included with Vespucci**, do the following:

@todo

#### D. Processing experimental data

Once the genome schemas are set up, you can proceed to process and build Vespucci transcripts for your experimental data. In these examples, I am using 'mm9'; simply replace that with 'hg19' or 'dm3' as desired. The option '-c default' here indicates that the default schema should be used; if you set up cell-type-specific schemas (i.e., '-c es_cell') in section C, simply replace the 'default' with the appropriate identifier.

1. Transfer over the mapped SAM or BAM GRO-seq files you will be using. I suggest putting these files, which can be rather large, in the /data directory, which is the mounted Amazon EBS volume.

	```
	scp me@my-local-server.com:/path/to/my/data/groseq_1.sam /data/sequencing
	```

1. For each separate experiment file, add the raw tags to the Vespucci database:

	```
	~/Repositories/vespucci/vespucci/vespucci/sequencing/pipeline/scripts/add_tags.sh -g mm9 -c default -f /data/sequencing/groseq_1.sam  --output_dir=/data/sequencing/  --schema_name=groseq --project_name=groseq_1 --processes=3 
	```

	Some advisements on the options:

	1. -f: the path to the SAM file
	1. --output_dir: the path to a location that Vespucci can place some output data while processing tags
	1. --schema_name: a name for the schema you would like all the tag tables to be placed in; should be Postgres-friendly (i.e., no spaces or unusual characters)
	1. --project_name: a descriptive label of the experiment in question for your future reference; this will be used in the naming of tag tables, so it should be Postgres-friendly (i.e., no spaces or unusual characters)
	1. --processes: the number of daughter processes to use; three is good for an m1.small Amazon instance
	
	Too see other available options, run the add_tags.sh script with --help.
	
1. Repeat the two steps above for all separate sequencing files. The 'groseq' schema that has been added will then have numerous tables-- one for each sequencing run added, with separate partitions for each chromosome.

1. For each sequencing run added above, assemble proto-transcripts:

	```

	```


	```

	```



#### E. Etc.

