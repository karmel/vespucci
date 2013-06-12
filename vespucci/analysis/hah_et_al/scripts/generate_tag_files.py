'''
Created on Jun 12, 2013

@author: karmel

Run with:

Create SQL queries, then run with:
for f in *.sql; do psql -U vespucci_user vespucci < $f > ${f}.txt; done;

Note that it helps to have a ~/.pgpass file setup.

'''

s = '''
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_12h_09_10_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
UNION
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_05_11_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
UNION
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_1h_09_10_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
UNION
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_6h_02_11_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
UNION
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_1h_02_11_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
UNION
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_6h_04_11_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
UNION
(select chr.name as "CHR", "start" as "START", "end" as "END", 
CASE WHEN strand = 0 THEN '+' ELSE '-' END as "STRAND"
FROM groseq.tag_wt_notx_12h_08_10_{0} tag
JOIN genome_reference_mm9.chromosome chr
ON tag.chromosome_id = chr.id)
ORDER BY "START" asc;
'''

for x in xrange(2,23): 
    f = open('chr{0}_tags.sql'.format(x), 'w+')
    f.write(s.format(x))