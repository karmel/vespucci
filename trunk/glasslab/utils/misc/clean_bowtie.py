WHOLE_LINE = True

def clean_bowtie(file_name, unique=True, output_file=None):
	f = file(file_name)
	seen = {}
	output = output_file or (WHOLE_LINE and file_name + '.unique') or (file_name + '.clean')
	o1 = file(output, 'w')
	
	line_to_write = None
	mismatches = None
	for line in f:
		fields = line.split('\t')
		if len(fields) < 6: 
			print 'Skipping line:\n%s' % line
			continue
		if unique:
			write_line(fields[1:5], o1)
		else:
			curr = fields[0]
			try:
				seen[curr] += 1
				# This read maps in multiple places.
				# Only use if mismatches are more in this than the original line.
				curr_mismatches = fields[7].strip('\n') and len(fields[7].split(',')) or 0
				if mismatches != None and mismatches < curr_mismatches: 
					write_line(line_to_write, o1)
				
				# Otherwise, don't write the previous occurrence to file. 
				line_to_write = None 
				mismatches = None 
			except KeyError:
				seen[curr] = 1
			
				# This line is not a repeat; write the last line, if it exists
				write_line(line_to_write, o1)
			
				# Store this line to write if the next is not a duplicate
				if WHOLE_LINE: line_to_write = fields
				else: line_to_write = fields[1:5]
				
				# Keep track of mismatches; if another match has more, we can still use this line.
				# Mismatches come as: "1:A>T,2:A>T"; no mismatches at all is an empty string.
				mismatches = fields[7].strip('\n') and len(fields[7].split(',')) or 0

	# If there is one line left, write it:
	write_line(line_to_write, o1)
	
	o1.close()
	#o2 = file(file_name + '.dirty', 'w')
	#o2.write(''.join(dirty))
	#o2.close()
	return output

def write_line(line_to_write, output):
	if line_to_write: output.write('\t'.join(line_to_write).strip('\n') + '\n')
	
if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1: file_name = sys.argv[1]
	else: file_name = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/ThioMac/2011_03_08_Glass/wt_kla_rosi_2h/s_1_sequence.txt.CA.trimmed.mm9.41.align'
	if len(sys.argv) > 2 and sys.argv[2] == 'not_unique': 
		# This flag indicates bowtie has already been configured to only return unique matches; no need to re-ensure
		unique = False
	else: unique = True
	clean_bowtie(file_name, unique=unique)

