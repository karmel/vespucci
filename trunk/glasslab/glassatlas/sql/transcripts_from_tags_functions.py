'''
Created on Nov 12, 2010

@author: karmel

Convenience script for transcript functions.
'''
genome = 'gap3_100_10_1000'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE TYPE glass_atlas_%s_%s_prep.glass_transcript_row AS ("chromosome_id" integer, "strand" smallint, 
	transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer);
CREATE TYPE glass_atlas_%s_%s_prep.glass_transcript_pair AS ("t1" glass_atlas_%s_%s_prep.glass_transcript, "t2" glass_atlas_%s_%s_prep.glass_transcript);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.update_transcript_source_records(merged_trans glass_atlas_%s_%s_prep.glass_transcript, trans glass_atlas_%s_%s_prep.glass_transcript)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s_%s_prep.glass_transcript_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps)
		FROM glass_atlas_%s_%s_prep.glass_transcript_source trans_assoc
		WHERE merged_assoc.glass_transcript_id = merged_trans.id
			AND trans_assoc.glass_transcript_id = trans.id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s_%s_prep.glass_transcript_source
		SET glass_transcript_id = merged_trans.id
		WHERE glass_transcript_id = trans.id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s_%s_prep.glass_transcript_source
			WHERE glass_transcript_id = merged_trans.id);
	-- Delete those that remain for the removed transcript.
	DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_source
		WHERE glass_transcript_id = trans.id;
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
	average_tags := (SELECT glass_atlas_%s_%s_prep.get_average_tags(rec, density_multiplier)); 
	EXECUTE 'UPDATE glass_atlas_%s_%s_prep.glass_transcript_' || rec.chromosome_id 
	|| ' SET'
		|| ' strand = ' || rec.strand || ','
		|| ' transcription_start = ' || rec.transcription_start || ','
		|| ' transcription_end = ' || rec.transcription_end || ','
		|| ' start_end = public.make_box(' || rec.transcription_start || ', 0' 
            || ',' ||  rec.transcription_end || ', 0),'
        || ' start_end_density = public.make_box(' || rec.transcription_start || ',' || average_tags 
            || ',' ||  rec.transcription_end || ',' || average_tags || '),'
		|| ' processed = false'
	|| ' WHERE id = ' || rec.id;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_sequencing_run(chr_id integer, strand integer, source_t text, max_gap integer, tag_extension integer)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
 DECLARE
   rec record;
   row glass_atlas_%s_%s_prep.glass_transcript_row;
   last_start bigint := 0;
   last_end bigint := 0;
   tag_count integer := 0;
   gaps integer := 0;
   finish_row boolean := false;
   strand_query text := '';
 BEGIN 
	FOR rec IN 
		EXECUTE 'SELECT * FROM "'
		|| source_t || '_' || chr_id
		|| '" WHERE strand = ' || strand || ' ORDER BY start ASC;'
		LOOP
		    -- The tags returned from the sequencing run are shorter than we know them to be biologically
		    -- We can therefore extend the mapped tag region by a set number of bp if an extension is passed in
		    IF tag_extension IS NOT NULL THEN
    		    IF strand = 0 THEN rec."end" = rec."end" + tag_extension;
    		    ELSE rec."start" = rec."start" - tag_extension;
    		    END IF;
		    END IF;
		    
			-- Initialize the start and end if necessary
			IF (last_start = 0) THEN 
				last_start := rec."start";
			END IF;
			IF (last_end = 0) THEN 
				last_end := rec."end";
			END IF;

			-- Include this tag if it overlaps or has < max_gap bp gap
			-- Else, this is a new transcript; close off the current and restart.
			IF ((last_end + max_gap) >= rec."start") THEN
				tag_count := tag_count + 1;
				IF (rec."start" > last_end) THEN
					gaps := gaps + 1;
				END IF;
				last_start := (SELECT LEAST(last_start, rec."start"));
				last_end := (SELECT GREATEST(last_end, rec."end"));
			ELSE
				finish_row := true;
			END IF;
			
			-- Store row even if not done, in case this is the last loop	
			row.chromosome_id := chr_id;
			row.strand = strand;
			row.transcription_start := last_start;
			row.transcription_end := last_end;
			row.tag_count := tag_count;
			row.gaps := gaps;
			
			IF finish_row THEN
				RETURN NEXT row;
				
				-- Restart vars for next loop
				last_start := rec.start;
				last_end := rec."end";
				tag_count := 1;
				gaps := 0;
				finish_row := false;
				
				-- Store row even if not done, in case this is the last loop	
				row.chromosome_id := chr_id;
				row.strand = strand;
				row.transcription_start := last_start;
				row.transcription_end := last_end;
				row.tag_count := tag_count;
				row.gaps := gaps;
				
			END IF;
	END LOOP;
		
	-- One more left?
	RETURN NEXT row;
		
	-- And finally, return the set.
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.save_transcripts_from_sequencing_run(seq_run_id integer, chr_id integer, source_t text, max_gap integer, tag_extension integer, density_multiplier integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_prep.glass_transcript_row;
	transcript glass_atlas_%s_%s_prep.glass_transcript;
	average_tags float;
 BEGIN
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
					|| ' "start_end", "start_end_density")'
					|| ' VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , '
					|| ' public.make_box(' || rec.transcription_start || ', 0' 
                        || ',' ||  rec.transcription_end || ', 0),'
                    || ' public.make_box(' || rec.transcription_start || ',' || average_tags 
                        || ',' ||  rec.transcription_end || ',' || average_tags || ')'
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.stitch_transcripts_together(chr_id integer, allowed_gap integer, density_multiplier integer, allow_extended_gaps boolean)
RETURNS VOID AS $$
 DECLARE
    trans glass_atlas_%s_%s_prep.glass_transcript;
    merged_trans glass_atlas_%s_%s_prep.glass_transcript;
    repeat_region integer;
    overlapping_length integer;
    should_merge boolean := false;
    merged boolean := false;
    max_gap integer;
    length_gap integer;
    limit_gap integer := 1000;
BEGIN
    -- Ignore any RefSeq boundaries
	FOR strand IN 0..1 
 	LOOP

	    FOR trans IN 
	        EXECUTE 'SELECT' 
	            || ' transcript.* '
	        || ' FROM "glass_atlas_%s_%s_prep"."glass_transcript_' || chr_id ||'" transcript'
			|| ' WHERE strand = ' || strand
	        || ' ORDER BY transcription_start ASC '
	    LOOP
	        max_gap := allowed_gap;
	        IF merged_trans IS NULL THEN merged_trans := trans;
	        ELSE
	            should_merge := false;
	            -- Does this transcript connect?
	            IF (merged_trans.transcription_end >= trans.transcription_start) THEN should_merge := true;
	            ELSE
                    -- Should this gap be considered in light of an overlapping repeat region?
                    EXECUTE 'SELECT reg.id ' 
                        || ' FROM genome_reference_mm9.patterned_transcription_region_' || chr_id || ' reg '
                            || ' WHERE reg.strand = ' || merged_trans.strand
                                || ' AND reg.start_end @> '
                                    || ' public.make_box(' || merged_trans.transcription_end || ', 0, ' || trans.transcription_start || ', 0) '
                            || ' LIMIT 1' INTO repeat_region;
                    IF repeat_region IS NOT NULL THEN should_merge := true;
	                ELSE
    	                IF allow_extended_gaps = true THEN
                            -- Should this gap be considered in light of an overlapping sequence?
                            overlapping_length := (SELECT (reg.transcription_end - reg.transcription_start) 
                                                FROM genome_reference_mm9.sequence_transcription_region reg
                                                WHERE reg.chromosome_id = chr_id
                                                    AND reg.strand = merged_trans.strand
                                                    AND reg.start_end @>
                                                        public.make_box(merged_trans.transcription_end, 0, trans.transcription_start, 0)
                                                ORDER BY (reg.transcription_end - reg.transcription_start) DESC
                                                LIMIT 1);
                            -- Allow up to a fifth of the sequence as a gap
                            length_gap := (overlapping_length::float*.2)::integer;
                            max_gap := (SELECT GREATEST(max_gap, length_gap));
                            max_gap := (SELECT LEAST(max_gap, limit_gap));
                        END IF;
                    END IF;
	                IF (trans.transcription_start - merged_trans.transcription_end) <= max_gap THEN should_merge := true;
	                END IF;
	            END IF;
            
	            IF should_merge = true
	                THEN 
	                    merged_trans := (SELECT glass_atlas_%s_%s_prep.merge_transcripts(merged_trans, trans));
	                    -- Delete/update old associations
	                    PERFORM glass_atlas_%s_%s_prep.update_transcript_source_records(merged_trans, trans);
	                    EXECUTE 'DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_' || trans.chromosome_id || ' WHERE id = ' || trans.id;
	                    merged := true;
	            ELSE
	                -- We have reached a gap; close off any open merged_transcripts
	                IF merged THEN
	                    PERFORM glass_atlas_%s_%s_prep.save_transcript(merged_trans, density_multiplier);
	                END IF;
	                -- And reset the merged transcript
	                merged_trans := trans;
	                merged := false;
	            END IF;
	        END IF;
	    END LOOP;
    
	    -- We may have one final merged transcript awaiting a save:
	    IF merged THEN
	        PERFORM glass_atlas_%s_%s_prep.save_transcript(merged_trans, density_multiplier);
	    END IF;
	    -- And reset the merged transcript
	    merged_trans := NULL;
	    merged := false;
	END LOOP;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome, cell_type]*42)

if __name__ == '__main__':
    print sql(genome, cell_type)
