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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.get_density(trans glass_atlas_%s_%s_staging.glass_transcript, density_multiplier integer)
RETURNS float AS $$
DECLARE
    sum integer;
    count integer;
BEGIN 
	EXECUTE 'SELECT SUM(tag_count) - COALESCE(SUM(polya_count),0) FROM glass_atlas_%s_%s_staging.glass_transcript_source_' || trans.chromosome_id || '  source
	        JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = ' || trans.id || ' AND run.use_for_scoring = true' INTO sum;
	EXECUTE 'SELECT COUNT(sequencing_run_id) FROM glass_atlas_%s_%s_staging.glass_transcript_source_' || trans.chromosome_id || '  source
	        JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = ' || trans.id || ' AND run.use_for_scoring = true' INTO count;
	RETURN GREATEST(0,(density_multiplier*sum::numeric)/(count*(trans.transcription_end - trans.transcription_start)::numeric)); 
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.get_polya(trans glass_atlas_%s_%s_staging.glass_transcript)
RETURNS boolean AS $$
DECLARE
	polya boolean;
BEGIN 
	EXECUTE 'SELECT COALESCE(SUM(polya_count),0)::numeric/SUM(tag_count)::numeric >= .5
	        FROM glass_atlas_%s_%s_staging.glass_transcript_source_' || trans.chromosome_id || ' source
	        JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = ' || trans.id || ' AND run.use_for_scoring = true' INTO polya; 
	RETURN polya;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.draw_transcript_edges(chr_id integer)
RETURNS VOID AS $$
DECLARE
    strand integer;
    last_trans glass_atlas_%s_%s_staging.glass_transcript;
    trans glass_atlas_%s_%s_staging.glass_transcript;
    transcript glass_atlas_%s_%s_staging.glass_transcript;
BEGIN
    FOR strand in 0..1
    LOOP
        last_trans := NULL;
        FOR trans IN 
            SELECT * FROM glass_atlas_%s_%s_staging.get_close_transcripts(chr_id, strand)
        LOOP
            -- Initialize the transcript to be saved if necessary
            IF last_trans IS NULL THEN 
                last_trans := trans;
            ELSE
                
                -- Include this tag if it overlaps or has < max_gap bp gap
                -- Else, this is a new transcript; close off the current and restart.
                IF last_trans.transcription_end >= trans.transcription_start THEN 
                    last_trans.transcription_start := (SELECT LEAST(last_trans.transcription_start, trans.transcription_start));
                    last_trans.transcription_end := (SELECT GREATEST(last_trans.transcription_end, trans.transcription_end));
                ELSE
                    transcript := (SELECT glass_atlas_%s_%s_staging.insert_transcript(last_trans));
                    last_trans := trans;
                END IF;
            END IF;
        END LOOP;
        -- And the last one..
        IF last_trans.transcription_start IS NOT NULL THEN
            transcript := (SELECT glass_atlas_%s_%s_staging.insert_transcript(last_trans));
        END IF;
    END LOOP;
        
    PERFORM glass_atlas_%s_%s_staging.insert_transcript_source_records(chr_id);
    PERFORM glass_atlas_%s_%s_staging.insert_associated_transcript_regions(chr_id);
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.get_close_transcripts(chr_id integer, strand integer)
RETURNS SETOF glass_atlas_%s_%s_staging.glass_transcript AS $$
DECLARE
    trans record;
    transcript glass_atlas_%s_%s_staging.glass_transcript;    
BEGIN
        -- From prep tables, get close-enough transcripts
    FOR trans IN 
        EXECUTE 'SELECT t1.id, t1.strand, t1.transcription_start, t1.transcription_end, 
                    GREATEST(max(t2.transcription_end), t1.transcription_end) as max_end,
                    count(s.sequencing_run_id) as run_count
            FROM glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' t1
            LEFT OUTER JOIN (
                SELECT * FROM glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' 
                WHERE id IN (SELECT t.id
                FROM  glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' t
                JOIN glass_atlas_%s_%s_prep.glass_transcript_source_' || chr_id || ' s
                    ON t.id = s.glass_transcript_id
                GROUP BY t.id
                HAVING sum(s.tag_count)/count(s.sequencing_run_id)::numeric > 1 AND count(s.sequencing_run_id) > 1) -- Omit one-tag-wonders and one-run-transcripts
                ) t2 
            ON t1.density_circle @> t2.start_density 
                AND t1.strand = t2.strand 
            JOIN glass_atlas_%s_%s_prep.glass_transcript_source_' || chr_id || ' s
                ON t1.id = s.glass_transcript_id
            WHERE t1.strand = ' || strand || '
            GROUP by t1.id, t1.strand, t1.transcription_start, t1.transcription_end
            HAVING sum(s.tag_count) > 1  -- Omit one-tag-wonders
            ORDER by t1.transcription_start ASC'
    LOOP
        IF trans.id IS NOT NULL THEN
            -- Reset transcript record.
            transcript := NULL;
            transcript.chromosome_id = chr_id;
            transcript.strand = trans.strand;
            transcript.transcription_start = trans.transcription_start;
            -- Take max end unless this transcript only belongs to one run;
            -- In that case, leave it as is.
            IF trans.run_count > 1 THEN
                transcript.transcription_end = trans.max_end;
            ELSE transcript.transcription_end = trans.transcription_end;
            END IF;
            
            RETURN NEXT transcript;
        END IF;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.insert_transcript(rec glass_atlas_%s_%s_staging.glass_transcript)
