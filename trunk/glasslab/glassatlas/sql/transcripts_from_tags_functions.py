'''
Created on Nov 12, 2010

@author: karmel

Convenience script for transcript functions.
'''
genome = 'gap3_200_0_1000'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE TYPE glass_atlas_%s_%s_prep.glass_transcript_row AS ("chromosome_id" integer, "strand" smallint, 
	transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer, ids integer[]);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.update_transcript_source_records(trans glass_atlas_%s_%s_prep.glass_transcript, old_id integer)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s_%s_prep.glass_transcript_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps)
		FROM glass_atlas_%s_%s_prep.glass_transcript_source trans_assoc
		WHERE merged_assoc.glass_transcript_id = trans.id
			AND trans_assoc.glass_transcript_id = old_id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s_%s_prep.glass_transcript_source
		SET glass_transcript_id = trans.id
		WHERE glass_transcript_id = old_id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s_%s_prep.glass_transcript_source
			WHERE glass_transcript_id = trans.id);
	-- Delete those that remain for the removed transcript.
	DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_source
		WHERE glass_transcript_id = old_id;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
			
CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.merge_transcripts(merged_trans glass_atlas_%s_%s_prep.glass_transcript, trans glass_atlas_%s_%s_prep.glass_transcript)
RETURNS glass_atlas_%s_%s_prep.glass_transcript AS $$
BEGIN 
	-- Update the merged transcript
	merged_trans.transcription_start := (SELECT LEAST(merged_trans.transcription_start, trans.transcription_start));
	merged_trans.transcription_end := (SELECT GREATEST(merged_trans.transcription_end, trans.transcription_end));
	merged_trans.strand := trans.strand;
	RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.get_average_tags(trans glass_atlas_%s_%s_prep.glass_transcript, density_multiplier integer)
RETURNS float AS $$
DECLARE
    sum integer;
    count integer;
BEGIN 
    sum := (SELECT SUM(tag_count) FROM glass_atlas_%s_%s_prep.glass_transcript_source WHERE glass_transcript_id = trans.id);
    count := (SELECT COUNT(sequencing_run_id) FROM glass_atlas_%s_%s_prep.glass_transcript_source WHERE glass_transcript_id = trans.id);
    RETURN (density_multiplier*sum::numeric)/(count*(trans.transcription_end - trans.transcription_start)::numeric); 
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.save_transcript(rec glass_atlas_%s_%s_prep.glass_transcript, density_multiplier integer)
RETURNS VOID AS $$
DECLARE 
    average_tags float;
BEGIN 	
	-- Update record
	--average_tags := (SELECT glass_atlas_%s_%s_prep.get_average_tags(rec, density_multiplier)); 
	EXECUTE 'UPDATE glass_atlas_%s_%s_prep.glass_transcript_' || rec.chromosome_id 
	|| ' SET'
		|| ' strand = ' || rec.strand || ','
		|| ' transcription_start = ' || rec.transcription_start || ','
		|| ' transcription_end = ' || rec.transcription_end || ','
		|| ' start_end = public.make_box(' || rec.transcription_start || ', 0' 
            || ',' ||  rec.transcription_end || ', 0),'
		|| ' processed = false'
	|| ' WHERE id = ' || rec.id;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_sequencing_run(chr_id integer, strand integer, source_t text, max_gap integer, tag_extension integer)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
BEGIN 

    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_table(chr_id, strand, source_t, max_gap, tag_extension,'', false, false);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_existing(chr_id integer, strand integer, max_gap integer, allow_extended_gaps boolean)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
