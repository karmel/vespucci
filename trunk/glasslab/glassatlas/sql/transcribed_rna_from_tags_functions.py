'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcribed RNA functions.
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

CREATE TYPE glass_atlas_%s.glass_transcribed_rna_pair AS ("t1" glass_atlas_%s.glass_transcribed_rna, "t2" glass_atlas_%s.glass_transcribed_rna);

CREATE FUNCTION glass_atlas_%s.update_transcribed_rna_source_records(merged_trans glass_atlas_%s.glass_transcribed_rna, trans glass_atlas_%s.glass_transcribed_rna)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s.glass_transcribed_rna_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps)
		FROM glass_atlas_%s.glass_transcribed_rna_source trans_assoc
		WHERE merged_assoc.glass_transcribed_rna_id = merged_trans.id
			AND trans_assoc.glass_transcribed_rna_id = trans.id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s.glass_transcribed_rna_source
		SET glass_transcribed_rna_id = merged_trans.id
		WHERE glass_transcribed_rna_id = trans.id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s.glass_transcribed_rna_source
			WHERE glass_transcribed_rna_id = merged_trans.id);
	-- Delete those that remain for the removed transcript.
	DELETE FROM glass_atlas_%s.glass_transcribed_rna_source
		WHERE glass_transcribed_rna_id = trans.id;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	
CREATE FUNCTION glass_atlas_%s.merge_transcribed_rna(merged_trans glass_atlas_%s.glass_transcribed_rna, trans glass_atlas_%s.glass_transcribed_rna)
RETURNS glass_atlas_%s.glass_transcribed_rna AS $$
BEGIN
	-- Update the merged transcript
	merged_trans.glass_transcript_id := trans.glass_transcript_id;
	merged_trans.transcription_start := (SELECT LEAST(merged_trans.transcription_start, trans.transcription_start));
	merged_trans.transcription_end := (SELECT GREATEST(merged_trans.transcription_end, trans.transcription_end));
	merged_trans.strand := trans.strand;
	merged_trans.start_end := public.cube(merged_trans.transcription_start, merged_trans.transcription_end);
	RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.save_transcribed_rna(rec glass_atlas_%s.glass_transcribed_rna)
RETURNS VOID AS $$
BEGIN 	
	-- Update record
	EXECUTE 'UPDATE glass_atlas_%s.glass_transcribed_rna' 
	|| ' SET'
		|| ' glass_transcript_id = ' || rec.glass_transcript_id || ','
		|| ' strand = ' || rec.strand || ','
		|| ' transcription_start = ' || rec.transcription_start || ','
		|| ' transcription_end = ' || rec.transcription_end || ','
		|| ' start_end = public.cube(' || rec.transcription_start || '::float,' || rec.transcription_end || '::float),'
		|| ' modified = NOW()'
	|| ' WHERE id = ' || rec.id;
	
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
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap)
		LOOP		
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
				("chromosome_id", "strand", "start", "end", "start_end")
				VALUES (chr_id, strand, rec.transcription_start, rec.transcription_end, 
				public.cube(rec.transcription_start, rec.transcription_end))
				RETURNING * INTO transcribed_rna;
				
			-- Save the record of the sequencing run source
			INSERT INTO glass_atlas_%s.glass_transcribed_rna_source 
				("glass_transcribed_rna_id", "sequencing_run_id", "tag_count", "gaps") 
				VALUES (transcribed_rna.id, seq_run_id, rec.tag_count, rec.gaps);
							
		END LOOP;
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

CREATE FUNCTION glass_atlas_%s.join_overlapping_transcribed_rna(chr_id integer)
RETURNS VOID AS $$
 DECLARE
	transcribed_rna_pair glass_atlas_%s.glass_transcribed_rna_pair;
	consumed1 integer[];
BEGIN
	-- Loop until all pairs are consumed
	WHILE (consumed1 IS NULL OR consumed1 > array[]::integer[])
	LOOP
		consumed1 := array[]::integer[];
		FOR transcribed_rna_pair IN
			SELECT * FROM glass_atlas_%s.get_overlapping_transcribed_rna(chr_id)
		LOOP
			-- Transcript 1 overlapps with Transcript 2,
			-- and further has the same glass_transcript_id.
			-- Keep track of consumed transcripts to ensure we do not try to process an already deleted transcript
			consumed1 = (SELECT glass_atlas_%s.process_transcript_pair(transcript_pair, consumed1));
		END LOOP;
	END LOOP;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.process_transcribed_rna_pair(transcribed_rna_pair glass_atlas_%s.glass_transcribed_rna_pair, consumed integer[])
RETURNS integer[] AS $$
 DECLARE
	trans glass_atlas_%s.glass_transcribed_rna;
	merged_trans glass_atlas_%s.glass_transcribed_rna;
