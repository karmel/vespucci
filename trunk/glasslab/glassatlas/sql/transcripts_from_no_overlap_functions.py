'''
Created on Nov 12, 2010

@author: karmel

Convenience script for transcript functions.
'''
genome = 'gap3_100_'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.resize_transcripts(merged_trans glass_atlas_%s_%s.glass_transcript, trans glass_atlas_%s_%s.glass_transcript)
RETURNS glass_atlas_%s_%s.glass_transcript AS $$
BEGIN 
	-- Update the merged transcript
	merged_trans.transcription_start := (SELECT LEAST(merged_trans.transcription_start, trans.transcription_start));
	merged_trans.transcription_end := (SELECT GREATEST(merged_trans.transcription_end, trans.transcription_end));
	RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.get_average_tags(trans glass_atlas_%s_%s.glass_transcript)
RETURNS float AS $$
DECLARE
    sum integer;
    count integer;
BEGIN 
	sum := (SELECT SUM(tag_count) FROM glass_atlas_%s_%s.glass_transcript_source WHERE glass_transcript_id = trans.id);
	count := (SELECT COUNT(sequencing_run_id) FROM glass_atlas_%s_%s.glass_transcript_source WHERE glass_transcript_id = trans.id);
	RETURN sum::numeric/(count*(trans.transcription_end - trans.transcription_start)::numeric); 
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.create_transcript_cycles(chr_id integer, allowed_gap integer, scaling_factor float, allow_extended_gaps boolean)
RETURNS VOID AS $$
DECLARE
    processing boolean := true;
BEGIN
    WHILE processing = true
    LOOP
        processing := (SELECT glass_atlas_%s_%s.next_transcript_cycle(chr_id, allowed_gap, scaling_factor, allow_extended_gaps));
    END LOOP;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.next_transcript_cycle(chr_id integer, allowed_gap integer, scaling_factor float, allow_extended_gaps boolean)
RETURNS boolean AS $$
 DECLARE
    trans glass_atlas_%s_%s.glass_transcript;
    orig_id integer;
    closest_trans glass_atlas_%s_%s.glass_transcript;
    overlapping_length integer;
    max_gap integer;
    length_gap integer;
    limit_gap integer := 5000;
BEGIN
    trans := (EXECUTE 'SELECT' 
	            || ' transcript.*, source.sum::numeric/(source.count*(transcript.transcription_end ' 
	            || ' - transcript.transription_start)::numeric) as average_tags '
	        || ' FROM "glass_atlas_%s_%s_prep"."glass_transcript_' || chr_id ||'" transcript'
	        || ' JOIN (SELECT glass_transcript_id, SUM(tag_count) as sum, COUNT(sequencing_run_id) as count '
	            || ' FROM "glass_atlas_%s_%s_prep"."glass_transcript_source" '
	            || ' GROUP BY glass_transcript_id) source'
            || ' ON transcript.id = source.glass_transcript_id'
			|| ' WHERE processed = false AND strand = ' || strand
	        || ' ORDER BY transcription_start ASC LIMIT 1');
	
	IF trans IS NULL THEN RETURN false;
	END IF;
	
	-- Cast trans as proper type
	trans := trans::glass_atlas_%s_%s.glass_transcript;
	orig_id = trans.id;
	trans.id = NULL;
	
	-- Determine allowed gap
	max_gap := allowed_gap;
	IF allow_extended_gaps = true THEN
        -- Should this gap be considered in light of an overlapping sequence?
        overlapping_length := (SELECT (reg.transcription_end - reg.transcription_start) 
                            FROM genome_reference_mm9.sequence_transcription_region reg
                            WHERE reg.chromosome_id = chr_id
                                AND reg.strand = merged_trans.strand
                                AND reg.start_end OPERATOR(public.@>) 
                                    public.cube(merged_trans.transcription_end, trans.transcription_start)
                            ORDER BY (reg.transcription_end - reg.transcription_start) DESC
                            LIMIT 1);
        -- Allow up to a fifth of the sequence as a gap
        length_gap := (overlapping_length::float*.2)::integer;
        max_gap := (SELECT GREATEST(max_gap, length_gap));
        max_gap := (SELECT LEAST(max_gap, limit_gap));
    END IF;
    
    -- Scale gap according to current transcript average_tags
    max_gap := (max_gap * trans.average_tags * scaling_factor)::integer;
    
    -- Pull any transcripts that fall into the left hand radius of this transcript
    trans := SELECT glass_atlas_%s_%s.merge_close_transcripts(trans, max_gap, 'left');
    trans := SELECT glass_atlas_%s_%s.merge_close_transcripts(trans, max_gap, 'right');
    
    trans := (SELECT glass_atlas_%s_%s.insert_transcript(trans));
    UPDATE "glass_atlas_%s_%s_prep"."glass_transcript" SET processed = true WHERE id = orig_id;
    PERFORM glass_atlas_%s_%s.insert_transcript_source_records(trans);
    PERFORM glass_atlas_%s_%s.insert_associated_regions(trans);
    
    RETURN true;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.merge_close_transcripts(trans glass_atlas_%s_%s.glass_transcript, allowed_gap integer, side text)
