'''
Created on Nov 12, 2010

@author: karmel

** DEPRECATED **

'''
genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE TYPE glass_atlas_%s_%s_rna.glass_transcribed_rna_row AS ("chromosome_id" integer, "strand" smallint, 
    transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer, polya_count integer, ids integer[]);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.update_transcribed_rna_source_records(trans glass_atlas_%s_%s_rna.glass_transcribed_rna, old_id integer)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s_%s_rna.glass_transcribed_rna_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps),
			polya_count = (merged_assoc.polya_count + trans_assoc.polya_count)
		FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_source trans_assoc
		WHERE merged_assoc.glass_transcribed_rna_id = trans.id
			AND trans_assoc.glass_transcribed_rna_id = old_id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s_%s_rna.glass_transcribed_rna_source
		SET glass_transcribed_rna_id = trans.id
		WHERE glass_transcribed_rna_id = old_id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_source
			WHERE glass_transcribed_rna_id = trans.id);
	-- Delete those that remain for the removed transcribed_rna.
	DELETE FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_source
		WHERE glass_transcribed_rna_id = old_id;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
			
CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.merge_transcribed_rnas(merged_trans glass_atlas_%s_%s_rna.glass_transcribed_rna, trans glass_atlas_%s_%s_rna.glass_transcribed_rna)
RETURNS glass_atlas_%s_%s_rna.glass_transcribed_rna AS $$
BEGIN 
	-- Update the merged transcribed_rna
	merged_trans.transcription_start := (SELECT LEAST(merged_trans.transcription_start, trans.transcription_start));
	merged_trans.transcription_end := (SELECT GREATEST(merged_trans.transcription_end, trans.transcription_end));
	merged_trans.strand := trans.strand;
	RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.save_transcribed_rna(rec glass_atlas_%s_%s_rna.glass_transcribed_rna, density_multiplier integer)
RETURNS VOID AS $$
BEGIN 	
	-- Update record
	EXECUTE 'UPDATE glass_atlas_%s_%s_rna.glass_transcribed_rna_' || rec.chromosome_id 
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_sequencing_run(chr_id integer, strand integer, source_t text, max_gap integer, tag_extension integer, start_end box)
RETURNS SETOF glass_atlas_%s_%s_rna.glass_transcribed_rna_row AS $$
BEGIN 

    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_table(chr_id, strand, source_t, max_gap, tag_extension,'', false, false, start_end);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_existing(chr_id integer, strand integer, max_gap integer, allow_extended_gaps boolean)
RETURNS SETOF glass_atlas_%s_%s_rna.glass_transcribed_rna_row AS $$
BEGIN 
    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_table(chr_id, strand, 'glass_atlas_%s_%s_rna"."glass_transcribed_rna', max_gap, 0,'transcription_', true, allow_extended_gaps, NULL);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_table(
        chr_id integer, strand integer, source_t text, max_gap integer, 
        tag_extension integer, field_prefix text, span_repeats boolean, allow_extended_gaps boolean,
        start_end box)
