def sam_to_bowtie(file_name, unique=True, output_file=None):
	'''
	Sample bowtie::
	
		0	+	chr18	78148411	AACCATTAGGAGACC	IIIIIIIIIIIIIII	1	

	and equivalent SAM::
	
		@HD	VN:1.0	SO:unsorted
		@SQ	SN:chr1	LN:197195432
		@SQ	SN:chr2	LN:181748087
		@SQ	SN:chr3	LN:159599783
		@SQ	SN:chr4	LN:155630120
		@SQ	SN:chr5	LN:152537259
		@SQ	SN:chr6	LN:149517037
		@SQ	SN:chr7	LN:152524553
		@SQ	SN:chr8	LN:131738871
		@SQ	SN:chr9	LN:124076172
		@SQ	SN:chr10	LN:129993255
		@SQ	SN:chr11	LN:121843856
		@SQ	SN:chr12	LN:121257530
		@SQ	SN:chr13	LN:120284312
		@SQ	SN:chr14	LN:125194864
		@SQ	SN:chr15	LN:103494974
		@SQ	SN:chr16	LN:98319150
		@SQ	SN:chr17	LN:95272651
		@SQ	SN:chr18	LN:90772031
		@SQ	SN:chr19	LN:61342430
		@SQ	SN:chrX	LN:166650296
		@SQ	SN:chrY	LN:15902555
		@SQ	SN:chrM	LN:16299
		@PG	ID:Bowtie	VN:0.12.7	CL:"/Volumes/Unknowme/bowtie/bowtie-0.12.7/bowtie mm9 -S -c aaccattaggagacc"
		0	0	chr18	78148412	255	15M	*	0	0	AACCATTAGGAGACC	IIIIIIIIIIIIIII	XA:i:0	MD:Z:15	NM:i:0

	Note that SAM is 1-indexed instead of 0-indexed like the Bowtie output.
	
	'''
	f = file(file_name)
	output = output_file or (file_name.replace('sam','align') + '.clean')
	o1 = file(output, 'w')
	
	for line in f:
		fields = line.split('\t')
		if fields[0][0] == '@': continue # Header line
		if int(fields[1]) == 4: continue # Read did not match
		if unique:
			if int(fields[1]) == 0: strand = '+'
			elif int(fields[1]) == 16: strand = '-'
			else: raise Exception('Did not recognize flag %s in line: \n%s' % (fields[1], line))
			
			pos = int(fields[3]) - 1
			
			to_write = map(str, [strand, fields[2], pos, fields[9]]) # Strand, chr, position, matched sequence
			write_line(to_write, o1)
		else:
			# Does SAM report multiple alignments? Unclear from Bowtie help.
			# Because we're Bowtie-ing only for unique reads at this point, we will not handle this case.
			raise Exception('This script does not handle the filtering of non-unique reads. Please re-Bowtie to get unique reads.')

	o1.close()
	return output

def write_line(line_to_write, output):
	if line_to_write: output.write('\t'.join(line_to_write) + '\n')
	
if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1: file_name = sys.argv[1]
	else: file_name = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/ThioMac/2011_03_08_Glass/wt_kla_rosi_2h/s_1_sequence.txt.CA.trimmed.mm9.41.align'
	if len(sys.argv) > 2 and sys.argv[2] == 'not_unique': 
		# This flag indicates bowtie has already been configured to only return unique matches; no need to re-ensure
		unique = False
	else: unique = True
	sam_to_bowtie(file_name, unique=unique)

