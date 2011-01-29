'''
Created on Nov 12, 2010

@author: karmel

Convenience script for transcribed RNA functions.
'''
genome = 'gap_0'
cell_type = 'thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE TYPE glass_atlas_%s_%s.glass_transcribed_rna_pair AS ("t1" glass_atlas_%s_%s.glass_transcribed_rna, "t2" glass_atlas_%s_%s.glass_transcribed_rna);
CREATE TYPE glass_atlas_%s_%s.glass_transcribed_rna_group AS ("transcribed" glass_atlas_%s_%s.glass_transcribed_rna[], 
        "transcribed_ids" integer[], "glass_transcript_id" integer,
        "exon_id" integer, "exon_length" bigint, "ncrna_id" integer, "ncrna_length" bigint);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.update_transcribed_rna_source_records(merged_trans glass_atlas_%s_%s.glass_transcribed_rna, trans glass_atlas_%s_%s.glass_transcribed_rna)
RETURNS VOID AS $$
BEGIN 
	-- Update redundant records: those that already exist for the merge
	UPDATE glass_atlas_%s_%s.glass_transcribed_rna_source merged_assoc
		SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
			gaps = (merged_assoc.gaps + trans_assoc.gaps)
		FROM glass_atlas_%s_%s.glass_transcribed_rna_source trans_assoc
		WHERE merged_assoc.glass_transcribed_rna_id = merged_trans.id
			AND trans_assoc.glass_transcribed_rna_id = trans.id
			AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id;
	-- UPDATE redundant records: those that don't exist for the merge
	UPDATE glass_atlas_%s_%s.glass_transcribed_rna_source
		SET glass_transcribed_rna_id = merged_trans.id
		WHERE glass_transcribed_rna_id = trans.id
		AND sequencing_run_id 
		NOT IN (SELECT sequencing_run_id 
				FROM glass_atlas_%s_%s.glass_transcribed_rna_source
			WHERE glass_transcribed_rna_id = merged_trans.id);
	-- Delete those that remain for the removed transcript.
	DELETE FROM glass_atlas_%s_%s.glass_transcribed_rna_source
		WHERE glass_transcribed_rna_id = trans.id;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	
CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.merge_transcribed_rna(merged_trans glass_atlas_%s_%s.glass_transcribed_rna, trans glass_atlas_%s_%s.glass_transcribed_rna)
RETURNS glass_atlas_%s_%s.glass_transcribed_rna AS $$
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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.save_transcribed_rna(rec glass_atlas_%s_%s.glass_transcribed_rna)
RETURNS VOID AS $$
DECLARE
	glass_transcript_sql text;
BEGIN 	
	-- Update record
	IF rec.glass_transcript_id IS NULL THEN glass_transcript_sql := ' glass_transcript_id = NULL ';
	ELSE glass_transcript_sql := ' glass_transcript_id = ' || rec.glass_transcript_id;
	END IF;
	
	EXECUTE 'UPDATE glass_atlas_%s_%s.glass_transcribed_rna' 
	|| ' SET'
		|| glass_transcript_sql || ','
		|| ' strand = ' || rec.strand || ','
		|| ' transcription_start = ' || rec.transcription_start || ','
		|| ' transcription_end = ' || rec.transcription_end || ','
		|| ' start_end = public.cube(' || rec.transcription_start || '::float,' || rec.transcription_end || '::float),'
		|| ' modified = NOW()'
	|| ' WHERE id = ' || rec.id;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.save_transcribed_rna_from_sequencing_run(seq_run_id integer, chr_id integer, source_t text, max_gap integer)
