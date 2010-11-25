'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript functions.
'''
genome = 'mm9'
sql = """
-- Not run from within the codebase, but kept here in case functions need to be recreated.
DROP FUNCTION IF EXISTS glass_atlas_%s.stitch_transcripts_together(integer, integer, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.remove_transcript_source_records(glass_atlas_%s.glass_transcript, glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.remove_transcript_region_records(glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.insert_associated_transcript_regions(glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.merge_transcripts(glass_atlas_%s.glass_transcript, glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.save_transcript(glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.determine_transcripts_from_sequencing_run(integer, integer, text, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.save_transcripts_from_sequencing_run(integer, integer, text, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.save_transcribed_rna_from_sequencing_run(integer, integer, text, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.join_subtranscripts(integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.calculate_scores(integer);
DROP TYPE IF EXISTS glass_atlas_%s.glass_transcript_row;

CREATE TYPE glass_atlas_%s.glass_transcript_row AS ("chromosome_id" integer, "strand_0" boolean, "strand_1" boolean, 
	transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer);

CREATE FUNCTION glass_atlas_%s.remove_transcript_source_records(merged_trans glass_atlas_%s.glass_transcript, trans glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
BEGIN 
	-- Remove redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s.glass_transcript_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps)
		FROM glass_atlas_%s.glass_transcript_source trans_assoc
		WHERE merged_assoc.glass_transcript_id = merged_trans.id
			AND trans_assoc.glass_transcript_id = trans.id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- Remove redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s.glass_transcript_source
		SET glass_transcript_id = merged_trans.id
		WHERE glass_transcript_id = trans.id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s.glass_transcript_source
			WHERE glass_transcript_id = merged_trans.id);
	-- Delete those that remain.
	DELETE FROM glass_atlas_%s.glass_transcript_source
		WHERE glass_transcript_id = trans.id;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.remove_transcript_region_records(rec glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
DECLARE
	region_types text[] := ARRAY['sequence','non_coding','conserved','patterned'];
	counter integer;
	table_type text;
BEGIN 
	FOR counter IN array_lower(region_types,1)..array_upper(region_types,1)
	LOOP
		table_type := region_types[counter];
		-- Delete associated regions.
		EXECUTE 'DELETE FROM glass_atlas_%s.glass_transcript_'
			|| table_type || ' WHERE glass_transcript_id = ' || rec.id;
	END LOOP;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.insert_associated_transcript_regions(rec glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
DECLARE
	region_types text[] := ARRAY['sequence','non_coding','conserved','patterned'];
	counter integer;
	cube text;
	table_type text;
	strand integer;
BEGIN
	-- Associate any sequencing regions
	cube = 'public.cube(' || rec.transcription_start || ',' || rec.transcription_end || ')';
	IF rec.strand_0 THEN strand := 0;
	ELSE strand := 1;
	END IF;
	FOR counter IN array_lower(region_types,1)..array_upper(region_types,1)
	LOOP
		table_type := region_types[counter];
		EXECUTE 'INSERT INTO glass_atlas_%s.glass_transcript_'
		|| table_type || ' (glass_transcript_id, '
		|| table_type || '_transcription_region_id, relationship)'
		|| '(SELECT ' || rec.id || ', id, '
		|| '(CASE WHEN start_end OPERATOR(public.=) ' || cube || ' THEN '
		|| ' glass_atlas_%s.glass_transcript_transcription_region_relationship(\\'is equal to\\') '
		|| ' WHEN start_end OPERATOR(public.<@) ' || cube || ' THEN '
		|| ' glass_atlas_%s.glass_transcript_transcription_region_relationship(\\'contains\\') '
		|| ' WHEN start_end OPERATOR(public.@>) ' || cube || ' THEN '
		|| ' glass_atlas_%s.glass_transcript_transcription_region_relationship(\\'is contained by\\') '
		|| 'ELSE glass_atlas_%s.glass_transcript_transcription_region_relationship(\\'overlaps with\\') END)'
		|| ' FROM genome_reference_mm9.'
		|| table_type || '_transcription_region '
		|| ' WHERE chromosome_id = ' || rec.chromosome_id 
		|| ' AND (strand IS NULL OR strand = ' || strand || ')'
		|| ' AND start_end OPERATOR(public.&&) ' || cube || ' )';
	END LOOP;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
			
CREATE FUNCTION glass_atlas_%s.merge_transcripts(merged_trans glass_atlas_%s.glass_transcript, trans glass_atlas_%s.glass_transcript)
RETURNS glass_atlas_%s.glass_transcript AS $$
BEGIN
	-- Update the merged transcript
	merged_trans.transcription_start := (SELECT LEAST(merged_trans.transcription_start, trans.transcription_start));
	merged_trans.transcription_end := (SELECT GREATEST(merged_trans.transcription_end, trans.transcription_end));
	IF trans.strand_0 = true THEN merged_trans.strand_0 := true;
	END IF;
	IF trans.strand_1 = true THEN merged_trans.strand_1 := true;
	END IF;
	IF trans.spliced = true THEN merged_trans.spliced := true;
	END IF;
	merged_trans.start_end := public.cube(merged_trans.transcription_start, merged_trans.transcription_end);
	merged_trans.score := NULL;
	RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.save_transcript(rec glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
BEGIN 	
	-- Update record
	UPDATE glass_atlas_%s.glass_transcript SET
		strand_0 = rec.strand_0,
		strand_1 = rec.strand_1,
		transcription_start = rec.transcription_start,
		transcription_end = rec.transcription_end,
		start_end = rec.start_end,
		spliced = rec.spliced,
		score = rec.score,
		modified = NOW()
	WHERE id = rec.id;
	
	-- Remove old and find new sequence associations
	PERFORM glass_atlas_%s.remove_transcript_region_records(rec);
	PERFORM glass_atlas_%s.insert_associated_transcript_regions(rec);
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.determine_transcripts_from_sequencing_run(chr_id integer, strand integer, source_t text, max_gap integer)
RETURNS SETOF glass_atlas_%s.glass_transcript_row AS $$
 DECLARE
   rec record;
   row glass_atlas_%s.glass_transcript_row;
   last_start bigint := 0;
   last_end bigint := 0;
   tag_count integer := 0;
   gaps integer := 0;
   finish_row boolean := false;
 BEGIN
	FOR rec IN 
		EXECUTE 'SELECT * FROM "'
		|| source_t || '_' || chr_id
		|| '" WHERE strand = '
		|| strand || ' ORDER BY start;'
		LOOP
			-- Initialize the start and end if necessary
			IF (last_start = 0) THEN 
				last_start := rec."start";
			END IF;
			IF (last_end = 0) THEN 
				last_end := rec."end";
			END IF;

			-- Include this tag if it overlaps or has < 100 bp gap
			-- Else, this is a new transcript; close off the current and restart.
			IF ((last_end + max_gap) >= rec."start") THEN
				tag_count := tag_count + 1;
				IF (rec."start" > last_end) THEN
					gaps := gaps + 1;
				END IF;
				IF (rec."end" > last_end) THEN
					last_end := rec."end";
				END IF;
			ELSE
				finish_row := true;
			END IF;
			
			-- Store row even if not done, in case this is the last loop	
			row.chromosome_id := chr_id;
			IF (rec.strand = 0) THEN 
				row.strand_0 := true;
				row.strand_1 := false;
			ELSE 
				IF (rec.strand = 1) THEN
					row.strand_0 := false;
					row.strand_1 := true;
				END IF;
			END IF;
			row.transcription_start := last_start;
			row.transcription_end := last_end;
			row.tag_count := tag_count;
			row.gaps := gaps;
			
			IF finish_row THEN
				-- Restart vars for next loop
				last_start := 0;
				last_end := 0;
				tag_count := 0;
				gaps := 0;
				finish_row := false;
				
				IF (row.tag_count > 5 AND row.gaps = 0) OR (row.tag_count > 8 AND row.tag_count > row.gaps*2) THEN 
					RETURN NEXT row;
				END IF;
			END IF;
	END LOOP;
		
	-- One more left?
	IF (row.tag_count > 5 AND row.gaps = 0) OR (row.tag_count > 8 AND row.tag_count > row.gaps*2) THEN 
		RETURN NEXT row;
	END IF;
		
	-- And finally, return the set.
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.save_transcripts_from_sequencing_run(seq_run_id integer, chr_id integer, source_t text, max_gap integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s.glass_transcript_row;
	transcript glass_atlas_%s.glass_transcript;
 BEGIN
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap)
		LOOP
				-- Save the transcript.
				INSERT INTO glass_atlas_%s.glass_transcript 
					("chromosome_id", "strand_0", "strand_1", 
					"transcription_start", "transcription_end", 
					"start_end", "modified", "created")
					VALUES (rec.chromosome_id, rec.strand_0, rec.strand_1, 
					rec.transcription_start, rec.transcription_end, 
					public.cube(rec.transcription_start, rec.transcription_end), 
					NOW(), NOW())
					RETURNING * INTO transcript;
	
				-- Save the record of the sequencing run source
				INSERT INTO glass_atlas_%s.glass_transcript_source 
					("glass_transcript_id", "sequencing_run_id", "tag_count", "gaps") 
					VALUES (transcript.id, seq_run_id, rec.tag_count, rec.gaps);
					
				-- Associate any sequencing regions
				PERFORM glass_atlas_%s.insert_associated_transcript_regions(transcript);
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.save_transcribed_rna_from_sequencing_run(seq_run_id integer, chr_id integer, source_t text, max_gap integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s.glass_transcript_row;
	transcript glass_atlas_%s.glass_transcript;
	transcribed_rna glass_atlas_%s.glass_transcribed_rna;
 BEGIN
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap)
		LOOP
			-- Find matching transcript
			transcript := (SELECT * FROM glass_atlas_%s.glass_transcript 
				WHERE chromosome_id = rec.chromosome_id 
					AND strand_0 = rec.strand_0
					AND strand_1 = rec.strand_1
					AND start_end OPERATOR(public.@>) public.cube(rec.transcription_start, rec.transcription_end));
			IF transcript IS NULL THEN
				-- Save the transcript.
				INSERT INTO glass_atlas_%s.glass_transcript
					("chromosome_id", "strand_0", "strand_1", "start", "end", "start_end")
					VALUES (rec.chromosome_id, rec.strand_0, rec.strand_1, 
					rec.transcription_start, rec.transcription_end, 
					public.cube(rec.transcription_start, rec.transcription_end))
					RETURNING * INTO transcript;
				PERFORM glass_atlas_%s.insert_associated_transcript_regions(transcript);
			END IF;
			-- Saved the Transcribed RNA
			INSERT INTO glass_atlas_%s.glass_transcribed_rna 
				("glass_transcript_id","strand_0", "strand_1", "start", "end", "start_end")
				VALUES (transcript.id, rec.strand_0, rec.strand_1, 
				rec.transcription_start, rec.transcription_end, 
				public.cube(rec.transcription_start, rec.transcription_end))
				RETURNING * INTO transcribed_rna;
				
			-- Save the record of the sequencing run source
			INSERT INTO glass_atlas_%s.glass_transcript_source 
				("glass_transcript_id", "sequencing_run_id", "tag_count", "gaps") 
				VALUES (transcript.id, seq_run_id, rec.tag_count, rec.gaps);
				
			-- Update transcript
			UPDATE glass_atlas_%s.glass_transcript 
				SET spliced = true, score = NULL 
				WHERE id = transcript.id;
			
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.stitch_transcripts_together(chr_id integer, max_sequence_gap integer, max_other_gap integer)
RETURNS VOID AS $$
 DECLARE
	transcript_group record;
	trans glass_atlas_%s.glass_transcript;
	merged_trans glass_atlas_%s.glass_transcript;
	merged boolean := false;
	max_gap integer;
BEGIN
	FOR transcript_group IN 
		SELECT 
		    array_agg(transcript.*) as transcripts,
			grouped_seq.regions
		FROM "glass_atlas_%s"."glass_transcript" transcript
		LEFT OUTER JOIN (SELECT 
		        glass_transcript_id, 
		        public.sort(array_agg(sequence_transcription_region_id)::int[]) as regions
		    FROM "glass_atlas_%s"."glass_transcript_sequence"
		    GROUP BY glass_transcript_id) grouped_seq
		ON transcript.id = grouped_seq.glass_transcript_id
		LEFT OUTER JOIN (SELECT 
		        glass_transcript_id, 
		        public.sort(array_agg(non_coding_transcription_region_id)::int[]) as regions
		    FROM "glass_atlas_%s"."glass_transcript_non_coding"
		    GROUP BY glass_transcript_id) grouped_nc
		ON transcript.id = grouped_nc.glass_transcript_id
		WHERE transcript.chromosome_id = chr_id
		GROUP BY grouped_seq.regions, grouped_nc.regions, transcript.strand_0, transcript.strand_1
		HAVING count(transcript.id) > 1
	LOOP
		-- Transcript_group is an array of transcripts and an array of associated sequences
		-- such that the group of transcripts all share the same associated sequences,
		-- and therefore are good candidates for stitching together.
		
		-- We want to allow shorter gaps if we do not have sequences associated
		-- with the transcript in question.
		IF transcript_group.regions IS NULL THEN max_gap := max_other_gap;
		ELSE max_gap := max_sequence_gap;
		END IF;
		
		-- Try to group each transcript, bailing if the gap is passed.
		FOR trans IN
			SELECT * FROM unnest(transcript_group.transcripts)
			ORDER BY transcription_start ASC, transcription_end DESC
		LOOP
			IF merged_trans IS NULL THEN merged_trans := trans;
			ELSE
				-- Does this transcript connect?
				IF (merged_trans.transcription_end >= trans.transcription_start)
					OR (trans.transcription_start - merged_trans.transcription_end <= max_gap)
					THEN 
						merged_trans := (SELECT glass_atlas_%s.merge_transcripts(merged_trans, trans));
						-- Delete/update old associations
						PERFORM glass_atlas_%s.remove_transcript_source_records(merged_trans, trans);
						PERFORM glass_atlas_%s.remove_transcript_region_records(merged_trans);
						DELETE FROM glass_atlas_%s.glass_transcript WHERE id = trans.id;
						merged := true;
				ELSE
					-- We have reached a gap; close off any open merged_transcripts
					IF merged THEN
						PERFORM glass_atlas_%s.save_transcript(merged_trans);
					END IF;
					-- And reset the merged transcript
					merged_trans := trans;
					merged := false;
				END IF;
			END IF;
		END LOOP;
		
		-- We may have one final merged transcript awaiting a save:
		IF merged THEN
			PERFORM glass_atlas_%s.save_transcript(merged_trans);
		END IF;
		-- And reset the merged transcript
		merged_trans := NULL;
		merged := false;
	END LOOP;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.join_subtranscripts(chr_id integer)
RETURNS VOID AS $$
 DECLARE
	transcript_pair record;
	trans glass_atlas_%s.glass_transcript;
	merged_trans glass_atlas_%s.glass_transcript;
BEGIN
	FOR transcript_pair IN
		SELECT (transcript1.*)::record as t1,
			(transcript2.*)::record as t2,
			source1.runs as runs1,
			source2.runs as runs2
		FROM glass_atlas_%s.glass_transcript transcript1
		JOIN glass_atlas_%s.glass_transcript transcript2
		ON  transcript1.start_end OPERATOR(public.&&) transcript2.start_end
		AND transcript1.strand_0 = transcript2.strand_0
		AND transcript1.strand_1 = transcript2.strand_1
		AND transcript1.id != transcript2.id
		LEFT OUTER JOIN (
			SELECT glass_transcript_id, public.sort(array_agg(sequencing_run_id)::int[]) as runs
			FROM glass_atlas_%s.glass_transcript_source 
			GROUP BY glass_transcript_id
			) source1
		ON transcript1.id = source1.glass_transcript_id
		LEFT OUTER JOIN (
			SELECT glass_transcript_id, public.sort(array_agg(sequencing_run_id)::int[]) as runs
			FROM glass_atlas_%s.glass_transcript_source 
			GROUP BY glass_transcript_id
			) source2
		ON transcript2.id = source2.glass_transcript_id
		WHERE transcript1.chromosome_id = chr_id
			AND transcript2.chromosome_id = chr_id
			AND source1.runs @> source2.runs
	LOOP
		-- Transcript 1 contains Transcript 2. Unite and update references
		-- where Transcript 1 has tags from the same sequencing runs as Transcript 2.
		
		merged_trans := transcript_pair.t1;
		trans := transcript_pair.t2;
		merged_trans := (SELECT glass_atlas_%s.merge_transcripts(merged_trans, trans));
		PERFORM glass_atlas_%s.remove_transcript_source_records(merged_trans, trans);
		PERFORM glass_atlas_%s.remove_transcript_region_records(trans);
		DELETE FROM glass_atlas_%s.glass_transcript WHERE id = trans.id;
		PERFORM glass_atlas_%s.save_transcript(merged_trans);
	END LOOP;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';


CREATE FUNCTION glass_atlas_%s.calculate_scores(chr_id integer)
RETURNS VOID AS $$
BEGIN 
	UPDATE glass_atlas_%s.glass_transcript transcript
		SET score = derived.score 
		FROM (SELECT 
				transcript.id, 
				log(SUM(source.tag_count)::numeric) as score
			FROM glass_atlas_%s.glass_transcript transcript, 
				glass_atlas_%s.glass_transcript_source source
			WHERE source.glass_transcript_id = transcript.id
				AND transcript.chromosome_id = chr_id
				AND transcript.score IS NULL
			GROUP BY transcript.id
		) derived
		WHERE transcript.id = derived.id;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome]*96)

print sql