BEGIN
	merged_trans := transcribed_rna_pair.t1;
	trans := transcribed_rna_pair.t2;
	IF (consumed @> ARRAY[trans.id] = false 
		AND consumed @> ARRAY[merged_trans.id] = false) THEN
			merged_trans := (SELECT glass_atlas_%s.merge_transcribed_rna(merged_trans, trans));
			PERFORM glass_atlas_%s.update_transcribed_rna_source_records(merged_trans, trans);
			EXECUTE 'DELETE FROM glass_atlas_%s.glass_transcribed_rna WHERE id = ' || trans.id;
			PERFORM glass_atlas_%s.save_transcribed_rna(merged_trans);
			consumed = consumed || trans.id;
			consumed = consumed || merged_trans.id;
	END IF;
	RETURN consumed;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.associate_transcribed_rna(chr_id integer)
RETURNS VOID AS $$
	-- Match transcribed RNA to transcripts, preferring transcripts according to:
	-- 1. Largest transcript containing transcribed RNA
	-- 2. Transcript overlapping with transcribed RNA with minimal distance of extension
	UPDATE glass_atlas_%s.glass_transcribed_rna 
		SET glass_transcript_id = NULL, modified = NOW()
		WHERE chromosome_id = chr_id;
	
	UPDATE glass_atlas_%s.glass_transcribed_rna rna
		SET glass_transcript_id = transcript.id, modified = NOW()
		FROM (SELECT row_number() OVER (PARTITION BY rna.id) as row_num,
				rna.id as rna_id, t.id as id
			FROM glass_atlas_%s.glass_transcript t
			JOIN glass_atlas_%s.glass_transcribed_rna rna
			ON t.chromosome_id = rna.chromosome_id
			AND transcript.start_end OPERATOR(public.@>) rna.start_end
			WHERE rna.chromosome_id = chr_id
			ORDER BY (t.transcription_end - t.transcription_start) DESC
		) transcript
		WHERE transcript.rna_id = rna.id
		AND transcript.row_num = 1;
	
	UPDATE glass_atlas_%s.glass_transcribed_rna rna
		SET glass_transcript_id = transcript.id, modified = NOW()
		FROM (SELECT row_number() OVER (PARTITION BY rna.id) as row_num,
				rna.id as rna_id, t.id as id
			FROM glass_atlas_%s.glass_transcript t
			JOIN glass_atlas_%s.glass_transcribed_rna rna
			ON t.chromosome_id = rna.chromosome_id
			AND transcript.start_end OPERATOR(public.&&) rna.start_end
			WHERE rna.chromosome_id = chr_id
			ORDER BY (GREATEST((t.transcription_start - rna.transcription_start),0)
				+ GREATEST((rna.transcription_end - t.transcription_end),0)) ASC
		) transcript
		WHERE transcript.rna_id = rna.id
		AND transcript.row_num = 1;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.get_overlapping_transcribed_rna(chr_id integer)
RETURNS SETOF glass_atlas_%s.glass_transcribed_rna_pair AS $$
BEGIN
	RETURN QUERY
		EXECUTE '(SELECT (transcribed_rna1.*)::glass_atlas_%s.glass_transcribed_rna as t1,'
			|| ' (transcribed_rna2.*)::glass_atlas_%s.glass_transcribed_rna as t2'
		|| ' FROM glass_atlas_%s.glass_transcribed_rna transcribed_rna1'
		|| ' JOIN glass_atlas_%s.glass_transcribed_rna transcribed_rna2'
		|| ' ON transcribed_rna1.chromosome_id = transcribed_rna2.chromosome_id
		|| ' AND transcribed_rna1.glass_transcript_id = transcribed_rna2.glass_transcript_id'
		|| ' AND transcribed_rna1.strand = transcribed_rna2.strand'
		|| ' AND transcribed_rna1.start_end OPERATOR(public.&&) transcribed_rna2.start_end'
		|| ' AND transcribed_rna1.id != transcribed_rna2.id'
		|| ' WHERE transcribed_rna1.chromosome_id = ' || chr_id
			-- Prevent equivalent run arrays from appearing as two separate rows
			|| ' AND transcribed_rna1.id > transcribed_rna2.id)'
		|| ' ORDER BY transcribed_rna1.transcription_start ASC, transcribed_rna1.transcription_end DESC)';
END;
$$ LANGUAGE 'plpgsql';

CREATE FUNCTION glass_atlas_%s.mark_transcripts_as_spliced(chr_id integer)
RETURNS VOID AS $$
	UPDATE glass_atlas_%s.glass_transcript 
		SET spliced = NULL, modified = NOW()
		WHERE chromosome_id = chr_id;
	UPDATE glass_atlas_%s.glass_transcript 
		SET spliced = true, modified = NOW()
		WHERE chromosome_id = chr_id
			AND id IN (SELECT DISTINCT glass_transcript_id FROM glass_atlas_%s.glass_transcribed_rna);
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome]*133)

print sql
