'''
Created on Nov 12, 2010

@author: karmel

Prep table functions, extracted for ease of reading.
'''
def sql(genome, cell_type, suffix):
    return """

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.draw_transcript_edges(chr_id integer, min_one_run_tags integer, max_edge integer)
RETURNS VOID AS $$
DECLARE
    strand integer;
    last_trans atlas_{0}_{1}{suffix}.atlas_transcript;
    trans atlas_{0}_{1}{suffix}.atlas_transcript;
    transcript atlas_{0}_{1}{suffix}.atlas_transcript;
BEGIN
    FOR strand in 0..1
    LOOP
        last_trans := NULL;
        FOR trans IN 
            SELECT * FROM atlas_{0}_{1}{suffix}.get_close_transcripts(chr_id, strand, min_one_run_tags)
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
                    transcript := (SELECT atlas_{0}_{1}{suffix}.insert_transcript(last_trans));
                    last_trans := trans;
                END IF;
            END IF;
        END LOOP;
        -- And the last one..
        IF last_trans.transcription_start IS NOT NULL THEN
            transcript := (SELECT atlas_{0}_{1}{suffix}.insert_transcript(last_trans));
        END IF;
    END LOOP;
        
    PERFORM atlas_{0}_{1}{suffix}.insert_transcript_source_records(chr_id);
    PERFORM atlas_{0}_{1}{suffix}.insert_associated_transcript_regions(chr_id);
    PERFORM atlas_{0}_{1}{suffix}.link_post_gene_transcripts(chr_id, max_edge);
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.get_close_transcripts(chr_id integer, strand integer, min_one_run_tags integer)
RETURNS SETOF atlas_{0}_{1}{suffix}.atlas_transcript AS $$
DECLARE
    above_thresh_table text;
    trans record;
    transcript atlas_{0}_{1}{suffix}.atlas_transcript;    
BEGIN
        -- From prep tables, get close-enough transcripts
    above_thresh_table = 'above_thresh_table_' || chr_id || '_' || strand || '_' || (1000*RANDOM())::int;
        
    EXECUTE 'CREATE TEMP TABLE ' || above_thresh_table  || ' 
        as SELECT t.id, t.strand, t.transcription_start, t.transcription_end, t.refseq,
                circle(point(t.transcription_end, t.density), t.edge) as density_circle, 
                point(t.transcription_start,t.density) as start_density
                FROM  atlas_{0}_{1}_prep.atlas_transcript_' || chr_id || ' t
                JOIN atlas_{0}_{1}_prep.atlas_transcript_source_' || chr_id || ' s
                    ON t.id = s.atlas_transcript_id
                WHERE t.strand = ' || strand || '
                GROUP BY t.id, t.strand, t.transcription_start, t.transcription_end, t.refseq, t.density, t.edge  
                -- Omit one-tag-wonders and one-run wonders unless they have at least 5 tags
                HAVING avg(s.tag_count) > 1 AND (count(s.sequencing_run_id) > 1 OR avg(s.tag_count) >= ' || min_one_run_tags || ')
            ';
    EXECUTE 'CREATE INDEX ' || above_thresh_table || '_density_circle_idx ON ' || above_thresh_table || ' USING gist(density_circle)';
    EXECUTE 'CREATE INDEX ' || above_thresh_table || '_start_density_idx ON ' || above_thresh_table || ' USING gist(start_density)';
        
    FOR trans IN 
        EXECUTE 'SELECT t1.id, t1.strand, t1.transcription_start, t1.transcription_end, t1.refseq,
                    GREATEST(max(t2.transcription_end), t1.transcription_end) as max_end
            FROM ' || above_thresh_table  || ' t1
            LEFT OUTER JOIN ' || above_thresh_table  || ' t2 
            ON t1.density_circle @> t2.start_density 
                AND t1.strand = t2.strand 
                AND t1.refseq = t2.refseq
                AND t1.transcription_start <= t2.transcription_start -- Omit upstream transcripts in the circle 
            GROUP by t1.id, t1.strand, t1.transcription_start, t1.transcription_end, t1.refseq
            ORDER by t1.transcription_start ASC'
    LOOP
        IF trans.id IS NOT NULL THEN
            -- Reset transcript record.
            transcript := NULL;
            transcript.chromosome_id = chr_id;
            transcript.strand = trans.strand;
            transcript.transcription_start = trans.transcription_start;
            transcript.transcription_end = trans.max_end;
            transcript.refseq = trans.refseq;
            RETURN NEXT transcript;
        END IF;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.insert_transcript(rec atlas_{0}_{1}{suffix}.atlas_transcript)
RETURNS atlas_{0}_{1}{suffix}.atlas_transcript AS $$
DECLARE
    transcript atlas_{0}_{1}{suffix}.atlas_transcript;
BEGIN
    -- Update record
    EXECUTE 'INSERT INTO atlas_{0}_{1}{suffix}.atlas_transcript_' || rec.chromosome_id 
    || ' (chromosome_id, strand, transcription_start, transcription_end,
            start_end, refseq, modified, created) 
        VALUES (' || rec.chromosome_id || ',' || rec.strand || ','
        || rec.transcription_start || ',' || rec.transcription_end || ',' 
        || ' int8range(' || rec.transcription_start || ',' ||  rec.transcription_end || ', ''[]''),'
         || COALESCE(rec.refseq, 'NULL') || ', NOW(), NOW()) RETURNING *' INTO transcript;
    RETURN transcript;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.insert_transcript_source_records(chr_id integer)
RETURNS VOID AS $$
DECLARE
    temp_table text;
BEGIN 
    temp_table = 'source_table_' || chr_id || '_' || (1000*RANDOM())::int;
    EXECUTE 'CREATE TEMP TABLE ' || temp_table || ' AS
        SELECT trans.id as transcript_id, prep.id as prep_id
                FROM atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' trans
                JOIN atlas_{0}_{1}_prep.atlas_transcript_' || chr_id || ' prep
                ON trans.start_end @> prep.start_end
                AND trans.strand = prep.strand';
    EXECUTE 'CREATE INDEX ' || temp_table || '_prep_idx ON ' || temp_table || ' USING btree(prep_id)';
            
    EXECUTE 'INSERT INTO atlas_{0}_{1}{suffix}.atlas_transcript_source_' || chr_id || '
            (chromosome_id, atlas_transcript_id, sequencing_run_id, tag_count, gaps)
            SELECT ' || chr_id || ', temp_t.transcript_id, source.sequencing_run_id, 
                SUM(source.tag_count), COUNT(source.atlas_transcript_id) - 1
            FROM atlas_{0}_{1}_prep.atlas_transcript_source_' || chr_id || ' source 
            JOIN ' || temp_table || ' temp_t
            ON source.atlas_transcript_id = temp_t.prep_id
        GROUP BY temp_t.transcript_id, source.sequencing_run_id';
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.insert_associated_transcript_regions(chr_id integer)
RETURNS VOID AS $$
DECLARE
    region_types text[] := ARRAY['sequence','non_coding'];
    counter integer;
    table_type text;
BEGIN
    -- Associate any sequencing regions
    FOR counter IN array_lower(region_types,1)..array_upper(region_types,1)
    LOOP
        table_type := region_types[counter];
        EXECUTE 'INSERT INTO atlas_{0}_{1}{suffix}.atlas_transcript_'
        || table_type || ' (atlas_transcript_id, '
        || table_type || '_transcription_region_id, relationship, major)
            (SELECT trans.id, reg.id, 
                (CASE WHEN reg.start_end = trans.start_end THEN 
                atlas_{0}_{1}{suffix}.atlas_transcript_transcription_region_relationship(''is equal to'') 
                WHEN reg.start_end <@ trans.start_end THEN 
                atlas_{0}_{1}{suffix}.atlas_transcript_transcription_region_relationship(''contains'') 
                WHEN reg.start_end @> trans.start_end THEN 
                atlas_{0}_{1}{suffix}.atlas_transcript_transcription_region_relationship(''is contained by'') 
                ELSE atlas_{0}_{1}{suffix}.atlas_transcript_transcription_region_relationship(''overlaps with'') END),
                (CASE WHEN (upper(reg.start_end * trans.start_end) - lower(reg.start_end * trans.start_end)) 
                    > (upper(reg.start_end) - lower(reg.start_end))::numeric/2 THEN true
                ELSE false END)
            FROM atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' trans
            JOIN genome_reference_{0}.' || table_type || '_transcription_region reg
            ON reg.start_end && trans.start_end
            WHERE reg.chromosome_id = ' || chr_id || '
            AND (reg.strand IS NULL OR reg.strand = trans.strand))';
            
    END LOOP;
                
    -- We also want to mark whether a transcript is gene distal.
    -- This means it does not overlap with the region of any refseq transcripts
    -- plus 1000bp on either side. NOT strand specific.
    EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' t
        SET distal = true';
    EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' t
        SET distal = false
        FROM genome_reference_{0}.sequence_transcription_region seq
        WHERE t.start_end && seq.start_end_1000
            AND seq.chromosome_id = ' || chr_id;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.link_post_gene_transcripts(chr_id integer, distance integer)
RETURNS VOID AS $$
DECLARE
    temp_table text;
BEGIN 
    -- Post-gene transcripts are demarcated as separate, but need to be tied
    -- to the genes they were split from.
    -- Here, we assign a parent_id to the post-gene transcripts if they follow
    -- a genic transcript within distance basepairs.
     
    temp_table = 'post_gene_table_' || chr_id || '_' || (1000*RANDOM())::int;
    EXECUTE 'CREATE TEMP TABLE ' || temp_table || ' AS
        SELECT distinct ON (t.id) 
            t.id as post_gene_id,
            t2.id as gene_id
        FROM atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' t
        JOIN atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' t2
        ON t.chromosome_id = t2.chromosome_id
        AND t.start_end && int8range(t2.strand*(t2.transcription_start - ' || distance || '
                ) + abs(t2.strand - 1)*t2.transcription_end, 
            t2.strand*t2.transcription_start + abs(t2.strand - 1)*(t2.transcription_end + ' || distance || '
                ))
        AND t.strand = t2.strand
        WHERE t.refseq = false
        AND t2.refseq = true;';
    EXECUTE 'CREATE INDEX ' || temp_table || '_idx ON ' || temp_table || ' USING btree(post_gene_id)';
    
    EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' transcript
        SET parent_id = temp_t.gene_id
        FROM ' || temp_table || ' temp_t
        WHERE transcript.id = temp_t.post_gene_id';

    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.calculate_scores_rpkm(chr_id integer, field text)
RETURNS VOID AS $$
DECLARE
    millions_of_tags float;
    temp_table text;
BEGIN 
    -- RPKM. Can be modified as necessary.
    
    -- Use prep tables to determine raw runs and tag counts
    millions_of_tags := (SELECT sum(tag_count)::numeric/1000000 FROM atlas_{0}_{1}_prep.atlas_transcript_source);
    
    temp_table = 'score_table_' || chr_id || '_' || (1000*RANDOM())::int;
    EXECUTE 'CREATE TEMP TABLE ' || temp_table || ' AS
        SELECT 
            transcript.id,
            SUM(source.tag_count) as sum_tags, 
            (transcript.transcription_end - transcript.transcription_start + 1)::numeric/1000 as kb_width
        FROM atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' transcript 
        JOIN atlas_{0}_{1}{suffix}.atlas_transcript_source_' || chr_id || ' source
        ON transcript.id = source.atlas_transcript_id
        GROUP BY transcript.id, transcript.transcription_end, transcript.transcription_start';
    EXECUTE 'CREATE INDEX ' || temp_table || '_idx ON ' || temp_table || ' USING btree(id)';
    
	EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' transcript
	    SET ' || field || ' = temp_t.sum_tags::numeric/temp_t.kb_width/' || millions_of_tags || '::numeric
	    FROM ' || temp_table || ' temp_t
	    WHERE transcript.id = temp_t.id';

	RETURN;
END;
$$ LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.calculate_scores_atlas(chr_id integer)
RETURNS VOID AS $$
BEGIN 
    -- Transformation of RPKM.
    -- Severely penalizes transcripts less than 200bp long,
    -- and scales RPKM by log100 of length, such that very long,
    -- lowly transcribed transcripts get a boost.
    
    EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' transcript
        SET score = rpkm*log(100, 
                            greatest(1,(transcript.transcription_end 
                                        - transcript.transcription_start + 1) - 200))';

    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.calculate_scores(chr_id integer)
RETURNS VOID AS $$
    BEGIN
        PERFORM atlas_{0}_{1}{suffix}.calculate_scores_rpkm(chr_id, 'rpkm');
        PERFORM atlas_{0}_{1}{suffix}.calculate_scores_atlas(chr_id);
    RETURN;
END;
$$ LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION atlas_{0}_{1}{suffix}.calculate_standard_error(chr_id integer)
RETURNS VOID AS $$
DECLARE
    total_runs integer;
    temp_table text;
BEGIN 
    -- We want an easily accessible measure of the expected standard error of this transcript.
    -- Use notx replicates to get a standard deviation of tags, scaled by total tags in each run,
    -- then normalized to 10^7 total tags.
    -- Then we take the sample standard deviation over the square root of the number of samples to get 
    -- standard error of the mean (SEM).
    
    -- This value should be scaled by total tags in the target run for it to be meaningful
    -- for a particular run!
    
    -- Note that we do lots of aggregating and unnesting here before taking the stddev_samp.
    -- This is so that we can pad out the number of samples to the total_runs for
    -- each transcript to get an accurate calculation using stddev_samp.
    
    -- For transcripts that don't show up at all in the notx runs, we default to zero.
    -- This is not theoretically perfect, but will suffice for our purposes.
    
    total_runs := (SELECT count(*) FROM genome_reference_{0}.sequencing_run run);
    
    temp_table = 'deviation_table_' || chr_id || '_' || (1000*RANDOM())::int; 
    
    EXECUTE 'CREATE TEMP TABLE ' || temp_table || ' AS
        SELECT t.id, count(s.sequencing_run_id), 
            -- We want an array padded out with 0s to the total_run.
            -- In postgresql, this means we get our actual array, concat
            -- more than enough zeroes, and trim down to the desired length.
            (array_agg((s.tag_count::numeric/run.total_tags)*(10^7)) 
                || array_fill(0::float,array[' || total_runs || ']) -- concat a bunch of zeroes
            )[0:' || total_runs || '] -- Trim to desired length 
            as norm_tags
        FROM atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || '  t
        JOIN atlas_{0}_{1}{suffix}.atlas_transcript_source_' || chr_id || ' s
            ON t.id = s.atlas_transcript_id
        JOIN genome_reference_{0}.sequencing_run run
            ON s.sequencing_run_id = run.id
        GROUP BY t.id';

    -- Set all scores to zero at first, since some we will not have data on,
    -- and want those to be zero
    EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' 
        SET standard_error = 0';
        
    EXECUTE 'UPDATE atlas_{0}_{1}{suffix}.atlas_transcript_' || chr_id || ' transcript
        SET standard_error = der2.standard_error
        
        FROM (SELECT der.id, stddev(der.tags)/sqrt(count(der.tags)) as standard_error 
            FROM (select temp_t.id, unnest(temp_t.norm_tags) as tags from ' || temp_table || ' temp_t) der
            GROUP BY der.id
        ) der2
        WHERE transcript.id = der2.id';
        
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

""".format(genome, cell_type, suffix=suffix)
