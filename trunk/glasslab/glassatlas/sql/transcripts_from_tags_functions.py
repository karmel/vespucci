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
    EXECUTE 'UPDATE glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || ' merged_assoc
        SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
            gaps = (merged_assoc.gaps + trans_assoc.gaps),
            polya_count = (merged_assoc.polya_count + trans_assoc.polya_count)
        FROM glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || ' trans_assoc
        WHERE merged_assoc.glass_transcript_id = ' || trans.id || '
            AND trans_assoc.glass_transcript_id = ' || old_id || '
            AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id';
    -- UPDATE redundant records: those that don't exist for the merge
    EXECUTE 'UPDATE glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || '
        SET glass_transcript_id = ' || trans.id || '
        WHERE glass_transcript_id = ' || old_id || '
        AND sequencing_run_id 
        NOT IN (SELECT sequencing_run_id 
                FROM glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || '
            WHERE glass_transcript_id = ' || trans.id || ')';
    -- Delete those that remain for the removed transcript.
    EXECUTE 'DELETE FROM glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || '
        WHERE glass_transcript_id = ' || old_id;
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
    EXECUTE 'SELECT SUM(tag_count) - SUM(polya_count) FROM glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || ' source
            JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = ' || trans.id || ' 
                AND run.use_for_scoring = true' INTO sum;
    EXECUTE 'SELECT COUNT(sequencing_run_id) FROM glass_atlas_%s_%s_prep.glass_transcript_source_' || trans.chromosome_id || ' source
            JOIN glass_atlas_mm9.sequencing_run run
                ON source.sequencing_run_id = run.id
            WHERE glass_transcript_id = ' || trans.id || ' AND run.use_for_scoring = true' INTO count;
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

    RETURN QUERY SELECT * FROM glass_atlas_%s_%s_prep.determine_transcripts_from_table(chr_id, strand, source_t, max_gap, tag_extension,'', false, start_end);
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
    polya_string text := '';
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
    
    IF field_prefix = '' THEN
        polya_string = ', polya';
    END IF; 
    
    -- Select each tag set, grouped by start and polya, if that is a field.
    -- We group here to speed up processing on tables where many tags start at the same location.
    FOR rec IN 
        EXECUTE 'SELECT array_agg(id) as ids, ' || chr_id || ' as chromosome_id, ' || strand ||' as strand,
        "' || field_prefix || 'start" as transcription_start, max("' || field_prefix || 'end") as transcription_end, 
         count(id) as tag_count ' || polya_string || '
         FROM "' || source_t || '_' || chr_id
        || '" WHERE strand = ' || strand 
        || start_end_clause
        || ' GROUP BY "' || field_prefix || 'start"' || polya_string || '
        ORDER BY ' || field_prefix || 'start ASC;'
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
                tag_count := tag_count + rec.tag_count;
                IF field_prefix = '' THEN
                    -- This is a tag row, with the polya t/f 
                    IF (rec.polya = true) THEN
                        polya_count := polya_count + rec.tag_count;
                    END IF;
                END IF;
                IF (rec.transcription_start > last_end) THEN
                    gaps := gaps + 1;
                END IF;
                last_start := (SELECT LEAST(last_start, rec.transcription_start));
                last_end := (SELECT GREATEST(last_end, rec.transcription_end));
                ids = ids || rec.ids::integer[];
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
                tag_count := rec.tag_count;
                IF field_prefix = '' THEN
                    polya_count := (SELECT CASE WHEN rec.polya = true THEN rec.tag_count ELSE 0 END);
                ELSE polya_count := 0;
                END IF;
                gaps := 0;
                ids := rec.ids::integer[];
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
                EXECUTE 'INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_source_' || rec.chromosome_id || '
                    (chromosome_id, "glass_transcript_id", "sequencing_run_id", "tag_count", "gaps", "polya_count") 
                    VALUES (' || transcript.chromosome_id || ', ' || transcript.id || ', ' || seq_run_id || ', 
                    ' || rec.tag_count || ', ' || rec.gaps || ', ' || rec.polya_count || ')';

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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_staging.split_joined_genes(chr_id integer, tag_extension integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer)
RETURNS VOID AS $$
DECLARE
    joined record;
    run_id integer;
    i integer;
