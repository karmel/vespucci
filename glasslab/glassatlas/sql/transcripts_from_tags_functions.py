'''
Created on Nov 12, 2010

@author: karmel

Prep table functions, extracted for ease of reading.
'''

def sql(genome, cell_type):
    return """

CREATE TYPE glass_atlas_{0}_{1}_prep.glass_transcript_row AS ("chromosome_id" integer, "strand" smallint, 
    transcription_start bigint, transcription_end bigint, refseq boolean, tag_count integer, gaps integer, ids integer[]);

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.update_transcript_source_records(trans glass_atlas_{0}_{1}_prep.glass_transcript, old_id integer)
RETURNS VOID AS $$
BEGIN 
    -- Update redundant records: those that already exist for the merge
    EXECUTE 'UPDATE glass_atlas_{0}_{1}_prep.glass_transcript_source_' || trans.chromosome_id || ' merged_assoc
        SET tag_count = (merged_assoc.tag_count + trans_assoc.tag_count),
            gaps = (merged_assoc.gaps + trans_assoc.gaps)
        FROM glass_atlas_{0}_{1}_prep.glass_transcript_source_' || trans.chromosome_id || ' trans_assoc
        WHERE merged_assoc.glass_transcript_id = ' || trans.id || '
            AND trans_assoc.glass_transcript_id = ' || old_id || '
            AND merged_assoc.sequencing_run_id = trans_assoc.sequencing_run_id';
    -- UPDATE redundant records: those that don't exist for the merge
    EXECUTE 'UPDATE glass_atlas_{0}_{1}_prep.glass_transcript_source_' || trans.chromosome_id || '
        SET glass_transcript_id = ' || trans.id || '
        WHERE glass_transcript_id = ' || old_id || '
        AND sequencing_run_id 
        NOT IN (SELECT sequencing_run_id 
                FROM glass_atlas_{0}_{1}_prep.glass_transcript_source_' || trans.chromosome_id || '
            WHERE glass_transcript_id = ' || trans.id || ')';
    -- Delete those that remain for the removed transcript.
    EXECUTE 'DELETE FROM glass_atlas_{0}_{1}_prep.glass_transcript_source_' || trans.chromosome_id || '
        WHERE glass_transcript_id = ' || old_id;
    RETURN;
END;
$$ LANGUAGE 'plpgsql';
            
CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.merge_transcripts(merged_trans glass_atlas_{0}_{1}_prep.glass_transcript, trans glass_atlas_{0}_{1}_prep.glass_transcript)
RETURNS glass_atlas_{0}_{1}_prep.glass_transcript AS $$
BEGIN 
    -- Update the merged transcript
    merged_trans.transcription_start := (SELECT LEAST(merged_trans.transcription_start, trans.transcription_start));
    merged_trans.transcription_end := (SELECT GREATEST(merged_trans.transcription_end, trans.transcription_end));
    merged_trans.strand := trans.strand;
    RETURN merged_trans;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.get_allowed_edge(trans glass_atlas_{0}_{1}_prep.glass_transcript, 
                                            allowed_edge integer, scaling_factor integer, allow_extended_gaps boolean, 
                                            extension_percent float)
RETURNS float AS $$
DECLARE
    overlapping_edge float := NULL;
    edge float;
BEGIN 
    edge := allowed_edge;
    IF allow_extended_gaps = true THEN
        -- Allow longer edge (up to extension_percent percent of seq) if this sequence is contained in a RefSeq region
        overlapping_edge := (SELECT LEAST(reg.transcription_end - trans.transcription_end + 1,
                                    (reg.transcription_end - reg.transcription_start + 1)*extension_percent) 
                        FROM genome_reference_{0}.sequence_transcription_region reg
                        WHERE reg.chromosome_id = trans.chromosome_id
                            AND reg.strand = trans.strand
                            AND reg.start_end @>
                                point(trans.transcription_end, 0)
                        ORDER BY LEAST(reg.transcription_end - trans.transcription_end + 1,
                                    (reg.transcription_end - reg.transcription_start + 1)*extension_percent) DESC
                        LIMIT 1);
        edge := (SELECT GREATEST(allowed_edge, overlapping_edge));
    END IF;
    
    IF overlapping_edge IS NULL THEN
        edge := (SELECT allowed_edge*LEAST(trans.density/scaling_factor::numeric, 1));
    END IF;
    
    RETURN edge;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.determine_transcripts_from_sequencing_run(chr_id integer, strand integer, source_t text, max_gap integer, tag_extension integer, start_end box)
RETURNS SETOF glass_atlas_{0}_{1}_prep.glass_transcript_row AS $$
BEGIN 

    RETURN QUERY SELECT * FROM glass_atlas_{0}_{1}_prep.determine_transcripts_from_table(chr_id, strand, source_t, max_gap, tag_extension,'', start_end);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.determine_transcripts_from_existing(chr_id integer, strand integer, max_gap integer)
RETURNS SETOF glass_atlas_{0}_{1}_prep.glass_transcript_row AS $$
BEGIN 
    RETURN QUERY SELECT * FROM glass_atlas_{0}_{1}_prep.determine_transcripts_from_table(chr_id, strand, 'glass_atlas_{0}_{1}_prep"."glass_transcript', max_gap, 0,'transcription_', NULL);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.determine_transcripts_from_table(
        chr_id integer, strand integer, source_t text, max_gap integer, 
        tag_extension integer, field_prefix text, start_end box)
RETURNS SETOF glass_atlas_{0}_{1}_prep.glass_transcript_row AS $$
 DECLARE
    max_chrom_pos bigint;
    rec record;
    start_end_clause text := '';
    row glass_atlas_{0}_{1}_prep.glass_transcript_row;
    last_start bigint := 0;
    last_end bigint := 0;
    current_refseq boolean;
    tag_count integer := 0;
    gaps integer := 0;
    ids integer[];
    should_merge boolean := false;
    finish_row boolean := false;
    repeat_region integer;
BEGIN 
    -- Tag extension can exceed the boundaries of the chromosome if we are not careful.
    -- Make sure to keep lengths in range.
    max_chrom_pos := (SELECT (length - 1) FROM genome_reference_{0}.chromosome WHERE id = chr_id);
    
    -- IF a start_end is passed, use that to limit transcripts
    IF start_end IS NOT NULL THEN
        start_end_clause := ' and start_end && public.make_box(' || (start_end[0])[0] || ',0,' || (start_end[1])[0] || ',0) ';
    END IF;
    
    -- Select each tag set, grouped by start.
    -- We group here to speed up processing on tables where many tags start at the same location.
    FOR rec IN 
        EXECUTE 'SELECT array_agg(id) as ids, ' || chr_id || ' as chromosome_id, ' || strand ||' as strand,
        "' || field_prefix || 'start" as transcription_start, max("' || field_prefix || 'end") as transcription_end, 
         count(id) as tag_count, bool_or(refseq) as refseq
         FROM "' || source_t || '_' || chr_id
        || '" WHERE strand = ' || strand 
        || start_end_clause
        || ' GROUP BY "' || field_prefix || 'start", "' || field_prefix || 'end"
        ORDER BY "' || field_prefix || 'start" ASC, "' || field_prefix || 'end" ASC;'
        LOOP
            -- The tags returned from the sequencing run are shorter than we know them to be biologically
            -- We can therefore extend the mapped tag region by a set number of bp if an extension is passed in
            IF (tag_extension IS NOT NULL) AND (tag_extension != 0) THEN
                IF strand = 0 THEN rec.transcription_end := rec.transcription_end + tag_extension;
                ELSE rec.transcription_start := rec.transcription_start - tag_extension;
                END IF;
            END IF;
            
            -- Ensure values are in range
            rec.transcription_start := (SELECT GREATEST(0,rec.transcription_start));
            rec.transcription_end := (SELECT LEAST(max_chrom_pos, rec.transcription_end));
            
            -- Initialize the start and end if necessary
            IF (last_start = 0) AND (last_end = 0) THEN 
                last_start := rec.transcription_start; 
                last_end := rec.transcription_end;
            END IF;
            IF (current_refseq IS NULL) THEN
                current_refseq := rec.refseq;
            END IF;

            -- Include this tag if it doesn't violate a refseq boundary,
            -- and it overlaps or has < max_gap bp gap
            -- Else, this is a new transcript; close off the current and restart.
            -- We have a special case for the refseq boundary in which, if the
            -- two records differ, but the latter record is entirely contained
            -- within the first, we allow it to be joined in. 
            -- We add a 1bp margin to avoid scenarios where last_end = 10, 
            -- rec.transcription_end = 11, and rec.transcription_start gets set to 
            -- last_end + 1, rendering a 0-bp transcript. Checking for last_end + 1
            -- means that any clipped transcript is at least 1bp long.
            IF ((current_refseq = rec.refseq) OR (last_end + 1 >= rec.transcription_end)) THEN
                IF ((last_end + max_gap) >= rec.transcription_start) THEN should_merge := true; 
                END IF;
            END IF;
            
            IF should_merge = true THEN
                tag_count := tag_count + rec.tag_count;
                IF (rec.transcription_start > last_end) THEN
                    gaps := gaps + 1;
                END IF;
                -- We don't force last_start to be the least here,
                -- in case we had to reset it to not overlap with the previous row.
                -- Instead, use last_start as set, which, in most cases,
                -- will be the least of the two in any case.
                -- last_start := (SELECT LEAST(last_start, rec.transcription_start));
                
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
            row.refseq := current_refseq;
            row.gaps := gaps;
            row.ids := ids;
            
            IF (row.transcription_end <= row.transcription_start) THEN
                RAISE EXCEPTION 'Transcript end is less than transcript start for row ids %!', row.ids;
            END IF;
            IF (row.tag_count <= 0) THEN
                RAISE EXCEPTION 'Tag count is less than zero for row ids %!', row.ids;
            END IF;
                
            IF finish_row THEN
                RETURN NEXT row;
                
                -- Restart vars for next loop
                
                -- If we have to finish the row because of a refseq discrepancy,
                -- we want to make sure the next row won't overlap with 
                -- the one we just finished. So, we reset the start of the 
                -- record to the end of the last one if neccessary.
                last_start := (SELECT GREATEST(last_end + 1, rec.transcription_start));
                last_end := rec.transcription_end;
                tag_count := rec.tag_count;
                current_refseq = rec.refseq;
                gaps := 0;
                ids := rec.ids::integer[];
                finish_row := false;
                
                -- Store row even if not done, in case this is the last loop    
                row.chromosome_id := chr_id;
                row.strand = strand;
                row.transcription_start := last_start;
                row.transcription_end := last_end;
                row.tag_count := tag_count;
                row.refseq := current_refseq;
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

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.save_transcripts_from_sequencing_run(
    seq_run_id integer, chr_id integer, source_t text, max_gap integer, 
    tag_extension integer, allowed_edge integer, edge_scaling_factor integer, density_multiplier integer, 
    start_end box, one_strand integer)
RETURNS VOID AS $$
 DECLARE
    rec glass_atlas_{0}_{1}_prep.glass_transcript_row;
    transcript glass_atlas_{0}_{1}_prep.glass_transcript;
    density float;
    scaling_factor text;
    strand_start integer := 0;
    strand_end integer := 1;
 BEGIN
    IF edge_scaling_factor = 0 THEN scaling_factor := 'NULL';
    ELSE scaling_factor := edge_scaling_factor::text;
    END IF;
    
    -- Allow for strand selection
    IF one_strand IS NOT NULL THEN
        strand_start := one_strand;
        strand_end := one_strand;
    END IF; 
    
     FOR strand IN strand_start..strand_end 
     LOOP
        FOR rec IN 
            SELECT * FROM glass_atlas_{0}_{1}_prep.determine_transcripts_from_sequencing_run(chr_id, strand, source_t, max_gap, tag_extension, start_end)
        LOOP
            IF rec IS NOT NULL THEN
                -- Save the transcript.
                
                -- This transcript has been added for a single run, so we can set density
                -- as simple tag_count/length.
                density := (density_multiplier*(rec.tag_count)::numeric)/
                                (rec.transcription_end - rec.transcription_start + 1)::numeric;
                
                EXECUTE 'INSERT INTO glass_atlas_{0}_{1}_prep.glass_transcript_' || rec.chromosome_id
                    || ' ("chromosome_id", "strand", 
                    "transcription_start", "transcription_end", 
                    "start_end", "start_density", "refseq")
                    VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
                    || rec.transcription_start || ' , ' || rec.transcription_end || ' , 
                    public.make_box(' || rec.transcription_start || ', 0, ' || rec.transcription_end || ', 0),
                    point(' || rec.transcription_start || ',' || density || '),
                    ' || rec.refseq || '
                        ) RETURNING *' INTO transcript;
                
                -- Save the record of the sequencing run source
                EXECUTE 'INSERT INTO glass_atlas_{0}_{1}_prep.glass_transcript_source_' || rec.chromosome_id || '
                    (chromosome_id, "glass_transcript_id", "sequencing_run_id", "tag_count", "gaps") 
                    VALUES (' || transcript.chromosome_id || ', ' || transcript.id || ', ' || seq_run_id || ', 
                    ' || rec.tag_count || ', ' || rec.gaps || ')';

            END IF;
        END LOOP;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.save_transcripts_from_existing(chr_id integer, max_gap integer)
RETURNS VOID AS $$
 DECLARE
    rec glass_atlas_{0}_{1}_prep.glass_transcript_row;
    transcript glass_atlas_{0}_{1}_prep.glass_transcript;
    old_id integer;
 BEGIN
     FOR strand IN 0..1 
     LOOP
        FOR rec IN 
            SELECT * FROM glass_atlas_{0}_{1}_prep.determine_transcripts_from_existing(chr_id, strand, max_gap)
        LOOP
            IF rec IS NOT NULL AND rec.tag_count > 1 THEN            
                -- Save the transcript. 
                EXECUTE 'INSERT INTO glass_atlas_{0}_{1}_prep.glass_transcript_' || rec.chromosome_id
                    || ' ("chromosome_id", "strand", '
                    || ' "transcription_start", "transcription_end",' 
                    || ' "start_end", "refseq")'
                    || ' VALUES (' || rec.chromosome_id || ' , ' || rec.strand || ' , '
                    || rec.transcription_start || ' , ' || rec.transcription_end || ' , '
                    || ' public.make_box(' || rec.transcription_start || ', 0' 
                        || ',' ||  rec.transcription_end || ', 0), '
                    || rec.refseq || ' 
                    ) RETURNING *' INTO transcript;
                
                -- Remove existing records
                FOR old_id IN 
                    SELECT * FROM unnest(rec.ids)
                LOOP
                    PERFORM glass_atlas_{0}_{1}_prep.update_transcript_source_records(transcript, old_id);
                END LOOP;
                EXECUTE 'DELETE FROM glass_atlas_{0}_{1}_prep.glass_transcript_' || rec.chromosome_id
                    || ' WHERE id IN (' || array_to_string(rec.ids,',') || ')';
            END IF; 
        END LOOP;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.set_density(chr_id integer, 
                                        allowed_edge integer, edge_scaling_factor integer, 
                                        density_multiplier integer, allow_extended_gaps boolean,
                                        extension_percent float, null_only boolean)
RETURNS VOID AS $$
DECLARE
    table_name text;
    null_only_text text := ' AND 1=1 '; 
BEGIN
    -- Use temp tables to speed up processing.
    table_name := 'set_density_' || chr_id || '_' || (1000*RANDOM())::int;
    
    IF (null_only = true) THEN null_only_text = ' AND density IS NULL ';
    END IF;
    
    EXECUTE 'CREATE TEMP TABLE ' || table_name || '
        as SELECT t.id, GREATEST(0,(' || density_multiplier || '*sum(source.tag_count)::numeric)
                                        /(count(source.sequencing_run_id)*
                                        (t.transcription_end - t.transcription_start + 1)::numeric)) as density
        FROM glass_atlas_{0}_{1}_prep.glass_transcript_' || chr_id || ' t,
            glass_atlas_{0}_{1}_prep.glass_transcript_source_' || chr_id || ' source
        WHERE t.id = source.glass_transcript_id
        ' || null_only_text || '
        GROUP BY t.id, t.transcription_start, t.transcription_end';
        
    EXECUTE 'UPDATE glass_atlas_{0}_{1}_prep.glass_transcript_' || chr_id || ' t
        SET density = temp.density
            FROM ' || table_name || ' temp
        WHERE t.id = temp.id';

    
    -- Ditto for overlapping edge.
    EXECUTE 'CREATE TEMP TABLE ' || table_name || '_2
        as SELECT t.id,
                glass_atlas_{0}_{1}_prep.get_allowed_edge(t.*,
                    ' || allowed_edge || ',' || edge_scaling_factor || ', ' 
                    || allow_extended_gaps || ', ' || extension_percent || ') as edge
        FROM glass_atlas_{0}_{1}_prep.glass_transcript_' || chr_id || ' t';

    EXECUTE 'UPDATE glass_atlas_{0}_{1}_prep.glass_transcript_' || chr_id || ' t
        SET edge = temp.edge
            FROM ' || table_name || '_2 temp
        WHERE t.id = temp.id';
    
    EXECUTE 'UPDATE glass_atlas_{0}_{1}_prep.glass_transcript_' || chr_id || ' t 
             SET density_circle = circle(point(t.transcription_end, t.density), t.edge),
                 start_density = point(t.transcription_start,t.density)';
END;
$$ LANGUAGE 'plpgsql';



""".format(genome, cell_type)