RETURNS SETOF glass_atlas_%s_%s_rna.glass_transcribed_rna_row AS $$
 DECLARE
    max_chrom_pos bigint;
    rec record;
    start_end_clause text := '';
    row glass_atlas_%s_%s_rna.glass_transcribed_rna_row;
    overlapping_length integer;
    length_gap integer;
    limit_gap integer := 1000;
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
    
    -- IF a start_end is passed, use that to limit transcribed_rnas
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
			-- Else, this is a new transcribed_rna; close off the current and restart.
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.save_transcribed_rnas_from_sequencing_run(
    seq_run_id integer, chr_id integer, source_t text, max_gap integer, 
    tag_extension integer, one_strand integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_rna.glass_transcribed_rna_row;
	transcribed_rna glass_atlas_%s_%s_rna.glass_transcribed_rna;
	scaling_factor text;
	strand_start integer := 0;
	strand_end integer := 1;
	use_for_scoring boolean;
 BEGIN
    
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
			SELECT * FROM glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_sequencing_run(chr_id, strand, source_t, max_gap, tag_extension, start_end)
		LOOP
			IF rec IS NOT NULL THEN
				EXECUTE 'INSERT INTO glass_atlas_%s_%s_rna.glass_transcribed_rna_' || rec.chromosome_id
					|| ' ("chromosome_id", "strand", 
					"transcription_start", "transcription_end", 
					"start_end")
					VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , 
					public.make_box(' || rec.transcription_start || ', 0, ' || rec.transcription_end || ', 0),
                    ) RETURNING *' INTO transcribed_rna;
	
				-- Save the record of the sequencing run source
				INSERT INTO glass_atlas_%s_%s_rna.glass_transcribed_rna_source 
					("glass_transcribed_rna_id", "sequencing_run_id", "tag_count", "gaps", "polya_count") 
					VALUES (transcribed_rna.id, seq_run_id, rec.tag_count, rec.gaps, rec.polya_count);

			END IF;
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.save_transcribed_rnas_from_existing(chr_id integer, max_gap integer, allow_extended_gaps boolean)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s_rna.glass_transcribed_rna_row;
	transcribed_rna glass_atlas_%s_%s_rna.glass_transcribed_rna;
	old_id integer;
 BEGIN
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s_%s_rna.determine_transcribed_rnas_from_existing(chr_id, strand, max_gap, allow_extended_gaps)
		LOOP
			IF rec IS NOT NULL AND rec.tag_count > 1 THEN		    
		        -- Save the transcribed_rna. 
				EXECUTE 'INSERT INTO glass_atlas_%s_%s_rna.glass_transcribed_rna_' || rec.chromosome_id
					|| ' ("chromosome_id", "strand", '
					|| ' "transcription_start", "transcription_end",' 
					|| ' "start_end")'
					|| ' VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , '
					|| ' public.make_box(' || rec.transcription_start || ', 0' 
                        || ',' ||  rec.transcription_end || ', 0)'
                    || ' ) RETURNING *' INTO transcribed_rna;
                
                -- Remove existing records
                FOR old_id IN 
                    SELECT * FROM unnest(rec.ids)
                LOOP
                    PERFORM glass_atlas_%s_%s_rna.update_transcribed_rna_source_records(transcribed_rna, old_id);
                END LOOP;
                EXECUTE 'DELETE FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_' || rec.chromosome_id
                    || ' WHERE id IN (' || array_to_string(rec.ids,',') || ')';
            END IF; 
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.calculate_scores_transcribed_rna(chr_id integer)
RETURNS VOID AS $$
DECLARE
    total_runs integer;
BEGIN 
    -- Tag count is scaled avg and max tags: sqrt(avg_tags * max_tags)
    -- Score is tag count divided by the lesser of length/1000 and 2*log(length),
    -- which allows lower tag counts per bp for longer transcribed_rnas.
    
    total_runs := (SELECT count(DISTINCT sequencing_run_id) FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_source);
    EXECUTE 'UPDATE glass_atlas_%s_%s_rna.glass_transcribed_rna_' || chr_id || ' transcribed_rna
            SET score = derived.score 
            FROM (SELECT 
                    transcribed_rna.id,
                    GREATEST(0,
                        SQRT((SUM(source.tag_count - source.polya_count)::numeric/' || total_runs || ')
                        *MAX(source.tag_count - source.polya_count)::numeric)
                        /LEAST(
                            GREATEST(1000, transcribed_rna.transcription_end - transcribed_rna.transcription_start)::numeric/1000,
                            2*LOG(transcribed_rna.transcription_end - transcribed_rna.transcription_start)
                            )
                    ) as score
                FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_' || chr_id || ' transcribed_rna 
                JOIN glass_atlas_%s_%s_rna.glass_transcribed_rna_source source
                ON source.glass_transcribed_rna_id = transcribed_rna.id
                JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
                WHERE run.use_for_scoring = true
                    AND transcribed_rna.chromosome_id = ' || chr_id || ' 
                    --AND transcribed_rna.score IS NULL
                GROUP BY transcribed_rna.id, transcribed_rna.transcription_end, transcribed_rna.transcription_start
            ) derived
            WHERE transcribed_rna.id = derived.id';
    EXECUTE 'UPDATE glass_atlas_%s_%s_rna.glass_transcribed_rna_' || chr_id || ' transcribed_rna
            SET score = 0 WHERE transcribed_rna.score IS NULL';
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.associate_transcribed_rna(chr_id integer)
RETURNS VOID AS $$
BEGIN
    -- Associate transcribed_rna with containing transcript, if it exists
    EXECUTE 'UPDATE glass_atlas_%s_%s_rna.glass_transcribed_rna_' || chr_id || ' transcribed_rna 
        SET glass_transcript_id = transcript.t_id
        FROM (
            SELECT tr.id as tr_id, t.id as t_id, row_number() OVER (PARTITION BY tr.id ORDER BY width(tr.start_end # t1.start_end) DESC) 
                FROM glass_atlas_%s_%s_rna.glass_transcribed_rna_' || chr_id || ' tr
            JOIN glass_atlas_%s_%s.glass_transcript_' || chr_id || ' t
            ON tr.start_end && t.start_end
                AND tr.strand = t.strand) transcript
        WHERE transcribed_rna.id = transcript.tr_id
            AND transcript.row_number = 1';
    RETURN;
END;
$$ LANGUAGE 'plpgsql'; 

""" % tuple([genome, cell_type]*48)

if __name__ == '__main__':
    print sql(genome, cell_type)
