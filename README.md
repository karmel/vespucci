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
* When in doubt, the Wizard's default option should suffice.

#### B. Setting up the Image

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

#### D. Processing experimental data

#### E. Etc.

