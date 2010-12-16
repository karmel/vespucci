'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript functions.
'''
genome = 'mm10'
sql = """
-- Not run from within the codebase, but kept here in case functions need to be recreated.
DROP FUNCTION IF EXISTS glass_atlas_%s.stitch_transcripts_together(integer, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.update_transcript_source_records(glass_atlas_%s.glass_transcript, glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.update_transcribed_rna_records(glass_atlas_%s.glass_transcript, glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.remove_transcript_region_records(glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.insert_associated_transcript_regions(glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.merge_transcripts(glass_atlas_%s.glass_transcript, glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.save_transcript(glass_atlas_%s.glass_transcript);
DROP FUNCTION IF EXISTS glass_atlas_%s.determine_transcripts_from_sequencing_run(integer, integer, text, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.save_transcripts_from_sequencing_run(integer, integer, text, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.save_transcribed_rna_from_sequencing_run(integer, integer, text, integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.join_subtranscripts(integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.process_transcript_pair(glass_atlas_%s.glass_transcript_pair, integer[]);
DROP FUNCTION IF EXISTS glass_atlas_%s.get_subtranscripts_by_sequencing_run(integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.get_subtranscripts_by_transcription_region(integer);
DROP FUNCTION IF EXISTS glass_atlas_%s.calculate_scores(integer);
DROP TYPE IF EXISTS glass_atlas_%s.glass_transcript_row;
DROP TYPE IF EXISTS glass_atlas_%s.glass_transcript_pair;

CREATE TYPE glass_atlas_%s.glass_transcript_row AS ("chromosome_id" integer, "strand" smallint, 
	transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer);
CREATE TYPE glass_atlas_%s.glass_transcript_pair AS ("t1" glass_atlas_%s.glass_transcript, "t2" glass_atlas_%s.glass_transcript);

CREATE FUNCTION glass_atlas_%s.update_transcript_source_records(merged_trans glass_atlas_%s.glass_transcript, trans glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s.glass_transcript_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps)
		FROM glass_atlas_%s.glass_transcript_source trans_assoc
		WHERE merged_assoc.glass_transcript_id = merged_trans.id
			AND trans_assoc.glass_transcript_id = trans.id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s.glass_transcript_source
		SET glass_transcript_id = merged_trans.id
		WHERE glass_transcript_id = trans.id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s.glass_transcript_source
			WHERE glass_transcript_id = merged_trans.id);
	-- Delete those that remain for the removed transcript.
	DELETE FROM glass_atlas_%s.glass_transcript_source
		WHERE glass_transcript_id = trans.id;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.update_transcribed_rna_records(merged_trans glass_atlas_%s.glass_transcript, trans glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
BEGIN 
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s.glass_transcribed_rna
		SET glass_transcript_id = merged_trans.id
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
BEGIN
	-- Associate any sequencing regions
	cube = 'public.cube(' || rec.transcription_start || ',' || rec.transcription_end || ')';
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
		|| ' AND (strand IS NULL OR strand = ' || rec.strand || ')'
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
	merged_trans.strand := trans.strand;
	IF trans.spliced = true THEN merged_trans.spliced := true;
	END IF;
	merged_trans.start_end := public.cube(merged_trans.transcription_start, merged_trans.transcription_end);
	merged_trans.score := NULL;
	RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.save_transcript(rec glass_atlas_%s.glass_transcript)
RETURNS VOID AS $$
DECLARE spliced_sql text;
DECLARE score_sql text;
BEGIN 	
	-- Update record
	IF rec.spliced IS NOT NULL THEN spliced_sql = ' spliced = ' || rec.spliced;
	ELSE spliced_sql = ' spliced = NULL ';
	END IF; 
	IF rec.score IS NOT NULL THEN score_sql = ' score = ' || rec.score;
	ELSE score_sql = ' score = NULL ';
	END IF; 
	EXECUTE 'UPDATE glass_atlas_%s.glass_transcript_' || rec.chromosome_id 
	|| ' SET'
		|| ' strand = ' || rec.strand || ','
		|| ' transcription_start = ' || rec.transcription_start || ','
		|| ' transcription_end = ' || rec.transcription_end || ','
		|| ' start_end = public.cube(' || rec.transcription_start || '::float,' || rec.transcription_end || '::float),'
		|| spliced_sql || ','
		|| score_sql || ','
		|| ' modified = NOW()'
	|| ' WHERE id = ' || rec.id;
	
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
   strand_query text := '';
 BEGIN
 	IF strand IS NOT NULL THEN strand_query = '" WHERE strand = ' || strand;
 	END IF; 
	FOR rec IN 
		EXECUTE 'SELECT * FROM "'
		|| source_t || '_' || chr_id
		|| strand_query || ' ORDER BY start;'
		LOOP
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
			IF rec IS NOT NULL THEN
				-- Save the transcript.
				EXECUTE 'INSERT INTO glass_atlas_%s.glass_transcript_' || rec.chromosome_id
					|| ' ("chromosome_id", "strand", '
					|| ' "transcription_start", "transcription_end",' 
					|| ' "start_end", "modified", "created")'
					|| ' VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
					|| rec.transcription_start || ' , ' || rec.transcription_end || ' , '
					|| ' public.cube(' || rec.transcription_start || ' , ' || rec.transcription_end || ' ),' 
					|| ' NOW(), NOW()) RETURNING *' INTO transcript;
	
				-- Save the record of the sequencing run source
				INSERT INTO glass_atlas_%s.glass_transcript_source 
					("glass_transcript_id", "sequencing_run_id", "tag_count", "gaps") 
					VALUES (transcript.id, seq_run_id, rec.tag_count, rec.gaps);
					
				-- Associate any sequencing regions
				PERFORM glass_atlas_%s.insert_associated_transcript_regions(transcript);
			END IF;
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
	transcript_id integer;
	existing glass_atlas_%s.glass_transcribed_rna;
	transcribed_rna glass_atlas_%s.glass_transcribed_rna;
 BEGIN
	FOR rec IN 
		SELECT * FROM glass_atlas_%s.determine_transcripts_from_sequencing_run(chr_id, NULL, source_t, max_gap)
	LOOP
		-- Note that we do not match on strand here, presuming that total RNA will come back double stranded
		
		-- Find existing transcribed RNA where the start and end are
		-- only 10percent of the existing transcribed region's length separated
		-- from the new start and end
		FOR existing IN
			SELECT * FROM glass_atlas_%s.glass_transcribed_rna 
			WHERE chromosome_id = rec.chromosome_id 
				AND abs("start" - rec.transcription_start) <= .1*(("end" - "start")::float)
				AND abs("end" - rec.transcription_end) <= .1*(("end" - "start")::float)
				ORDER BY start ASC
		LOOP
			rec.transcription_start := (SELECT LEAST(existing.start, rec.transcription_start));
			rec.transcription_end := (SELECT GREATEST(existing."end", rec.transcription_end));
			DELETE FROM glass_atlas_%s.glass_transcribed_rna WHERE id = existing.id;
		END LOOP;
		
		-- Find matching transcript, preferring the longest available where more than one match
		EXECUTE 'SELECT * FROM glass_atlas_%s.glass_transcript_' || rec.chromosome_id
			|| ' WHERE chromosome_id = rec.chromosome_id '
				|| ' AND start_end OPERATOR(public.@>) public.cube(' || rec.transcription_start 
					|| ', ' || rec.transcription_end || ') '
				|| ' ORDER BY (transcription_end - transcription_start) DESC'
				|| ' LIMIT 1' INTO transcript;
				
		IF NOT FOUND THEN transcript_id = NULL;
		ELSE transcript_id = transcript.id;
		END IF;
		
		-- Saved the Transcribed RNA
		INSERT INTO glass_atlas_%s.glass_transcribed_rna 
			("glass_transcript_id", "chromosome_id", "start", "end", "start_end")
			VALUES (transcript.id, chr_id, rec.transcription_start, rec.transcription_end, 
			public.cube(rec.transcription_start, rec.transcription_end))
			RETURNING * INTO transcribed_rna;
			
		-- Save the record of the sequencing run source
		--INSERT INTO glass_atlas_%s.glass_transcript_source 
		--	("glass_transcript_id", "sequencing_run_id", "tag_count", "gaps") 
		--	VALUES (transcript_id, seq_run_id, rec.tag_count, rec.gaps);
			
		-- Update transcript
		EXECUTE 'UPDATE glass_atlas_%s.glass_transcript_' || chr_id
			|| ' SET spliced = true, score = NULL,'
			|| ' modified = NOW()'
			|| ' WHERE id = ' || transcript.id;
		
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.stitch_transcripts_together(chr_id integer, allowed_gap integer)
RETURNS VOID AS $$
 DECLARE
	transcript_group record;
	trans glass_atlas_%s.glass_transcript;
	merged_trans glass_atlas_%s.glass_transcript;
	overlapping_length integer;
	should_merge boolean := false;
	merged boolean := false;
	max_gap integer;
	length_gap integer;
BEGIN
	FOR transcript_group IN 
		EXECUTE 'SELECT' 
		    || ' array_agg(transcript.*) as transcripts,'
			|| ' grouped_seq.regions'
		|| ' FROM "glass_atlas_%s"."glass_transcript_' || chr_id ||'" transcript'
		|| ' LEFT OUTER JOIN (SELECT '
		        || ' glass_transcript_id, '
		        || ' public.sort(array_agg(sequence_transcription_region_id)::int[]) as regions'
		    || ' FROM "glass_atlas_%s"."glass_transcript_sequence"'
		    || ' GROUP BY glass_transcript_id) grouped_seq'
		|| ' ON transcript.id = grouped_seq.glass_transcript_id'
		|| ' LEFT OUTER JOIN (SELECT '
		        || ' glass_transcript_id, '
		        || ' public.sort(array_agg(non_coding_transcription_region_id)::int[]) as regions'
		    || ' FROM "glass_atlas_%s"."glass_transcript_non_coding"'
		    || ' GROUP BY glass_transcript_id) grouped_nc'
		|| ' ON transcript.id = grouped_nc.glass_transcript_id'
		|| ' WHERE transcript.chromosome_id = ' || chr_id
		|| ' GROUP BY grouped_seq.regions, grouped_nc.regions, transcript.strand'
		|| ' HAVING count(transcript.id) > 1'
	LOOP
		-- Transcript_group is an array of transcripts and an array of associated sequences
		-- such that the group of transcripts all share the same associated sequences,
		-- and therefore are good candidates for stitching together.
		
		-- Try to group each transcript, bailing if the gap is passed.
		FOR trans IN
			SELECT * FROM unnest(transcript_group.transcripts)
			ORDER BY transcription_start ASC, transcription_end DESC
		LOOP
			max_gap := allowed_gap;
			IF merged_trans IS NULL THEN merged_trans := trans;
			ELSE
				should_merge := false;
				-- Does this transcript connect?
				IF (merged_trans.transcription_end >= trans.transcription_start) THEN should_merge := true;
				ELSE
					IF (transcript_group.regions IS NOT NULL) THEN
						-- Should this gap be considered in light of an overlapping sequence?
						overlapping_length := (SELECT (transcription_end - transcription_start) 
											FROM genome_reference_mm9.sequence_transcription_region
											WHERE chromosome_id = chr_id
												AND strand = merged_trans.strand
												AND start_end OPERATOR(public.@>) 
													public.cube(merged_trans.transcription_end, trans.transcription_start)
											ORDER BY (transcription_end - transcription_start) DESC
											LIMIT 1);
						-- Allow up to a fifth of the sequence as a gap
						length_gap := (overlapping_length::float*.2)::integer;
						max_gap := (SELECT GREATEST(max_gap, length_gap));
						max_gap := (SELECT LEAST(max_gap, 5000));
					END IF;
					IF (trans.transcription_start - merged_trans.transcription_end) <= max_gap THEN should_merge := true;
					END IF;
				END IF;
				
				IF should_merge = true
					THEN 
						merged_trans := (SELECT glass_atlas_%s.merge_transcripts(merged_trans, trans));
						-- Delete/update old associations
						PERFORM glass_atlas_%s.update_transcript_source_records(merged_trans, trans);
						PERFORM glass_atlas_%s.update_transcribed_rna_records(merged_trans, trans);
						PERFORM glass_atlas_%s.remove_transcript_region_records(trans);
						EXECUTE 'DELETE FROM glass_atlas_%s.glass_transcript_' || trans.chromosome_id || ' WHERE id = ' || trans.id;
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
	transcript_pair glass_atlas_%s.glass_transcript_pair;
	consumed1 integer[];
	consumed2 integer[];
BEGIN
	-- Loop until all pairs are consumed
	WHILE (consumed1 IS NULL OR consumed1 > array[]::integer[])
	LOOP
		consumed1 := array[]::integer[];
		FOR transcript_pair IN
			SELECT * FROM glass_atlas_%s.get_subtranscripts_by_sequencing_run(chr_id)
		LOOP
			-- Transcript 1 contains Transcript 2. Unite and update references
			-- where Transcript 1 has tags from the same sequencing runs as Transcript 2.
			-- Keep track of consumed transcripts to ensure we do not try to process an already deleted transcript
			consumed1 = (SELECT glass_atlas_%s.process_transcript_pair(transcript_pair, consumed1));
		END LOOP;
	END LOOP;

	WHILE (consumed2 IS NULL OR consumed2 > array[]::integer[])
	LOOP
		consumed2 := array[]::integer[];
		FOR transcript_pair IN
			SELECT * FROM glass_atlas_%s.get_subtranscripts_by_transcription_region(chr_id)
		LOOP
			-- Transcript 1 contains Transcript 2. Unite and update references
			-- where Transcript 1 has tags from the same sequencing runs as Transcript 2.
			consumed2 = (SELECT glass_atlas_%s.process_transcript_pair(transcript_pair, consumed2));
		END LOOP;
	END LOOP;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.process_transcript_pair(transcript_pair glass_atlas_%s.glass_transcript_pair, consumed integer[])
RETURNS integer[] AS $$
 DECLARE
	trans glass_atlas_%s.glass_transcript;
	merged_trans glass_atlas_%s.glass_transcript;
BEGIN
	merged_trans := transcript_pair.t1;
	trans := transcript_pair.t2;
	IF (consumed @> ARRAY[trans.id] = false 
		AND consumed @> ARRAY[merged_trans.id] = false) THEN
			merged_trans := (SELECT glass_atlas_%s.merge_transcripts(merged_trans, trans));
			PERFORM glass_atlas_%s.update_transcript_source_records(merged_trans, trans);
			PERFORM glass_atlas_%s.update_transcribed_rna_records(merged_trans, trans);
			PERFORM glass_atlas_%s.remove_transcript_region_records(trans);
			EXECUTE 'DELETE FROM glass_atlas_%s.glass_transcript_' || trans.chromosome_id || ' WHERE id = ' || trans.id;
			PERFORM glass_atlas_%s.save_transcript(merged_trans);
			consumed = consumed || trans.id;
			consumed = consumed || merged_trans.id;
	END IF;
	RETURN consumed;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.get_subtranscripts_by_sequencing_run(chr_id integer)
RETURNS SETOF glass_atlas_%s.glass_transcript_pair AS $$
BEGIN
	RETURN QUERY
		EXECUTE '(SELECT (transcript1.*)::glass_atlas_%s.glass_transcript as t1,'
			|| ' (transcript2.*)::glass_atlas_%s.glass_transcript as t2'
		|| ' FROM glass_atlas_%s.glass_transcript_' || chr_id || '  transcript1'
		|| ' JOIN glass_atlas_%s.glass_transcript_' || chr_id || '  transcript2'
		|| ' ON  transcript1.start_end OPERATOR(public.&&) transcript2.start_end'
		|| ' AND transcript1.strand = transcript2.strand'
		|| ' AND transcript1.id != transcript2.id'
		|| ' LEFT OUTER JOIN ('
			|| ' SELECT glass_transcript_id, public.sort(array_agg(sequencing_run_id)::int[]) as runs'
			|| ' FROM glass_atlas_%s.glass_transcript_source' 
			|| ' GROUP BY glass_transcript_id'
			|| ' ) source1'
		|| ' ON transcript1.id = source1.glass_transcript_id'
		|| ' LEFT OUTER JOIN ('
			|| ' SELECT glass_transcript_id, public.sort(array_agg(sequencing_run_id)::int[]) as runs'
			|| ' FROM glass_atlas_%s.glass_transcript_source' 
			|| ' GROUP BY glass_transcript_id'
			|| ' ) source2'
		|| ' ON transcript2.id = source2.glass_transcript_id'
		|| ' WHERE transcript1.chromosome_id = ' || chr_id
			|| ' AND transcript2.chromosome_id = ' || chr_id
			|| ' AND source1.runs @> source2.runs'
			-- Prevent equivalent run arrays from appearing as two separate rows
			|| ' AND (source1.runs != source2.runs OR transcript1.id > transcript2.id)'
		|| ' ORDER BY transcript1.transcription_start ASC, transcript1.transcription_end DESC)';
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.get_subtranscripts_by_transcription_region(chr_id integer)
RETURNS SETOF glass_atlas_%s.glass_transcript_pair AS $$
BEGIN
	RETURN QUERY
		EXECUTE '(SELECT (transcript1.*)::glass_atlas_%s.glass_transcript as t1,'
			|| ' (transcript2.*)::glass_atlas_%s.glass_transcript as t2'
		|| ' FROM glass_atlas_%s.glass_transcript_' || chr_id || ' transcript1'
		|| ' JOIN glass_atlas_%s.glass_transcript_' || chr_id || ' transcript2'
		|| ' ON  transcript1.start_end OPERATOR(public.&&) transcript2.start_end'
		|| ' AND transcript1.strand = transcript2.strand'
		|| ' AND transcript1.id != transcript2.id'
		|| ' LEFT OUTER JOIN (SELECT '
		        || ' glass_transcript_id,' 
		        || ' public.sort(array_agg(sequence_transcription_region_id)::int[]) as regions'
		    || ' FROM "glass_atlas_%s"."glass_transcript_sequence"'
		    || ' GROUP BY glass_transcript_id) grouped_seq1'
		|| ' ON transcript1.id = grouped_seq1.glass_transcript_id'
		|| ' LEFT OUTER JOIN (SELECT '
		        || ' glass_transcript_id,' 
		        || ' public.sort(array_agg(sequence_transcription_region_id)::int[]) as regions'
		    || ' FROM "glass_atlas_%s"."glass_transcript_sequence"'
		    || ' GROUP BY glass_transcript_id) grouped_seq2'
		|| ' ON transcript2.id = grouped_seq2.glass_transcript_id'
		|| ' WHERE transcript1.chromosome_id = ' || chr_id
			|| ' AND transcript2.chromosome_id = ' || chr_id
			|| ' AND ((grouped_seq1.regions @> grouped_seq2.regions'
				-- Prevent equivalent region arrays from appearing as two separate rows
				|| ' AND (grouped_seq1.regions != grouped_seq2.regions OR transcript1.id > transcript2.id)) '
				|| ' OR grouped_seq2.regions IS NULL)'
		|| ' ORDER by transcript1.transcription_start ASC, transcript1.transcription_end DESC)';
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.calculate_scores(chr_id integer)
RETURNS VOID AS $$
BEGIN 
	EXECUTE 'UPDATE glass_atlas_%s.glass_transcript_' || chr_id || ' transcript'
		|| ' SET score = derived.score '
		|| ' FROM (SELECT '
				|| ' transcript.id,' 
				|| ' log(SUM(source.tag_count)::numeric) as score'
			|| ' FROM glass_atlas_%s.glass_transcript_' || chr_id || ' transcript, '
				|| ' glass_atlas_%s.glass_transcript_source source'
			|| ' WHERE source.glass_transcript_id = transcript.id'
				|| ' AND transcript.chromosome_id = ' || chr_id
				|| ' AND transcript.score IS NULL'
			|| ' GROUP BY transcript.id'
		|| ' ) derived'
		|| ' WHERE transcript.id = derived.id';

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome]*133)

print sql
