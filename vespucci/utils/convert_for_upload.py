import sys
import subprocess


class TagFileConverter(object):
	def guess_file_type(self, file_name='', file_type=''):
		'''
		Use extensions to guess file name and perform the necessary conversion.
		'''
		file_type = (file_type or '').lower()
		# Is this a BAM file? Convert first to SAM.

		if file_type == 'bam' or file_name[-4:].lower() == '.bam':
			file_name = self.bam_to_sam(file_name)
			file_name = self.convert_sam_file(file_name)
		# Is this a SAM file? Convert to 4 column format.
		elif file_type == 'sam' or file_name[-4:].lower() == '.sam':
			file_name = self.convert_sam_file(file_name)
		elif file_type == 'bowtie':
			file_name = self.convert_bowtie_file(file_name)

		return file_name

	def bam_to_sam(self, file_name, output_file=None):
		'''
		Use samtools to convert BAM to SAM first if necessary.
		'''
		output = output_file or (file_name[-4:] == '.bam' \
								and file_name.replace('bam', 'sam')) \
				or (file_name + '.sam')
		subprocess.check_call('samtools view -h -o {0} {1}'.format(
														output, file_name),
							shell=True)
		return output

	def convert_sam_file(self, file_name, output_file=None, min_map_quality=10):
		'''
		Sample output::
		
			+	chr18	78148411	AACCATTAGGAGACC	
	
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
		output = output_file or (file_name + '.4column')
		o1 = file(output, 'w')

		for line in f:
			fields = line.split('\t')

			try:
				if fields[0][0] == '@': continue  # Header line
				if int(fields[1]) == 4: continue  # Read did not match

				bitwise_flag = int(fields[1])
				if bitwise_flag & 0x100: continue  # Not primary alignment
				# Filter for quality
				if min_map_quality and int(fields[4]) < min_map_quality: continue

				strand = '+'
				if bitwise_flag & 0x10: strand = '-'


				pos = int(fields[3]) - 1

				# Strand, chr, position, matched sequence
				to_write = map(str, [strand, fields[2], pos, fields[9]])
				self.write_line(to_write, o1)
			except IndexError:
				# Corrupted line. Skip.
				print('Caught index error with line:\n{}'.format(line))
				continue
		o1.close()
		return output

	def convert_bowtie_file(self, file_name, output_file=None):
		'''
		Used for files with (obsolete) six-column bowtie output.
		Generally, SAM is preferred at this point, even by Bowtie.
		'''
		f = file(file_name)
		output = output_file or (file_name + '.4column')
		o1 = file(output, 'w')

		for line in f:
			fields = line.split('\t')
			if len(fields) < 6:
				print('Skipping line:\n' + line)
				continue
			self.write_line(fields[1:5], o1)

		o1.close()
		return output

	def write_line(self, line_to_write, output):
		if line_to_write:
			output.write('\t'.join(line_to_write).strip('\n') + '\n')


if __name__ == '__main__':
	try: file_name = sys.argv[1]
	except IndexError:
		raise Exception('Please provide a file name for your mapped tag file. '\
					+ 'It should be a BOWTIE, BAM, or SAM file.')
	converter = TagFileConverter()
	output_file = converter.guess_file_type(file_name)

	print('Converted {0} as best as possible.'.format(output_file))
