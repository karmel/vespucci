# Vespucci
test
### A system for building annotated databases of nascent transcripts

Code written by Karmel Allison. Questions? Comments? Concerns? Email karmel@arcaio.com.

* [About](#about)
* [Citation](#citation)
* [Installation](#installation)
* [Frequently Asked Questions](/documentation/faq.md)

## About

What does Vespucci do? Briefly, it **analyzes GRO-sequencing data and allows the integration of many different genomic data types**, including ChIP-seq data, annotated databases, repeats, and so on. For the complete story, read the paper at @todo.

The code is commented-- never as well as it should be, but better than not at all-- and the formal description of Vespucci has been published at @todo. Vespucci is still **a work in progress**, with code publicly available on [GitHub](https://github.com/karmel/vespucci/). I happily take pull requests.

## Citation

If you use Vespucci, please cite:

@todo

## Installation

There are several ways to install and run Vespucci. The **easy way** is to use the **pre-built Amazon AWS Image** (described in section I below). The hard way is to install the dependencies from scratch. Installing from scratch is described in section II below, but I make no guarantees for results in environments other than a standard Ubuntu box.

### I. Installing from a pre-built Amazon AWS instance

An Amazon Machine Image (AMI) is available for Vespucci with the base Vespucci databases and all dependencies installed, awaiting installation of data for a specific genome. 

The current AMI is available here: <a href="https://console.aws.amazon.com/ec2/home?region=us-east-1#launchAmi=ami-e303518a" target="_blank">Vespucci v0.91, AMI ID ami-cbda91a2</a>.

#### A. Launching the Image 

Use the Amazon AWS Launch Wizard to launch an instance using the selected Image. 

Notes:

* If you are unfamiliar with Amazon EC2, I suggest looking first at Amazon's <a href="http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html" target="_blank">Getting Started Guide</a>.
* Vespucci should run on minimally an **m1.small** instance, and that is what was used for all of the data described in the paper.
* The images are EBS backed volumes. We recommend a minimum of 100 GB of mounted space, which is sufficient for a dataset of the size discussed in the publication, but more space is recommended if you will be loading lots of data.
* When setting up the firewall, you will minimally want SSH access to your instance. I also recommend allowing access at port 5432 if you would like to use a local client to view and manage your database, access at port 80 if you would like to host browser sessions from your instance, and access at port 8080 if you would like to use the <a href="#pgstudio-link" target="_blank">pre-installed PostgreSQL Studio web interface</a>. The Security Group I use opens four ports:
	* 22 (SSH): 0.0.0.0/0
	* 80 (HTTP): 0.0.0.0/0
	* 5432 (Postgres): 0.0.0.0/0
	* 8080 (Tomcat for PostgreSQL Studio): 0.0.0.0/0
* When in doubt, the Wizard's default options should suffice.

#### B. Setting up your instance

1. Once your instance has been launched, log in as root:

	```
	ssh -i my_security_key.pem ubuntu@ec2-11-111-11-11.compute-1.amazonaws.com
	sudo su -
	```
	Note that the image launches pre-loaded with the username ubuntu as a sudoer. The URL for your instance can be found on the Amazon AWS web listing for your instance as the **Public DNS**, and should look like the example above.

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

The base image of Vespucci comes with the database set up, but no genome-specific schemas installed. **To install existing genome-specific schemas (hg19, mm9, or dm3):**

1. Log in as the vespucci user:

	```
	su -l vespucci
	```

1. Install the genome of interest. In this example, I am using `mm9`; simply replace that with `hg19` or `dm3` as desired. The option `-c default` here will use a default schema name; if you wanted to specify cell type or some other option of interest, you could use any label here (i.e., `-c es_cell`).

	```
	~/Repositories/vespucci/vespucci/vespucci/genomereference/pipeline/scripts/set_up_database.sh -g mm9 
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_refseq_database.sh -g mm9
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_database.sh -g mm9 -c default
	```

	After running the above three commands, your vespucci database will have four schemas, each with its own set of tables: `genome_reference_mm9`, `atlas_mm9_refseq_prep`, `atlas_mm9_default_prep`, and `atlas_mm9_default`.

	Note that if you want to see the full set of options for any of the Vespucci scripts used above, simply run the script with the `--help` option.

To install a genome that is not included with Vespucci, see section III below.

#### D. Processing experimental data

Once the genome schemas are set up, you can proceed to process and build Vespucci transcripts for your experimental data. In these examples, I am using `mm9`; simply replace that with `hg19` or `dm3` as desired. The option `-c default` here indicates that the default schema should be used; if you set up cell-type-specific schemas (i.e., `-c es_cell`) in section C, simply replace the `default` with the appropriate identifier.

**Note: Some of the data loading can take a very long time. We recommend backgrounding processes by adding an ampersand (&) to the end of the command line, or running processes in a <a href="http://www.gnu.org/software/screen/manual/screen.html" target="_blank">screen</a>.**

1. Transfer over the mapped SAM or BAM GRO-seq files you will be using. I suggest putting these files, which can be rather large, in the /data directory, which is the mounted Amazon EBS volume. Note that you must decompress SAM and BAM files if necessary.

	```
	scp me@my-local-server.com:/path/to/my/data/groseq_1.sam.gz /data/sequencing
	gunzip /data/sequencing/groseq_1.sam.gz
	```

1. For each separate experiment file, add the raw tags to the Vespucci database:

	```
	~/Repositories/vespucci/vespucci/vespucci/sequencing/pipeline/scripts/add_tags.sh -g mm9 -c default -f /data/sequencing/groseq_1.sam  --output_dir=/data/sequencing/  --schema_name=groseq --project_name=groseq_1 --processes=3 
	```

	Some advisements on the options:
	* `-f`: the path to the SAM file
	* `--output_dir`: the path to a location that Vespucci can place some output data while processing tags
	* `--schema_name`: a name for the schema you would like all the tag tables to be placed in; should be Postgres-friendly (i.e., no spaces or unusual characters)
	* `--project_name`: a descriptive label of the experiment in question for your future reference; this will be used in the naming of tag tables, so it should be Postgres-friendly (i.e., no spaces or unusual characters)
	* `--processes`: the number of daughter processes to use; three is reasonable for a dedicated m1.small Amazon instance
	* `--no_refseq_segmentation`: this option specifies that when transcripts are stitched together, RefSeq boundaries should not be enforced, and instead the full nascent transcript lengths should be respected (see referenced paper for full detail).
	
	Too see other available options, run the add_tags.sh script with `--help`.
	
1. Repeat the two steps above for all separate sequencing files. The `groseq` schema that has been added will then have numerous tables-- one for each sequencing run added, with separate partitions for each chromosome.

	```
	scp me@my-local-server.com:/path/to/my/data/groseq_2.sam.gz /data/sequencing
	gunzip /data/sequencing/groseq_2.sam.gz
	~/Repositories/vespucci/vespucci/vespucci/sequencing/pipeline/scripts/add_tags.sh -g mm9 -c default -f /data/sequencing/groseq_2.sam  --output_dir=/data/sequencing/  --schema_name=groseq --project_name=groseq_2 --processes=3 
	```

1. For each sequencing run added above, assemble proto-transcripts:

	```
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --schema_name=groseq --tag_table=tag_groseq_1 --processes=5
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --schema_name=groseq --tag_table=tag_groseq_2 --processes=5
	```

	Importantly, in the usual case, the `--tag_table` is the same as the `--project_name` supplied above with "tag_" prepended. However, if for some reason you had manually named tables, `--tag_table` will work with whatever name you pass it.
	
1. Stitch together proto-transcripts. If you are adding a great number of sequencing runs, I recommend running this command at least every ~30 million tags (i.e., after three runs with ten million tags each are added). This helps keep the size of the proto-transcript tables down, which helps Postgres run more efficiently.

	```
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --stitch --stitch_processes=1
	```
	
	The option `--stitch_processes` indicates how many processes should be used during stitching. Stitching is a very RAM-intensive procedure, so we recommend using only one process at a time on an m1.small node.
	
1. After all runs have been added and stitched, calculate the density for each of the assembled proto-transcripts:

	```
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --set_density --stitch_processes=1
	```

1. Finally, build and score the tables of assembled transcripts:

	```
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --draw_edges --score
	```

	As with all the scripts above, run with `--help` to see other available options.


#### E. Etc.

You now have database tables built with assembled GRO-seq transcripts, which can be accessed with any number of <a href="http://wiki.postgresql.org/wiki/Community_Guide_to_PostgreSQL_GUI_Tools" target="_blank">Postgres client GUIs</a>, or from the psql command line: 

	psql -U vespucci_user vespucci

The Amazon instance also comes **pre-loaded with <a href="http://www.postgresqlstudio.org" target="_blank"><span id="pgstudio-link">PostgreSQL Studio</span></a>**, a web-based GUI that makes viewing your databases very simple. You can connect to the web interface by directing your web browser to:

	http://ec2-11-111-11-11.compute-1.amazonaws.com:8080/pgstudio

And entering the appropriate Postgres credentials:

	Database Host: localhost
	Database Port: 5432
	Database Name: vespucci
	Username: vespucci_user
	Password: <password you set for vespucci_user at psql prompt>

The **assembled transcripts are in the atlas_mm9_default schema**, in the set of atlas_transcript tables. Please see the publication referenced above for more detail on schema layouts and sample queries in the Supplementary Information.

You can **output a track for viewing on the <a href="http://genome.ucsc.edu/" target="_blank">UCSC Genome Browser</a>** with the following command, where `--output_dir` is the location the output files should be stored:

	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/transcripts_from_tags.sh -g mm9 -c default --output_dir=/data/www/ucsc/

The generated files will be suffixed with the date. They can then be added as custom tracks to the Genome Browser using the URLs:

	# Sense strand:
	http://ec2-11-111-11-11.compute-1.amazonaws.com/ucsc/Atlas_Transcripts_YYYY_mm_dd_0.bed
	# Anti-sense strand:
	http://ec2-11-111-11-11.compute-1.amazonaws.com/ucsc/Atlas_Transcripts_YYYY_mm_dd_1.bed

**Peak files generated using the <a href="http://biowhat.ucsd.edu/homer/" target="_blank">Homer analysis suite</a>** can be added automatically with the following command:

	~/Repositories/vespucci/vespucci/vespucci/sequencing/pipeline/scripts/add_peaks.sh -g mm9 -f /data/sequencing/chipseq_1.txt --schema_name=chipseq --project_name=chipseq_1

Other genomic data types can be added as new tables using the standard PostgreSQL import functionality. In order to allow for easy querying, we suggest adding a btree indexed column with a chromosome_id that refers back to the `id` column of `genome_reference_mm9.chromosome` and a gist indexed column that is an `intrange` datatype encompassing the start and end of the genomic entity in question.

### II. Installing from scratch

If you are comfortable at the command line, you may want to install Vespucci and its dependencies from scratch. Here are notes on how I have done this on Ubuntu Linux boxes in Amazon's EC2 cloud; modify as necessary!

	# All as root unless otherwise indicated.
	
	apt-get update
	apt-get -y install gcc git
	
	# Enable screen for all users
	chmod a+rw /dev/pts/0
	
	######################
	# Install python + pkgs
	######################
	mkdir /software
	chmod -R 775 /software/
	chown :ubuntu /software
	cd /software
	wget http://09c8d0b2229f813c1b93-c95ac804525aac4b6dba79b00b39d1d3.r79.cf1.rackcdn.com/Anaconda-1.5.0-Linux-x86_64.sh
	chmod +x Anaconda*.sh
	./Anaconda*.sh
	# install in /software/anaconda
	echo "PATH=/software/anaconda/bin:$PATH" >> /etc/profile
	source /etc/profile
	
	easy_install django
	
	######################
	# Install Postgres
	######################
	
	add-apt-repository -y ppa:pitti/postgresql
	apt-get update
	apt-get -y install postgresql-9.2 postgresql-server-dev-all
	easy_install psycopg2

	# DB setup
	sudo -u postgres psql postgres
	\password postgres
	\q
	
	# May not be necessary for your case;
	# But for Amazon instance, move DB to EBS volume
	mkdir -p /data/postgresql/9.2
	mv /var/lib/postgresql/9.2/main /data/postgresql/9.2

	vim /etc/postgresql/9.2/main/postgresql.conf 
	# Change location of data directory
	# data_directory = '/data/postgresql/9.2/main'
	# Open to outside world
	# listen_addresses = '*'
	# Turn off SSL
	# ssl    = false
	
	vim /etc/postgresql/9.2/main/pg_hba.conf 
	# Add TCP/IP for remote hosts if desired
	
	/etc/init.d/postgresql restart
	
	######################
	# Vespucci user setup
	######################
	
	export USER_NAME='vespucci'
	
	sudo -u postgres createuser -D -A -R -P ${USER_NAME}_user
	sudo -u postgres createdb -O ${USER_NAME}_user ${USER_NAME}

	useradd -d /home/${USER_NAME} -m ${USER_NAME} -s /bin/bash
	passwd ${USER_NAME}
	
	mkdir -p /data/sequencing
	chmod 775 /data/sequencing
	chown ${USER_NAME}:${USER_NAME} /data/sequencing
	mkdir -p /data/www/ucsc/
	chown -R ${USER_NAME}:${USER_NAME} /data/www/
	chmod -R 777 /data/www/

	######################
	# Install Nginx
	######################
	
	# If you want to host UCSC browser files
	# ${SERVER_NAME} below should be your hostname, i.e., sub.example.com
	apt-get -y install nginx
	echo "server {
	    listen   80;
	    server_name ${SERVER_NAME};
	    root /data/www;

	    access_log  /var/log/nginx/${USER_NAME}-access.log;
	    error_log  /var/log/nginx/${USER_NAME}-error.log info;

	    # what to serve if upstream is not available or crashes
	    error_page 500 502 503 504 /document_root/media/50x.html;
	}
	" > /etc/nginx/sites-available/${USER_NAME}.conf
	ln -s /etc/nginx/sites-available/${USER_NAME}.conf /etc/nginx/sites-enabled/
	/etc/init.d/nginx restart
	
	######################
	# Install PostgreSQL Studio
	######################
	apt-get -y install tomcat7
	mkdir /software/pgstudio
	cd /software/pgstudio
	wget http://www.postgresqlstudio.org/?ddownload=838
	tar -xzvf index.html?ddownload=838
	cp pgstudio.war /var/lib/tomcat7/webapps/	

	######################
	# Install Vespucci repo
	######################
	
	# Note that we drop into the vespucci user now
	su -l ${USER_NAME}
	mkdir -p ~/Repositories/${USER}
	cd ~/Repositories/${USER}
	git clone git://github.com/karmel/${USER}.git
	git checkout v0.9
	
	echo "export CURRENT_PATH=/home/${USER}/Repositories/${USER}/${USER}/" >> ~/.bash_profile
	source ~/.bash_profile
	
	# And then continue with section I, part C above.
	
### III. Installing a new genome

If you are working with a genome other than hg19, mm9, or dm3, you can install the necessary reference databases for that genome as follows. For ease of demonstration, we will use the Rat genome, rn3.

1. Create and navigate to a new directory to hold the genome data.

	```
	mkdir ~/Repositories/vespucci/vespucci/vespucci/genomereference/pipeline/data/rn3
	cd ~/Repositories/vespucci/vespucci/vespucci/genomereference/pipeline/data/rn3
	```
	
1. Download the necessary chromosome, RefSeq, and ncRNA files:

	```
	wget http://hgdownload.soe.ucsc.edu/goldenPath/rnJun2003/database/refGene.txt.gz
	wget http://hgdownload.soe.ucsc.edu/goldenPath/rnJun2003/database/chromInfo.txt.gz
	wget http://www.ncrna.org/frnadb/catalog_taxonomy/files/rn3_bed.zip
	```
	
1. Unzip and extract necessary files. Note that you may also want to manually remove the "random" chromosomes from the chromInfo.txt file, depending on whether you are interested in that data.

	```
	gunzip *.gz
	unzip *.zip
	mv rn3_bed/rn3.bed .
	rm -rf rn3_bed
	```
	
1. Add the genome and chromosomes to the set of available options:

	```
	vim ~/Repositories/vespucci/vespucci/vespucci/config/current_settings.py
	```

	To that file, add to the GENOME_CHOICES dictionary, at line 20, the symbolic name, full name, and range of chromosome values, which in the case of rn3 with random chromosomes removed, is 1 - 22:

	```
	'rn3': {'name':'Rattus norvegicus', 'chromosomes': range(1,23)},
	```

1. Build the databases.

	```
	~/Repositories/vespucci/vespucci/vespucci/genomereference/pipeline/scripts/set_up_database.sh -g rn3 
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_refseq_database.sh -g rn3
	~/Repositories/vespucci/vespucci/vespucci/atlas/pipeline/scripts/set_up_database.sh -g rn3 -c default
	```

The new genome database is now installed, and you can continue loading your data as described beginning in section I, part D above.