'''
Created on Jun 12, 2013

@author: karmel

Run with:

Create SQL queries, then run with:
for f in *.sql; do psql -U vespucci_user vespucci < $f > ${f}.txt; done;
for f in *.sql.txt; do sed -i '.clean' -e 's/ //g' $f; done;
for f in *.clean; do sed -i  -e 's/|/  /g' $f; done;
# Change spaces in next line to tabs!
echo  'CHR START END STRAND' >  notx_tags.txt
for f in *.clean; do sed '$d' < $f | sed '$d' | tail -n +3 >> notx_tags.txt; done;
rm *.txt

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