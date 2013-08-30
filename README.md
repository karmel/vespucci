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



#### B. Setting up the Image

1. Once your instance has been launched, log in as root:

	ssh -i my_security_key.pem ubuntu@ec2-11-111-11-11.compute-1.amazonaws.com
	sudo su -

2. Make sure the instance is all up-to-date:

	apt-get update
	conda update

3. Change the vespucci user password, so that I can't get in:

	passwd vespucci

4. Change the PostgreSQL user passwords, so that I can't get in:

	

5. Change the git repository's record of the PostgreSQL password to match the one you set for vespucci_user:




#### C. Installing genome data

Note: skip this section if using an Image with the hg19 or mm9 genomes already installed.

#### D. Processing experimental data

#### E. Etc.