RETURNS VOID AS $$
 DECLARE
	rec glass_atlas_%s_%s.glass_transcript_row;
	transcribed_rna glass_atlas_%s_%s.glass_transcribed_rna;
 BEGIN
 	FOR strand IN 0..1 
 	LOOP
		FOR rec IN 
			SELECT * FROM glass_atlas_%s_%s.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap)
		LOOP
		    IF rec IS NOT NULL THEN
    			-- Saved the Transcribed RNA
    			INSERT INTO glass_atlas_%s_%s.glass_transcribed_rna 
    				("chromosome_id", "strand", "transcription_start", "transcription_end", "start_end",
    				modified, created)
    				VALUES (chr_id, strand, rec.transcription_start, rec.transcription_end, 
    				public.cube(rec.transcription_start, rec.transcription_end), NOW(), NOW())
    				RETURNING * INTO transcribed_rna;
    				
    			-- Save the record of the sequencing run source
    			INSERT INTO glass_atlas_%s_%s.glass_transcribed_rna_source 
    				("glass_transcribed_rna_id", "sequencing_run_id", "tag_count", "gaps") 
    				VALUES (transcribed_rna.id, seq_run_id, rec.tag_count, rec.gaps);
			END IF;		
		END LOOP;
	END LOOP;
	
	RETURN;
END;
$$ LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.associate_transcribed_rna(chr_id integer)
RETURNS VOID AS $$
BEGIN
	-- Match transcribed RNA to transcripts, preferring transcripts according to:
	-- 1. Largest transcript containing transcribed RNA
	-- 2. Transcript overlapping with transcribed RNA with minimal distance of extension
	UPDATE glass_atlas_%s_%s.glass_transcribed_rna 
		SET glass_transcript_id = NULL, modified = NOW()
		WHERE chromosome_id = chr_id;
	
	UPDATE glass_atlas_%s_%s.glass_transcribed_rna rna
		SET glass_transcript_id = transcript.id, modified = NOW()
		FROM (SELECT row_number() OVER (
					PARTITION BY rna.id
					ORDER BY (t.transcription_end - t.transcription_start) DESC
				) as row_num,
				rna.id as rna_id, t.id as id
			FROM glass_atlas_%s_%s.glass_transcript t
			JOIN glass_atlas_%s_%s.glass_transcribed_rna rna
			ON t.chromosome_id = rna.chromosome_id
			AND t.strand = rna.strand
			AND t.start_end OPERATOR(public.@>) rna.start_end
			WHERE rna.chromosome_id = chr_id
			AND rna.glass_transcript_id IS NULL
		) transcript
		WHERE transcript.rna_id = rna.id
		AND transcript.row_num = 1;
	
	UPDATE glass_atlas_%s_%s.glass_transcribed_rna rna
		SET glass_transcript_id = transcript.id, modified = NOW()
		FROM (SELECT row_number() OVER (
					PARTITION BY rna.id
					ORDER BY (GREATEST((t.transcription_start - rna.transcription_start),0)
					+ GREATEST((rna.transcription_end - t.transcription_end),0)) ASC
				) as row_num,
				rna.id as rna_id, t.id as id
			FROM glass_atlas_%s_%s.glass_transcript t
			JOIN glass_atlas_%s_%s.glass_transcribed_rna rna
			ON t.chromosome_id = rna.chromosome_id
			AND t.strand = rna.strand
			AND t.start_end OPERATOR(public.&&) rna.start_end
			WHERE rna.chromosome_id = chr_id
			AND rna.glass_transcript_id IS NULL
		) transcript
		WHERE transcript.rna_id = rna.id
		AND transcript.row_num = 1;

	RETURN;
END;
$$ LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.mark_transcripts_as_spliced(chr_id integer)
RETURNS VOID AS $$
BEGIN
    UPDATE glass_atlas_%s_%s.glass_transcript 
        SET spliced = NULL, modified = NOW()
        WHERE chromosome_id = chr_id;
    UPDATE glass_atlas_%s_%s.glass_transcript t
        SET spliced = true, modified = NOW()
        FROM glass_atlas_%s_%s.glass_transcribed_rna trans_rna,
            (SELECT glass_transcribed_rna_id, sum(tag_count) as sum
            FROM glass_atlas_%s_%s.glass_transcribed_rna_source 
            GROUP BY glass_transcribed_rna_id
        ) trans_rna_source
        WHERE t.chromosome_id = chr_id
            AND t.id = trans_rna.glass_transcript_id
            AND trans_rna.id = trans_rna_source.glass_transcribed_rna_id
            AND trans_rna_source.sum > 1;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.stitch_transcribed_rna_together(chr_id integer, allowed_gap integer)
