-- Not run from within the codebase, but kept here in case functions need to be recreated.

DROP FUNCTION IF EXISTS glass_atlas_mm9.determine_transcripts_from_sequencing_run(integer, text, integer);
DROP TYPE IF EXISTS glass_atlas_mm9.glass_transcript_row;

CREATE TYPE glass_atlas_mm9.glass_transcript_row AS ("chromosome_id" integer, "strand_0" boolean, "strand_1" boolean, 
	transcription_start bigint, transcription_end bigint, tag_count integer, gaps integer);

CREATE FUNCTION glass_atlas_mm9.determine_transcripts_from_sequencing_run(chr_id integer, source_t text, strand integer)
RETURNS SETOF glass_atlas_mm9.glass_transcript_row AS $$
 DECLARE
   rec record;
   row glass_atlas_mm9.glass_transcript_row;
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
		|| strand 
		|| ' ORDER BY start;'
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
			IF ((last_end + 200) >= rec."start") THEN
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
			IF (strand = 0) THEN 
				row.strand_0 := true;
				row.strand_1 := false;
			ELSE 
				row.strand_0 := false;
				row.strand_1 := true;
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