RETURNS glass_atlas_%s_%s_staging.glass_transcript AS $$
DECLARE
    transcript glass_atlas_%s_%s_staging.glass_transcript;
BEGIN
    -- Update record
    EXECUTE 'INSERT INTO glass_atlas_%s_%s_staging.glass_transcript_' || rec.chromosome_id 
    || ' (chromosome_id, strand, transcription_start, transcription_end, '
        || ' start_end, modified, created) '
    || 'VALUES (' || rec.chromosome_id || ',' || rec.strand || ','
        || rec.transcription_start || ',' || rec.transcription_end || ','
        || ' public.make_box(' || rec.transcription_start || ', 0' 
            || ',' ||  rec.transcription_end || ', 0),'
        || ' NOW(), NOW()) RETURNING *' INTO transcript;
    RETURN transcript;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.insert_transcript_source_records(chr_id integer)
RETURNS VOID AS $$
BEGIN 
    EXECUTE 'INSERT INTO glass_atlas_%s_%s_staging.glass_transcript_source_' || chr_id || '
            (chromosome_id, glass_transcript_id, sequencing_run_id, tag_count, gaps, polya_count)
            SELECT ' || chr_id || ', der.transcript_id, der.sequencing_run_id, 
                SUM(der.tag_count), COUNT(der.glass_transcript_id) - 1,
                SUM(der.polya_count)
            FROM (
                SELECT trans.id as transcript_id,* 
                FROM glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' trans
                JOIN (SELECT * FROM glass_atlas_%s_%s_prep.glass_transcript_' || chr_id || ' t
                    JOIN glass_atlas_%s_%s_prep.glass_transcript_source_' || chr_id || ' s
                    ON t.id = s.glass_transcript_id) source
                ON source.strand = trans.strand
            AND source.start_end <@ trans.start_end) der
        GROUP BY der.transcript_id, der.sequencing_run_id';
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.insert_associated_transcript_regions(chr_id integer)
RETURNS VOID AS $$
DECLARE
    region_types text[] := ARRAY['sequence','non_coding','conserved','patterned','duped'];
    counter integer;
    table_type text;
BEGIN
    -- Associate any sequencing regions
    FOR counter IN array_lower(region_types,1)..array_upper(region_types,1)
    LOOP
        table_type := region_types[counter];
        EXECUTE 'INSERT INTO glass_atlas_%s_%s_staging.glass_transcript_'
        || table_type || ' (glass_transcript_id, '
        || table_type || '_transcription_region_id, relationship)
            (SELECT trans.id, reg.id, 
                (CASE WHEN reg.start_end ~= trans.start_end THEN 
                glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''is equal to'') 
                WHEN reg.start_end <@ trans.start_end THEN 
                glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''contains'') 
                WHEN reg.start_end @> trans.start_end THEN 
                glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''is contained by'') 
                ELSE glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''overlaps with'') END)
            FROM glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' trans
            JOIN genome_reference_mm9.' || table_type || '_transcription_region reg
            ON reg.start_end && trans.start_end
            WHERE reg.chromosome_id = ' || chr_id || '
            AND (reg.strand IS NULL OR reg.strand = trans.strand))';
            
    END LOOP;
    
    -- Special case for infrastructure regions
    table_type := 'infrastructure';
    EXECUTE 'INSERT INTO glass_atlas_%s_%s_staging.glass_transcript_'
        || table_type || ' (glass_transcript_id, '
        || table_type || '_transcription_region_id, relationship)
            (SELECT trans.id, reg.id, 
                (CASE WHEN reg.start_end ~= trans.start_end THEN 
                glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''is equal to'') 
                WHEN reg.start_end <@ trans.start_end THEN 
                glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''contains'') 
                WHEN reg.start_end @> trans.start_end THEN 
                glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''is contained by'') 
                ELSE glass_atlas_%s_%s_staging.glass_transcript_transcription_region_relationship(''overlaps with'') END)
            FROM glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' trans
            JOIN genome_reference_mm9.patterned_transcription_region_' || chr_id || ' reg
            ON reg.start_end && trans.start_end
            WHERE reg.type IN (''tRNA'',''rRNA'',''snRNA'',''srpRNA'',''scRNA'',''RNA'') 
            AND (reg.strand IS NULL OR reg.strand = trans.strand))';
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.calculate_scores(chr_id integer)
RETURNS VOID AS $$
DECLARE
    total_runs integer;
