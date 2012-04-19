def clean_unsorted_bowtie(file_name, unique=True, output_file=None):
	f = file(file_name)
	seen = {}
	
	for line in f:
		if not line.strip('\n'): 
			print 'blank'
			continue
		fields = line.split('\t')
		curr = fields[0].split()[0]
		
		try:
			seen[curr] += 1
			print curr
		except KeyError:
			seen[curr] = 1
			
		
def write_line(line_to_write, output):
	if line_to_write: output.write('\t'.join(line_to_write) + '\n')
	
if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1: file_name = sys.argv[1]
	else: file_name = '/Users/karmel/GlassLab/Data/Sequencing/GroSeq/BMDC/2012_04_05/Sample_karmel1/nod_notx_slow_diabetic/karmel1_NoIndex_L001_R1.fastq.trimmed.TG.mm9.50.align.unique'
	if len(sys.argv) > 2 and sys.argv[2] == 'not_unique': 
		# This flag indicates bowtie has already been configured to only return unique matches; no need to re-ensure
		unique = False
	else: unique = True
	clean_unsorted_bowtie(file_name, unique=unique)