BEGIN
    -- This should not need to be run often-- or even more than once. 
    -- During initial building phases, some genes get grouped together when they shouldn't.
    -- Here we split them out and re-add so that we can stitch with more stringent criteria.

    -- First, find transcripts with more than one gene, along with relevant source tables.
    
    FOR joined IN 
        EXECUTE 'SELECT t.id, t.transcription_start, t.transcription_end, t.strand,
                array_agg(run.source_table) as runs, array_agg(s.sequencing_run_id) as run_ids
            FROM glass_atlas_mm9_thiomac_prep.glass_transcript_' || chr_id || ' t
            JOIN genome_reference_mm9.sequence_transcription_region reg
                ON t.chromosome_id = reg.chromosome_id
                AND t.start_end && reg.start_end
                AND t.strand = reg.strand
            JOIN genome_reference_mm9.sequence_detail det
                ON reg.sequence_identifier_id = det.sequence_identifier_id
            JOIN glass_atlas_mm9_thiomac_prep.glass_transcript_source_' || chr_id || ' s
                ON t.id = s.glass_transcript_id
            WHERE width(t.start_end) >= .5*width(reg.start_end)
            GROUP BY t.id, t.transcription_start, t.transcription_end, t.strand
            HAVING count(distinct det.gene_name) > 1'
    LOOP
        -- Delete original transcript.
        EXECUTE 'DELETE FROM glass_atlas_mm9_thiomac_prep.glass_transcript_' || chr_id || ' WHERE id = ' || joined.id;
        
        -- Add from each source table for region only.
        FOR i IN 1..array_upper(joined.run_ids, 1)
        LOOP
            SELECT glass_atlas_%s_%s_prep.save_transcripts_from_sequencing_run(
            joined.run_ids[i], chr_id, joined.runs[i], 0, 
            tag_extension, allowed_edge, edge_scaling_factor, density_multiplier, 
            public.make_box(joined.transcription_start, 0, joined.transcription_end,0), joined.strand);
        END LOOP;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

-- This function operates on the post-prep table, but we keep it here to avoid having to recreate it every time.
-- This is used in manually generated queries to determine adjusted fold changes
CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.get_log_fold_change(ctl_tag_count bigint, sample_tag_count bigint, ctl_name text, sample_name text, deviation_score numeric)
RETURNS numeric AS $$
DECLARE
    norm_ctl_tag_count numeric;
    norm_sample_tag_count numeric;
    norm_deviation_score numeric;
BEGIN 
    -- Calculate the log-relative-fold change, 
    -- adjusting by deviation score in whatever direction _minimizes_ relative fold change.
    norm_ctl_tag_count := ctl_tag_count;
    norm_sample_tag_count := (SELECT sample_tag_count*total_norm_factor FROM glass_atlas_%s_%s.norm_sum WHERE name_1 = ctl_name AND name_2 = sample_name);
    norm_deviation_score := (SELECT deviation_score*total_tags_1 FROM glass_atlas_%s_%s.norm_sum WHERE name_1 = ctl_name AND name_2 = sample_name);
    IF (norm_sample_tag_count > norm_ctl_tag_count) THEN
        norm_sample_tag_count = (SELECT GREATEST(norm_ctl_tag_count, norm_sample_tag_count - norm_deviation_score));
    ELSE
        IF (norm_sample_tag_count < norm_ctl_tag_count) THEN
            norm_sample_tag_count = (SELECT LEAST(norm_ctl_tag_count, norm_sample_tag_count + norm_deviation_score));
        END IF;
    END IF;
    RETURN log(2, GREATEST(norm_sample_tag_count,1)/GREATEST(norm_ctl_tag_count,1)::numeric);
END;
$$ LANGUAGE 'plpgsql';

""" % tuple([genome, cell_type]*52)

if __name__ == '__main__':
    print sql(genome, cell_type)
