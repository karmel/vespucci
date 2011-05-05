'''
Created on Nov 12, 2010

@author: karmel

Convenience script for transcript functions.
'''
genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE TYPE glass_atlas_%s_%s_prep.glass_transcript_row AS ("chromosome_id" integer, "strand" smallint, 
	transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer, polya_count integer, ids integer[]);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.update_transcript_source_records(trans glass_atlas_%s_%s_prep.glass_transcript, old_id integer)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s_%s_prep.glass_transcript_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps),
			polya_count = (merged_assoc.polya_count + trans_assoc.polya_count)
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.get_density(trans glass_atlas_%s_%s_prep.glass_transcript, density_multiplier integer)
RETURNS float AS $$
DECLARE
    sum integer;
    count integer;
BEGIN 
    sum := (SELECT SUM(tag_count) - SUM(polya_count) FROM glass_atlas_%s_%s_prep.glass_transcript_source source
            JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = trans.id 
                AND run.use_for_scoring = true);
    count := (SELECT COUNT(sequencing_run_id) FROM glass_atlas_%s_%s_prep.glass_transcript_source source
            JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = trans.id AND run.use_for_scoring = true);
    RETURN GREATEST(0,(density_multiplier*sum::numeric)/(count*(trans.transcription_end - trans.transcription_start)::numeric)); 
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.get_allowed_edge(trans glass_atlas_%s_%s_prep.glass_transcript, density float, allowed_edge integer, scaling_factor integer, allow_extended_gaps boolean)
RETURNS float AS $$
DECLARE
    overlapping_edge float := NULL;
    edge float;
BEGIN 
    edge := allowed_edge;
    IF allow_extended_gaps = true THEN
        -- Allow longer edge (up to 20 percent of seq) if this sequence is contained in a RefSeq region
        overlapping_edge := (SELECT LEAST(reg.transcription_end - trans.transcription_end,
                                    (reg.transcription_end - reg.transcription_start)*.2) 
                        FROM genome_reference_mm9.sequence_transcription_region reg
                        WHERE reg.chromosome_id = trans.chromosome_id
                            AND reg.strand = trans.strand
                            AND reg.start_end @>
                                public.make_box(trans.transcription_start, 0, trans.transcription_end, 0)
                        ORDER BY LEAST(reg.transcription_end - trans.transcription_end,
                                    (reg.transcription_end - reg.transcription_start)*.2) DESC
                        LIMIT 1);
        edge := (SELECT GREATEST(allowed_edge, overlapping_edge));
    END IF;
    
    IF overlapping_edge IS NULL THEN
        edge := (SELECT allowed_edge*LEAST(density/scaling_factor::numeric, 1));
    END IF;
    
    RETURN edge;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_sequencing_run(chr_id integer, strand integer, source_t text, max_gap integer, tag_extension integer, start_end box)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
BEGIN 

    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_table(chr_id, strand, source_t, max_gap, tag_extension,'', false, false, start_end);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_existing(chr_id integer, strand integer, max_gap integer)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
BEGIN 
    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_table(chr_id, strand, 'glass_atlas_%s_%s_prep"."glass_transcript', max_gap, 0,'transcription_', true, NULL);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.determine_transcripts_from_table(
        chr_id integer, strand integer, source_t text, max_gap integer, 
        tag_extension integer, field_prefix text, span_repeats boolean, 
        start_end box)
RETURNS SETOF glass_atlas_%s_%s_prep.glass_transcript_row AS $$
 DECLARE
    max_chrom_pos bigint;
    rec record;
    start_end_clause text := '';
    row glass_atlas_%s_%s_prep.glass_transcript_row;
    last_start bigint := 0;
    last_end bigint := 0;
    tag_count integer := 0;
    polya_count integer := 0;
    gaps integer := 0;
    ids integer[];
    should_merge boolean := false;
    finish_row boolean := false;
    repeat_region integer;
