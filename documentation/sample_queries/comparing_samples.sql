---------------------------------------------------------
-- Get RPKM for transcripts within a single run:
-- In this case, the run that was loaded in to groseq"."tag_wt_notx_12h_1
-- Note that you can view all runs loaded in 
-- using the genome_reference_mm9.sequencing_run table
SELECT rpkm(t, s1.tag_count, run1.total_tags) as rpkm1, 
t.id
FROM atlas_mm9_default.atlas_transcript t

-- Join in the sequencing run you want
JOIN atlas_mm9_default.atlas_transcript_source s1
ON t.id = s1.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run1
ON s1.sequencing_run_id = run1.id
AND run1.source_table = 'groseq"."tag_wt_notx_12h_1' -- Note the quotation mark style here

WHERE t.score >= 1
AND t.parent_id IS NULL;


---------------------------------------------------------
-- Get RPKM for transcripts in multiple runs
SELECT rpkm(t, s1.tag_count, run1.total_tags) as rpkm1, 
rpkm(t, s2.tag_count, run2.total_tags) as rpkm2
FROM atlas_mm9_default.atlas_transcript t

JOIN atlas_mm9_default.atlas_transcript_source s1
ON t.id = s1.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run1
ON s1.sequencing_run_id = run1.id
AND run1.source_table = 'groseq"."tag_wt_notx_12h_1'

JOIN atlas_mm9_default.atlas_transcript_source s2
ON t.id = s2.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run2
ON s2.sequencing_run_id = run2.id
AND run2.source_table = 'groseq"."tag_wt_notx_12h_2'

WHERE t.score >= 1
AND t.parent_id IS NULL;


---------------------------------------------------------
-- Get log fold change between runs
SELECT log(2,rpkm(t, s1.tag_count, run1.total_tags)/rpkm(t, s2.tag_count, run2.total_tags)) as log_fold_change,
rpkm(t, s1.tag_count, run1.total_tags) as rpkm1, 
rpkm(t, s2.tag_count, run2.total_tags) as rpkm2
FROM atlas_mm9_default.atlas_transcript t

JOIN atlas_mm9_default.atlas_transcript_source s1
ON t.id = s1.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run1
ON s1.sequencing_run_id = run1.id
AND run1.source_table = 'groseq"."tag_wt_notx_12h_1'

JOIN atlas_mm9_default.atlas_transcript_source s2
ON t.id = s2.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run2
ON s2.sequencing_run_id = run2.id
AND run2.source_table = 'groseq"."tag_wt_notx_12h_2'

WHERE t.score >= 1
AND t.parent_id IS NULL;


---------------------------------------------------------
-- Get RefSeq transcripts with more than 2-fold change
SELECT refseq.sequence_identifier,
log(2,rpkm(t, s1.tag_count, run1.total_tags)/rpkm(t, s2.tag_count, run2.total_tags)) as log_fold_change,
rpkm(t, s1.tag_count, run1.total_tags) as rpkm1, 
rpkm(t, s2.tag_count, run2.total_tags) as rpkm2
FROM atlas_mm9_default.atlas_transcript t

-- Get RefSeq info
JOIN atlas_mm9_default.atlas_transcript_sequence seq
ON t.id = seq.atlas_transcript_id
JOIN genome_reference_mm9.sequence_transcription_region reg
ON seq.sequence_transcription_region_id = reg.id
JOIN genome_reference_mm9.sequence_identifier refseq
ON reg.sequence_identifier_id = refseq.id

JOIN atlas_mm9_default.atlas_transcript_source s1
ON t.id = s1.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run1
ON s1.sequencing_run_id = run1.id
AND run1.source_table = 'groseq"."tag_wt_notx_12h_1'

JOIN atlas_mm9_default.atlas_transcript_source s2
ON t.id = s2.atlas_transcript_id
JOIN genome_reference_mm9.sequencing_run run2
ON s2.sequencing_run_id = run2.id
AND run2.source_table = 'groseq"."tag_wt_notx_12h_2'


WHERE t.score >= 1
AND t.parent_id IS NULL
AND abs(log(2,rpkm(t, s1.tag_count, run1.total_tags)/rpkm(t, s2.tag_count, run2.total_tags))) > 1;