BEGIN 
    -- Tag count is scaled avg and max tags: sqrt(avg_tags * max_tags)
    -- Score is tag count divided by the lesser of length/1000 and 2*log(length),
    -- which allows lower tag counts per bp for longer transcripts.
    
    total_runs := (SELECT count(DISTINCT sequencing_run_id) FROM glass_atlas_%s_%s_staging.glass_transcript_source);
	EXECUTE 'UPDATE glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' transcript
		    SET score = derived.score 
		    FROM (SELECT 
				    transcript.id,
				    GREATEST(0,
                        SQRT((SUM(source.tag_count - COALESCE(source.polya_count,0))::numeric/' || total_runs || ')
                        *MAX(source.tag_count - COALESCE(source.polya_count,0))::numeric)
                        /LEAST(
                            GREATEST(1000, transcript.transcription_end - transcript.transcription_start)::numeric/1000,
                            2*LOG(transcript.transcription_end - transcript.transcription_start)
                            )
                    ) as score
			    FROM glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' transcript 
				JOIN glass_atlas_%s_%s_staging.glass_transcript_source source
			    ON source.glass_transcript_id = transcript.id
			    JOIN glass_atlas_mm9.sequencing_run run
			    ON source.sequencing_run_id = run.id
			    WHERE run.use_for_scoring = true
				    AND transcript.chromosome_id = ' || chr_id || ' 
				    --AND transcript.score IS NULL
			    GROUP BY transcript.id, transcript.transcription_end, transcript.transcription_start
		    ) derived
		    WHERE transcript.id = derived.id';
    EXECUTE 'UPDATE glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' transcript
            SET score = 0 WHERE transcript.score IS NULL';
	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.calculate_scores_sample(chr_id integer)
RETURNS VOID AS $$
BEGIN 
    -- Score = Ratio of max tag count for this transcript to
    -- expected tag count given the length of the region.
    -- NOTE: This assumes the expected_tag_count table is accurate and available.
	EXECUTE 'UPDATE glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' transcript'
		|| ' SET score = source.max_tags::numeric/(exp.tag_count * ' 
		    || ' ((transcript.transcription_end - transcript.transcription_start + 1)::numeric/exp.sample_size)) '
		|| ' FROM (SELECT '
				|| ' glass_transcript_id, MAX(tag_count) as max_tags '
			|| ' FROM glass_atlas_%s_%s_staging.glass_transcript_source '
			|| ' GROUP BY glass_transcript_id) source, '
			|| ' glass_atlas_mm9.expected_tag_count exp'
		|| ' WHERE transcript.id = source.glass_transcript_id'
		    || ' AND transcript.chromosome_id = exp.chromosome_id'
		    || ' AND transcript.strand = exp.strand';

	RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.set_density(chr_id integer, density_multiplier integer, null_only boolean)
RETURNS VOID AS $$
DECLARE
    where_clause text;
BEGIN
    IF null_only = true THEN where_clause := 'start_end_density IS NULL';
    ELSE where_clause := '1=1';
    END IF;
    
    EXECUTE 'UPDATE glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' t 
            SET start_end_density = public.make_box(transcription_start, 
                glass_atlas_%s_%s_staging.get_density(t.*, ' || density_multiplier || ')::numeric,
                transcription_end,
                glass_atlas_%s_%s_staging.get_density(t.*, ' || density_multiplier || ')::numeric), 
                density = glass_atlas_%s_%s_staging.get_density(t.*, ' || density_multiplier || ')::numeric,
                polya = glass_atlas_%s_%s_staging.get_polya(t.*)
            WHERE ' || where_clause;
END;
$$ LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.mark_transcripts_spliced(chr_id integer, score_threshold numeric)
RETURNS VOID AS $$
BEGIN
    -- Mark transcripts as spliced if sufficiently high-scoring RNA exists
    EXECUTE 'UPDATE glass_atlas_%s_%s_staging.glass_transcript_' || chr_id || ' transcript 
        SET spliced = true
        FROM glass_atlas_%s_%s_staging.glass_transcribed_rna_' || chr_id || ' transcribed_rna
        WHERE transcribed_rna.glass_transcript_id = transcript.id
            AND transcribed_rna.score >= ' || score_threshold;
    RETURN;
END;
$$ LANGUAGE 'plpgsql'; 

""" % tuple([genome, cell_type]*65)

if __name__ == '__main__':
    print sql(genome, cell_type)