RETURNS integer AS $$
DECLARE
	consumed integer[];
	loop_count integer := 0;
BEGIN
	WHILE (consumed IS NULL OR consumed > array[]::integer[])
	LOOP
		consumed := array[]::integer[];
		consumed = (SELECT glass_atlas_%s_%s.looped_stitch_transcribed_rna_together('glass_atlas_%s_%s.get_rna_groups_by_transcript_id_split', 
		                                                                                chr_id, allowed_gap, consumed));
		loop_count = loop_count + 1;
	END LOOP;
	
	consumed := NULL;
	WHILE (consumed IS NULL OR consumed > array[]::integer[])
	LOOP
		consumed := array[]::integer[];
		consumed = (SELECT glass_atlas_%s_%s.looped_stitch_transcribed_rna_together('glass_atlas_%s_%s.get_rna_groups_by_transcript_id',
		                                                                            chr_id, 0, consumed));
		loop_count = loop_count + 1;
	END LOOP;

	RETURN loop_count;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.looped_stitch_transcribed_rna_together(method text, chr_id integer, allowed_gap integer, consumed integer[])
RETURNS integer[] AS $$
 DECLARE
	transcribed_rna_group record;
	trans glass_atlas_%s_%s.glass_transcribed_rna;
	merged_trans glass_atlas_%s_%s.glass_transcribed_rna;
	should_merge boolean := false;
	merged boolean := false;
	max_gap integer;
BEGIN
	<<group_loop>>
	FOR transcribed_rna_group IN 
		EXECUTE 'SELECT * FROM ' || method || '(' || chr_id || ')'
	LOOP
		-- Transcribed_rna_group is an array of transcribed RNA and ids of associated glass transcripts and exons
		-- such that the group of transcribed RNA all share the same associated exon id,
		-- and therefore are good candidates for stitching together.
		
		-- BAIL if any of the transcripts have already been consumed.
		IF consumed && transcribed_rna_group.transcribed_ids THEN CONTINUE group_loop;
		END IF;
		
		-- Try to group each transcript, bailing if the gap is passed.
		<<pair_loop>>
		FOR trans IN
			SELECT * FROM unnest(transcribed_rna_group.transcribed)
			ORDER BY start_end ASC
		LOOP
			max_gap := (SELECT GREATEST(COALESCE(.5*transcribed_rna_group.exon_length::numeric,
										.5*transcribed_rna_group.ncrna_length::numeric,
										allowed_gap), allowed_gap))::integer;
			
			IF merged_trans IS NULL THEN merged_trans := trans;
			ELSE
				should_merge := false;
				-- Does this transcript connect?
				IF (merged_trans.transcription_end >= trans.transcription_start) THEN should_merge := true;
				ELSE
					IF (trans.transcription_start - merged_trans.transcription_end) <= max_gap THEN should_merge := true;
					END IF;
				END IF;
				
				IF should_merge = true
					THEN 
						merged_trans := (SELECT glass_atlas_%s_%s.merge_transcribed_rna(merged_trans, trans));
						-- Delete/update old associations
						PERFORM glass_atlas_%s_%s.update_transcribed_rna_source_records(merged_trans, trans);
						EXECUTE 'DELETE FROM glass_atlas_%s_%s.glass_transcribed_rna WHERE id = ' || trans.id;
						merged := true;
						IF (consumed @> ARRAY[merged_trans.id]) = false THEN
							consumed := consumed || merged_trans.id;
						END IF;
						consumed := consumed || trans.id;
				ELSE
					-- We have reached a gap; close off any open merged_transcripts
					IF merged THEN
						PERFORM glass_atlas_%s_%s.save_transcribed_rna(merged_trans);
					END IF;
					-- And reset the merged transcript
					merged_trans := trans;
					merged := false;
				END IF;
			END IF;
		END LOOP;
		
		-- We may have one final merged transcript awaiting a save:
		IF merged THEN
			PERFORM glass_atlas_%s_%s.save_transcribed_rna(merged_trans);
		END IF;
		-- And reset the merged transcript
		merged_trans := NULL;
		merged := false;
	END LOOP;

	RETURN consumed;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.get_rna_groups_by_transcript_id_split(chr_id integer)
