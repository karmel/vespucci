import sys
#if len(sys.argv) > 1: dir_name = sys.argv[1]
#else: dir_name = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/ThioMac/2011_03_08_Glass/wt_kla_rosi_2h/tags_wt_kla_rosi_2h/'
if len(sys.argv) > 1: file_name = sys.argv[1]
else: file_name = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/ThioMac/2011_03_08_Glass/wt_kla_rosi_2h/s_1_sequence.txt.CA.trimmed.mm9.41.align'

"""
chr = {}
chr_names = [str(x) for x in xrange(1,20)] + ['M','X','Y']
for x in chr_names:
	starts = [line.split('\t')[2] for line in file(dir_name + '/chr%s.tags.tsv' % x).readlines()]
	chr['chr' + x] = {}
	for start in starts:
		start = start[:-2]
		try: chr['chr' + x][start] += 1
		except KeyError: chr['chr' + x][start] = 1
"""
f = file(file_name)
clean = []
dirty = []
seen = {}
for line in f.readlines():
	fields = line.split('\t')
	curr = fields[0]
	try:
		seen[curr] += 1 
		dirty.append(line)
	except KeyError:
		seen[curr] = 1
		if len(fields[4]) > 16:
			clean.append(line)
		else: dirty.append(line)
o1 = file(file_name + '.clean', 'w')
o1.write(''.join(clean))
o1.close()
o2 = file(file_name + '.dirty', 'w')
o2.write(''.join(dirty))
o2.close()