RETURNS glass_atlas_%s_%s.glass_transcript AS $$
DECLARE
    side_op text;
    circ_center point;
    circ circle;
    close_trans glass_atlas_%s_%s.glass_transcript;
    merged_count integer := 0;
BEGIN 
    IF side = 'left' THEN 
        side_op = '&<'; -- Does not extend to the right of
        circ_center = trans.start_end[0];
    ELSE 
        side_op = '&>'; -- Does not extend to the left of
        circ_center = trans.start_end[1];
    END IF
	
	circ = '(' || circ_center || ', ' || allowed_gap || ')'::circle;
	FOR close_trans IN
	    EXECUTE 'SELECT' 
            || ' transcript.*::glass_atlas_%s_%s.glass_transcript '
        || ' FROM "glass_atlas_%s_%s_prep"."glass_transcript_' || trans.chromosome_id ||'" transcript'
        || ' WHERE strand = ' || trans.strand
            || ' AND start_end ' || side_op || trans.start_end 
            || ' AND start_end && ' || circ
        || ' ORDER BY transcription_start ASC'
    LOOP
        trans := (SELECT glass_atlas_%s_%s.resize_transcripts(trans, close_trans); 
        UPDATE "glass_atlas_%s_%s_prep"."glass_transcript" SET processed = true WHERE id = close_trans.id;
        merged_count := merged_count + 1;
    END LOOP
	RETURN trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.insert_transcript(rec glass_atlas_%s_%s.glass_transcript)
RETURNS glass_atlas_%s_%s.glass_transcript AS $$
DECLARE
    transcript glass_atlas_%s_%s.glass_transcript;
BEGIN
    -- Update record
    trans.average_tags = (SELECT glass_atlas_%s_%s.get_average_tags(trans));
    EXECUTE 'INSERT INTO glass_atlas_%s_%s.glass_transcript_' || rec.chromosome_id 
    || ' (chromosome_id, strand, transcription_start, transcription_end, average_tags, start_end, modified, created) '
    || 'VALUES (' || rec.chromosome_id || ',' || rec.strand || ','
        || rec.transcription_start || ',' || rec.transcription_end || ',' || rec.average_tags || ','
        || ' public.make_box(' || rec.transcription_start || ',' || rec.average_tags 
            || ',' ||  rec.transcription_end || ',' || rec.average_tags || '),'
        || ' modified = NOW(), created = NOW()) RETURNING *' INTO transcript;
    RETURN transcript;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.insert_transcript_source_records(trans glass_atlas_%s_%s.glass_transcript)
RETURNS VOID AS $$
BEGIN 
    INSERT INTO glass_atlas_%s_%s.glass_transcript_source
        (glass_transcript_id, sequencing_run_id, tag_count, gaps)
        SELECT trans.id, source.sequencing_run_id, 
            SUM(source.tag_count), COUNT(source.glass_transcript_id) - 1
        FROM (
            SELECT * FROM glass_atlas_%s_%s_prep.glass_transcript t
            JOIN glass_atlas_%s_%s_prep.glass_transcript_source s
            ON t.id = s.glass_transcript_id) source
        WHERE source.chromosome_id = trans.chromosome_id
            AND source.strand = trans.strand
            AND source.start_end <@ trans.start_end
        GROUP BY source.sequencing_run_id;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.insert_associated_transcript_regions(rec glass_atlas_%s_%s.glass_transcript)
RETURNS VOID AS $$
DECLARE
    region_types text[] := ARRAY['sequence','non_coding','conserved','patterned'];
    counter integer;
    cube text;
    table_type text;
BEGIN
    -- Associate any sequencing regions
    box = SELECT public.make_box(rec.transcription_start, 0, rec.transcription_end, 0);
    FOR counter IN array_lower(region_types,1)..array_upper(region_types,1)
    LOOP
        table_type := region_types[counter];
        EXECUTE 'INSERT INTO glass_atlas_%s_%s.glass_transcript_'
        || table_type || ' (glass_transcript_id, '
        || table_type || '_transcription_region_id, relationship)'
        || '(SELECT ' || rec.id || ', id, '
        || '(CASE WHEN start_end ~= ' || box || ' THEN '
        || ' glass_atlas_%s_%s.glass_transcript_transcription_region_relationship(''is equal to'') '
        || ' WHEN start_end <@ ' || box || ' THEN '
        || ' glass_atlas_%s_%s.glass_transcript_transcription_region_relationship(''contains'') '
        || ' WHEN start_end @> ' || box || ' THEN '
        || ' glass_atlas_%s_%s.glass_transcript_transcription_region_relationship(''is contained by'') '
        || 'ELSE glass_atlas_%s_%s.glass_transcript_transcription_region_relationship(''overlaps with'') END)'
        || ' FROM genome_reference_mm9.'
        || table_type || '_transcription_region '
        || ' WHERE chromosome_id = ' || rec.chromosome_id 
        || ' AND (strand IS NULL OR strand = ' || rec.strand || ')'
        || ' AND start_end && ' || box || ' )';
    END LOOP;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.update_transcribed_rna_records(chr_id integer)
RETURNS VOID AS $$
BEGIN 
    -- UPDATE redundant records: those that don't exist for the merge
    UPDATE glass_atlas_%s_%s.glass_transcribed_rna SET glass_transcript_id = NULL;
    UPDATE glass_atlas_%s_%s.glass_transcribed_rna rna
        SET glass_transcript_id = trans.id
        FROM glass_atlas_%s_%s.glass_transcribed trans
        WHERE rna.chromosome_id = chr_id
            AND trans.chromosome_id = chr_id
            AND rna.strand = trans.strand
            AND rna.start_end <@ public.make_box(trans.transcription_start, 0, trans.transcription_end, 0);
    UPDATE glass_atlas_%s_%s.glass_transcribed SET spliced = true
        WHERE id IN (SELECT glass_transcript_id FROM glass_atlas_%s_%s.glass_transcribed_rna);
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.calculate_scores(chr_id integer)
RETURNS VOID AS $$
BEGIN 
	EXECUTE 'UPDATE glass_atlas_%s_%s.glass_transcript_' || chr_id || ' transcript'
		|| ' SET score = derived.score '
		|| ' FROM (SELECT '
				|| ' transcript.id,' 
				|| ' (MAX(source.tag_count)::numeric*1000)/'
				|| ' (GREATEST(1000, (transcript.transcription_end - transcript.transcription_start)::numeric/1.5)) as score'
			|| ' FROM glass_atlas_%s_%s.glass_transcript_' || chr_id || ' transcript, '
				|| ' glass_atlas_%s_%s.glass_transcript_source source'
			|| ' WHERE source.glass_transcript_id = transcript.id'
				|| ' AND transcript.chromosome_id = ' || chr_id
				|| ' AND transcript.score IS NULL'
			|| ' GROUP BY transcript.id, transcript.transcription_end, transcript.transcription_start'
		|| ' ) derived'
		|| ' WHERE transcript.id = derived.id';

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.calculate_scores_sample(chr_id integer)
RETURNS VOID AS $$
BEGIN 
    -- Score = Ratio of max tag count for this transcript to
    -- expected tag count given the length of the region.
    -- NOTE: This assumes the expected_tag_count table is accurate and available.
	EXECUTE 'UPDATE glass_atlas_%s_%s.glass_transcript_' || chr_id || ' transcript'
		|| ' SET score = source.max_tags::numeric/(exp.tag_count * ' 
		    || ' ((transcript.transcription_end - transcript.transcription_start + 1)::numeric/exp.sample_size)) '
		|| ' FROM (SELECT '
				|| ' glass_transcript_id, MAX(tag_count) as max_tags '
			|| ' FROM glass_atlas_%s_%s.glass_transcript_source '
			|| ' GROUP BY glass_transcript_id) source, '
			|| ' glass_atlas_mm9.expected_tag_count exp'
		|| ' WHERE transcript.id = source.glass_transcript_id'
		    || ' AND transcript.chromosome_id = exp.chromosome_id'
		    || ' AND transcript.strand = exp.strand';

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome, cell_type]*61)

if __name__ == '__main__':
    print sql(genome, cell_type)