BEGIN 
    -- Tag extension can exceed the boundaries of the chromosome if we are not careful.
    -- Make sure to keep lengths in range.
    max_chrom_pos := (SELECT (length - 1) FROM genome_reference_mm9.chromosome WHERE id = chr_id);
    
    -- IF a start_end is passed, use that to limit transcripts
    IF start_end IS NOT NULL THEN
        start_end_clause := ' and start_end && public.make_box(' || (start_end[0])[0] || ',0,' || (start_end[1])[0] || ',0) ';
    END IF;
    
	FOR rec IN 
		EXECUTE 'SELECT *, "' 
		|| field_prefix || 'start" as transcription_start, "' || field_prefix || 'end" as transcription_end '
		|| ' FROM "' || source_t || '_' || chr_id
		|| '" WHERE strand = ' || strand 
		|| start_end_clause
		|| ' ORDER BY ' || field_prefix || 'start ASC;'
		LOOP
		    -- The tags returned from the sequencing run are shorter than we know them to be biologically
		    -- We can therefore extend the mapped tag region by a set number of bp if an extension is passed in
		    IF tag_extension IS NOT NULL THEN
    		    IF strand = 0 THEN rec.transcription_end := rec.transcription_end + tag_extension;
    		    ELSE rec.transcription_start := rec.transcription_start - tag_extension;
    		    END IF;
		    END IF;
		    
		    -- Ensure values are in range
		    rec.transcription_start := (SELECT GREATEST(0,rec.transcription_start));
		    rec.transcription_end := (SELECT LEAST(max_chrom_pos, rec.transcription_end));
		    
			-- Initialize the start and end if necessary
			IF (last_start = 0) THEN 
				last_start := rec.transcription_start;
			END IF;
			IF (last_end = 0) THEN 
				last_end := rec.transcription_end;
			END IF;

			-- Include this tag if it overlaps or has < max_gap bp gap
			-- Else, this is a new transcript; close off the current and restart.
			IF ((last_end + max_gap) >= rec.transcription_start) THEN should_merge := true;
			ELSE
			    IF span_repeats = true THEN
    			    -- Should this gap be considered in light of an overlapping repeat region?
					-- Note: not strand specific!
                    EXECUTE 'SELECT reg.id ' 
                        || ' FROM genome_reference_mm9.patterned_transcription_region_' || chr_id || ' reg '
                            || ' WHERE reg.start_end @> '
                                    || ' ''((' || last_end || ', 0), (' || rec.transcription_start || ', 0))''::box '
                            || ' LIMIT 1' INTO repeat_region;
                    IF repeat_region IS NOT NULL THEN should_merge := true;
                    END IF;
                END IF;
			END IF;
			
			IF should_merge = true THEN
				tag_count := tag_count + 1;
				IF field_prefix = '' THEN
				    -- This is a tag row, with the polya t/f 
				    IF (rec.polya = true) THEN
				        polya_count := polya_count + 1;
    				END IF;
				END IF;
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
			row.polya_count := polya_count;
			row.gaps := gaps;
			row.ids := ids;
			
			IF finish_row THEN
				RETURN NEXT row;
				
				-- Restart vars for next loop
				last_start := rec.transcription_start;
				last_end := rec.transcription_end;
				tag_count := 1;
				IF field_prefix = '' THEN
				    polya_count := (SELECT CASE WHEN rec.polya = true THEN 1 ELSE 0 END);
				ELSE polya_count := 0;
				END IF;
				gaps := 0;
				ids := array[rec.id]::integer[];
				finish_row := false;
				
				-- Store row even if not done, in case this is the last loop	
				row.chromosome_id := chr_id;
				row.strand = strand;
				row.transcription_start := last_start;
				row.transcription_end := last_end;
				row.tag_count := tag_count;
				row.polya_count := polya_count;
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.save_transcripts_from_sequencing_run(
    seq_run_id integer, chr_id integer, source_t text, max_gap integer, 
    tag_extension integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer, 
    start_end box, one_strand integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_prep.glass_transcript_row;
	transcript glass_atlas_%s_%s_prep.glass_transcript;
	density float;
	scaling_factor text;
	strand_start integer := 0;
	strand_end integer := 1;
	use_for_scoring boolean;
 BEGIN
    IF edge_scaling_factor = 0 THEN scaling_factor := 'NULL';
    ELSE scaling_factor := edge_scaling_factor::text;
    END IF;
    
    -- Allow for strand selection
    IF one_strand IS NOT NULL THEN
        strand_start := one_strand;
        strand_end := one_strand;
    END IF; 
    
    -- Should this run have tags counted for density?
    use_for_scoring := (SELECT r.use_for_scoring FROM glass_atlas_mm9.sequencing_run r WHERE id = seq_run_id);
    
 	FOR strand IN strand_start..strand_end 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap, tag_extension, start_end)
		LOOP
			IF rec IS NOT NULL THEN
				-- Save the transcript.
				IF use_for_scoring = true THEN
				    density := (density_multiplier*(rec.tag_count - rec.polya_count)::numeric)/
				                    (rec.transcription_end - rec.transcription_start)::numeric;
				ELSE density := 0;
				END IF;
				
				EXECUTE 'INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_' || rec.chromosome_id
					|| ' ("chromosome_id", "strand", 
					"transcription_start", "transcription_end", 
					"start_end", "start_density")
					VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , 
					public.make_box(' || rec.transcription_start || ', 0, ' || rec.transcription_end || ', 0),
                    point(' || rec.transcription_start || ',' || density || ') 
                        ) RETURNING *' INTO transcript;
	            
				-- Save the record of the sequencing run source
				INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_source 
					("glass_transcript_id", "sequencing_run_id", "tag_count", "gaps", "polya_count") 
					VALUES (transcript.id, seq_run_id, rec.tag_count, rec.gaps, rec.polya_count);

			END IF;
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.save_transcripts_from_existing(chr_id integer, max_gap integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_prep.glass_transcript_row;
	transcript glass_atlas_%s_%s_prep.glass_transcript;
	old_id integer;
 BEGIN
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_existing(chr_id, strand, max_gap)
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.set_density(chr_id integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer, allow_extended_gaps boolean, null_only boolean)
RETURNS VOID AS $$
DECLARE
    where_clause text;
BEGIN
    IF null_only = true THEN where_clause := 'density_circle IS NULL';
    ELSE where_clause := '1=1';
    END IF;
    
    EXECUTE 'UPDATE glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' t 
             SET density_circle = circle(point(transcription_end,  
                glass_atlas_%s_%s_prep.get_density(t.*, ' || density_multiplier || ')::numeric), 
                glass_atlas_%s_%s_prep.get_allowed_edge(t.*,
                    glass_atlas_%s_%s_prep.get_density(t.*, ' || density_multiplier || ')::numeric,
                    ' || allowed_edge || ',' || edge_scaling_factor || ', ' || allow_extended_gaps || ')),
             start_density = point(transcription_start,glass_atlas_%s_%s_prep.get_density(t.*, '  
            || density_multiplier || ')::numeric) 
             WHERE ' || where_clause;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.remove_rogue_run(
    chr_id integer, max_gap integer, 
    tag_extension integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer)
RETURNS VOID AS $$
DECLARE
    row record;
    source record;
    matching integer;
    ids integer[] := array[]::integer[];
BEGIN
	FOR strand IN 0..1 
 	LOOP
    	FOR row IN 
	        EXECUTE 'SELECT dex.*, t.id as t_id, t.start_end as t_start_end 
	        FROM glass_atlas_fixup_thiomac_prep.glass_transcript_' || chr_id || ' dex
	        JOIN glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' t
	        ON dex.start_end && t.start_end
	        and dex.strand = ' || strand
			|| ' and t.strand = ' || strand
	    LOOP
	        IF row.chromosome_id IS NOT NULL THEN
	            FOR source IN 
	                SELECT * FROM glass_atlas_%s_%s_prep.glass_transcript_source s
	                JOIN glass_atlas_mm9.sequencing_run r
	                    ON s.sequencing_run_id = r.id
	                WHERE glass_transcript_id = row.t_id
	                    --AND sequencing_run_id != run_id
	            LOOP 
	                EXECUTE 'SELECT id FROM "' || trim(source.source_table) || '_' || chr_id ||'"
	                    WHERE start_end && public.make_box(' || row.transcription_start || ', 0, ' || row.transcription_end || ', 0) 
	                        AND strand = ' || row.strand || ' LIMIT 1' INTO matching;
	                IF matching IS NOT NULL THEN EXIT;
	                END IF;
	            END LOOP;
            
	            IF matching IS NULL THEN
	                FOR source IN 
	                    SELECT * FROM glass_atlas_%s_%s_prep.glass_transcript_source s
	                    JOIN glass_atlas_mm9.sequencing_run r
	                        ON s.sequencing_run_id = r.id
	                    WHERE glass_transcript_id = row.t_id
	                        -- AND sequencing_run_id != run_id
	                LOOP
	                    PERFORM glass_atlas_%s_%s_prep.save_transcripts_from_sequencing_run(
	                        source.sequencing_run_id, chr_id, trim(source.source_table),  max_gap, 
	                        tag_extension, allowed_edge, edge_scaling_factor, density_multiplier,
	                        row.t_start_end, row.strand);
	                END LOOP;
	                ids := ids || row.t_id;
	            END IF;
	        END IF;
		END LOOP;
    END LOOP;
    IF array_length(ids,1) > 0 THEN
        -- Next, remove all glass transcripts with the bad id
        EXECUTE 'DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || '
        WHERE id IN (' || array_to_string(ids, ',') || ')';
        
        -- And all bad source records
        EXECUTE 'DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_source
        WHERE glass_transcript_id IN (' || array_to_string(ids, ',') || ')';
    END IF;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome, cell_type]*54)

if __name__ == '__main__':
    print sql(genome, cell_type)