RETURNS SETOF glass_atlas_%s_%s.glass_transcribed_rna_group AS $$
BEGIN
    RETURN QUERY
    SELECT
        array_agg(rna.*) as transcribed,
        array_agg(rna.id) as transcribed_ids,
        rna.glass_transcript_id,
        exon.id as exon_id,
        exon.length as exon_length,
        ncrna.id as ncrna_id,
        ncrna.length as ncrna_length
    FROM "glass_atlas_%s_%s"."glass_transcribed_rna" rna
    LEFT OUTER JOIN (SELECT 
            glass_transcript_id, 
            exon.sequence_transcription_region_id,
            exon.start_end,
            (exon.exon_end - exon.exon_start) as length,
            (reg.transcription_end - reg.transcription_start) as sequence_length,
            exon.id
        FROM "glass_atlas_%s_%s"."glass_transcript_sequence" seq
        JOIN genome_reference_mm9.sequence_exon exon
        ON seq.sequence_transcription_region_id = exon.sequence_transcription_region_id
        JOIN genome_reference_mm9.sequence_transcription_region reg
        ON exon.sequence_transcription_region_id = reg.id
    ) exon
    ON rna.glass_transcript_id = exon.glass_transcript_id
    AND rna.start_end operator(public.&&) exon.start_end
    
    LEFT OUTER JOIN (SELECT 
            glass_transcript_id, 
            reg.id,
            reg.start_end,
            (reg.transcription_end - reg.transcription_start) as length
        FROM "glass_atlas_%s_%s"."glass_transcript_non_coding" nc
        JOIN genome_reference_mm9.non_coding_transcription_region reg
        ON nc.non_coding_transcription_region_id  = reg.id
    ) ncrna
    ON rna.glass_transcript_id = ncrna.glass_transcript_id
    AND rna.start_end operator(public.&&) ncrna.start_end
    
    WHERE rna.chromosome_id = chr_id
    GROUP BY rna.glass_transcript_id, exon.id, exon.length, exon.sequence_transcription_region_id, rna.strand, 
        exon.sequence_length, ncrna.id, ncrna.length
    HAVING count(rna.id) > 1
    ORDER BY exon.sequence_length, ncrna.length DESC NULLS LAST;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.get_rna_groups_by_transcript_id(chr_id integer)
RETURNS SETOF glass_atlas_%s_%s.glass_transcribed_rna_group AS $$
BEGIN
    -- Return groups of transcribed RNA that overlap, share a glass_transcript_id, and share sequencing runs,
    -- irrespective of ncRNA or exon boundaries
    RETURN QUERY
    SELECT
        array_agg(rna.*) as transcribed,
        array_agg(rna.id) as transcribed_ids,
        rna.glass_transcript_id,
        0 as exon_id,
        0::bigint as exon_length,
        0 as ncrna_id,
        0::bigint as ncrna_length
    FROM "glass_atlas_%s_%s"."glass_transcribed_rna" rna    
    WHERE rna.chromosome_id = chr_id
    GROUP BY rna.glass_transcript_id, rna.strand
    HAVING count(rna.id) > 1;
END;
$$ LANGUAGE 'plpgsql';


""" % tuple([genome, cell_type]*60)

if __name__ == '__main__':
    print sql(genome, cell_type)