BEGIN 
    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_table(chr_id, strand, 'glass_atlas_%s_%s_prep"."glass_transcript', max_gap, 0,'transcription_', true, allow_extended_gaps);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_table(chr_id integer, strand integer, source_t text, max_gap integer, tag_extension integer, field_prefix text, span_repeats boolean, allow_extended_gaps boolean)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
 DECLARE
    rec record;
    row glass_atlas_%s_%s_prep.glass_transcript_row;
    overlapping_length integer;
    length_gap integer;
    limit_gap integer := 1000;
    last_start bigint := 0;
    last_end bigint := 0;
    tag_count integer := 0;
    gaps integer := 0;
    ids integer[];
    should_merge boolean := false;
    finish_row boolean := false;
    repeat_region integer;
 BEGIN 
	FOR rec IN 
		EXECUTE 'SELECT *, "' 
		|| field_prefix || 'start" as transcription_start, "' || field_prefix || 'end" as transcription_end '
		|| ' FROM "' || source_t || '_' || chr_id
		|| '" WHERE strand = ' || strand || ' ORDER BY ' || field_prefix || 'start ASC;'
		LOOP
		    -- The tags returned from the sequencing run are shorter than we know them to be biologically
		    -- We can therefore extend the mapped tag region by a set number of bp if an extension is passed in
		    IF tag_extension IS NOT NULL THEN
    		    IF strand = 0 THEN rec.transcription_end = rec.transcription_end + tag_extension;
    		    ELSE rec.transcription_start := (SELECT LEAST(0,rec.transcription_start - tag_extension));
    		    END IF;
		    END IF;
		    
			-- Initialize the start and end if necessary
			IF (last_start = 0) THEN 
				last_start := rec.transcription_start;
			END IF;
			IF (last_end = 0) THEN 
				last_end := rec.transcription_end;
			END IF;

            -- Conditionally allow extended gaps in sequence regions
            IF allow_extended_gaps = true THEN
                -- Should this gap be considered in light of an overlapping sequence?
                overlapping_length := (SELECT (reg.transcription_end - reg.transcription_start) 
                                    FROM genome_reference_mm9.sequence_transcription_region reg
                                    WHERE reg.chromosome_id = chr_id
                                        AND reg.strand = rec.strand
                                        AND reg.start_end @>
                                            public.make_box(last_end, 0, rec.transcription_start, 0)
                                    ORDER BY (reg.transcription_end - reg.transcription_start) DESC
                                    LIMIT 1);
                -- Allow up to a fifth of the sequence as a gap
                length_gap := (overlapping_length::float*.2)::integer;
                max_gap := (SELECT GREATEST(max_gap, length_gap));
                max_gap := (SELECT LEAST(max_gap, limit_gap));
            END IF;
            
			-- Include this tag if it overlaps or has < max_gap bp gap
			-- Else, this is a new transcript; close off the current and restart.
			IF ((last_end + max_gap) >= rec.transcription_start) THEN should_merge := true;
			ELSE
			    IF span_repeats = true THEN
    			    -- Should this gap be considered in light of an overlapping repeat region?
                    EXECUTE 'SELECT reg.id ' 
                        || ' FROM genome_reference_mm9.patterned_transcription_region_' || chr_id || ' reg '
                            || ' WHERE reg.strand = ' || strand
                                || ' AND reg.start_end @> '
                                    || ' ''((' || last_end || ', 0), (' || rec.transcription_start || ', 0))''::box '
                            || ' LIMIT 1' INTO repeat_region;
                    IF repeat_region IS NOT NULL THEN should_merge := true;
                    END IF;
                END IF;
			END IF;
			
			IF should_merge = true THEN
				tag_count := tag_count + 1;
				IF (rec.transcription_start > last_end) THEN
					gaps := gaps + 1;
				END IF;
				last_start := (SELECT LEAST(last_start, rec.transcription_start));
				last_end := (SELECT GREATEST(last_end, rec.transcription_end));
				ids = ids || rec.id;
			ELSE
				finish_row := true;
			END IF;
			
			-- Reset should_merge
			should_merge := false;
			
			-- Store row even if not done, in case this is the last loop	
			row.chromosome_id := chr_id;
			row.strand = strand;
			row.transcription_start := last_start;
			row.transcription_end := last_end;
			row.tag_count := tag_count;
			row.gaps := gaps;
			row.ids := ids;
			
			IF finish_row THEN
				RETURN NEXT row;
				
				-- Restart vars for next loop
				last_start := rec.transcription_start;
				last_end := rec.transcription_end;
				tag_count := 1;
				gaps := 0;
				ids := array[rec.id]::integer[];
				finish_row := false;
				
				-- Store row even if not done, in case this is the last loop	
				row.chromosome_id := chr_id;
				row.strand = strand;
				row.transcription_start := last_start;
				row.transcription_end := last_end;
				row.tag_count := tag_count;
				row.gaps := gaps;
				row.ids := ids;
				
			END IF;
	END LOOP;
		
	-- One more left?
	RETURN NEXT row;
		
	-- And finally, return the set.
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.save_transcripts_from_sequencing_run(seq_run_id integer, chr_id integer, source_t text, max_gap integer, tag_extension integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_prep.glass_transcript_row;
	transcript glass_atlas_%s_%s_prep.glass_transcript;
	average_tags float;
	scaling_factor text;
 BEGIN
    IF edge_scaling_factor = 0 THEN scaling_factor := 'NULL';
    ELSE scaling_factor := edge_scaling_factor::text;
    END IF;
    
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap, tag_extension)
		LOOP
			IF rec IS NOT NULL THEN
				-- Save the transcript.
				average_tags := (density_multiplier*rec.tag_count::numeric)/(rec.transcription_end - rec.transcription_start)::numeric;
				EXECUTE 'INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_' || rec.chromosome_id
					|| ' ("chromosome_id", "strand", '
					|| ' "transcription_start", "transcription_end",' 
					|| ' "start_end", "density_circle", "start_density")'
					|| ' VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , '
					|| ' public.make_box(' || rec.transcription_start || ', 0' 
                        || ',' ||  rec.transcription_end || ', 0),'
                    || ' circle(point(' || rec.transcription_end || ',' || average_tags 
                        || '::float), ' || allowed_edge || '*LEAST(' || average_tags || '::numeric/' 
                        || scaling_factor || '::numeric,1)), '
                    || ' point(' || rec.transcription_start || ',' || average_tags || ') '
                    || ' ) RETURNING *' INTO transcript;
	
				-- Save the record of the sequencing run source
				INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_source 
					("glass_transcript_id", "sequencing_run_id", "tag_count", "gaps") 
					VALUES (transcript.id, seq_run_id, rec.tag_count, rec.gaps);

			END IF;
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.save_transcripts_from_existing(chr_id integer, max_gap integer, allow_extended_gaps boolean)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_prep.glass_transcript_row;
	transcript glass_atlas_%s_%s_prep.glass_transcript;
	old_id integer;
 BEGIN
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_existing(chr_id, strand, max_gap, allow_extended_gaps)
		LOOP
			IF rec IS NOT NULL AND rec.tag_count > 1 THEN		    
		        -- Save the transcript. 
				EXECUTE 'INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_' || rec.chromosome_id
					|| ' ("chromosome_id", "strand", '
					|| ' "transcription_start", "transcription_end",' 
					|| ' "start_end")'
					|| ' VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , '
					|| ' public.make_box(' || rec.transcription_start || ', 0' 
                        || ',' ||  rec.transcription_end || ', 0)'
                    || ' ) RETURNING *' INTO transcript;
                
                -- Remove existing records
                FOR old_id IN 
                    SELECT * FROM unnest(rec.ids)
                LOOP
                    PERFORM glass_atlas_%s_%s_prep.update_transcript_source_records(transcript, old_id);
                END LOOP;
                EXECUTE 'DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_' || rec.chromosome_id
                    || ' WHERE id IN (' || array_to_string(rec.ids,',') || ')';
            END IF; 
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.set_average_tags(chr_id integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer, null_only boolean)
RETURNS VOID AS $$
DECLARE
    where_clause text;
    scaling_factor text;
BEGIN
    IF null_only = true THEN where_clause := 'density_circle IS NULL';
    ELSE where_clause := '1=1';
    END IF;
    
    IF edge_scaling_factor = 0 THEN scaling_factor := 'NULL';
    ELSE scaling_factor := edge_scaling_factor::text;
    END IF;
    
    EXECUTE 'UPDATE glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' t '
        || ' SET density_circle = circle(point(transcription_end, ' 
            || ' glass_atlas_%s_%s_prep.get_average_tags(t.*, ' || density_multiplier || ')::numeric), '
            || allowed_edge || '*LEAST(glass_atlas_%s_%s_prep.get_average_tags(t.*, ' 
                || density_multiplier || ')::numeric/' || scaling_factor || '::numeric, 1)),'
        || ' start_density = point(transcription_start,glass_atlas_%s_%s_prep.get_average_tags(t.*, ' 
            || density_multiplier || ')::numeric) '
        || ' WHERE ' || where_clause;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome, cell_type]*48)

if __name__ == '__main__':
    print sql(genome, cell_type)
