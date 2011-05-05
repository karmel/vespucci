def clean_bowtie(file_name, output_file=None):
	f = file(file_name)
	seen = {}
	output = output_file or (file_name + '.clean')
	o1 = file(output, 'w')
	for line in f.readlines():
		fields = line.split('\t')
		curr = fields[0]
		try:
			seen[curr] += 1 
		except KeyError:
			seen[curr] = 1
			if int(fields[6]) > 2: continue # More than three matches
			clean = fields[1:5]
			o1.write('\t'.join(clean) + '\n')
			
	o1.close()
	#o2 = file(file_name + '.dirty', 'w')
	#o2.write(''.join(dirty))
	#o2.close()
	return output

if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1: file_name = sys.argv[1]
	else: file_name = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/ThioMac/2011_03_08_Glass/wt_kla_rosi_2h/s_1_sequence.txt.CA.trimmed.mm9.41.align'
	clean_bowtie(file_name)

