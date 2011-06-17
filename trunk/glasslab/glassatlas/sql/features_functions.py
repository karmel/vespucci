'''
Created on Nov 12, 2010

@author: karmel

Convenience script for feature association functions.
'''
genome = 'erna'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
-- Not run from within the codebase, but kept here in case functions need to be recreated.

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.insert_associated_peak_features_from_run(run_id integer, chr_id integer)
RETURNS VOID AS $$
DECLARE
    run glass_atlas_mm9.sequencing_run;
BEGIN
    run := (SELECT (seq_run.*)::glass_atlas_mm9.sequencing_run 
            FROM glass_atlas_mm9.sequencing_run seq_run WHERE id = run_id);
    PERFORM glass_atlas_%s_%s.insert_associated_peak_features(run, chr_id);
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.insert_associated_peak_features(run glass_atlas_mm9.sequencing_run, chr_id integer)
RETURNS VOID AS $$
DECLARE
    rec record;
	padding integer := 2000;
	existing_feature glass_atlas_%s_%s.peak_feature;
	distance integer;
	peak_touches boolean;
BEGIN    
	-- Find relevant peaks
	FOR rec in 
	   EXECUTE
	   'SELECT transcript.*, 
	       glass_peak.id as glass_peak_id,
	       glass_peak."end" as glass_peak_end,
	       glass_peak.start as glass_peak_start,
	       glass_peak.length as glass_peak_length,
	       glass_peak.tag_count as glass_peak_tag_count,
	       glass_peak.score as glass_peak_score,
           (CASE WHEN transcript.start_end ~= glass_peak.start_end THEN
                glass_atlas_%s_%s.glass_transcript_feature_relationship(''is equal to'')
            WHEN transcript.start_end @> glass_peak.start_end THEN
                glass_atlas_%s_%s.glass_transcript_feature_relationship(''contains'')
            WHEN transcript.start_end <@ glass_peak.start_end THEN
                glass_atlas_%s_%s.glass_transcript_feature_relationship(''is contained by'')
            WHEN transcript.start_end && glass_peak.start_end THEN
                glass_atlas_%s_%s.glass_transcript_feature_relationship(''overlaps with'')
            
            -- Only reach upstream/downstream if not matched with one of the above
            WHEN (transcript.strand = 0 
                AND public.make_box(transcription_start - ' || padding || ', 0, transcription_start, 0)
                    && glass_peak.start_end) THEN
                glass_atlas_%s_%s.glass_transcript_feature_relationship(''is downstream of'')
            WHEN (transcript.strand = 1 
                AND public.make_box(transcription_end, 0, transcription_end + ' || padding || ', 0)
                    && glass_peak.start_end) THEN
                glass_atlas_%s_%s.glass_transcript_feature_relationship(''is downstream of'')
            ELSE glass_atlas_%s_%s.glass_transcript_feature_relationship(''is upstream of'')
            END) as relationship
        FROM glass_atlas_%s_%s.glass_transcript transcript
        JOIN "' || run.source_table || '" glass_peak
        ON box(point(transcription_start - ' || padding || ', 0), point(transcription_end + ' || padding || ', 0))
            && glass_peak.start_end
        WHERE transcript.chromosome_id = ' || chr_id || '
        AND glass_peak.chromosome_id = ' || chr_id 
    LOOP
        IF (rec.id IS NOT NULL) THEN
            -- Find or create feature record
            existing_feature := (SELECT (feat.*)::glass_atlas_%s_%s.peak_feature
                            FROM glass_atlas_%s_%s.peak_feature feat
                            WHERE feat.glass_transcript_id = rec.id
                            AND feat.glass_peak_id = rec.glass_peak_id
                            AND feat.sequencing_run_id = run.id);
        	
        	IF rec.relationship = glass_atlas_%s_%s.glass_transcript_feature_relationship('is downstream of')
                OR rec.relationship = glass_atlas_%s_%s.glass_transcript_feature_relationship('is upstream of')
                THEN peak_touches := false;
            ELSE peak_touches := true;
            END IF;
        
            -- Find the absolute val of the distance from the midpoint of the peak to the tss 
            
            distance := (SELECT (rec.glass_peak_start + rec.glass_peak_length/2.0)::integer
                                - (CASE WHEN rec.strand = 0 THEN rec.transcription_start ELSE rec.transcription_end END));
            
            IF existing_feature IS NULL THEN
                INSERT INTO glass_atlas_%s_%s.peak_feature
                    (glass_transcript_id, glass_peak_id, sequencing_run_id, peak_type_id, 
                    relationship, touches, length, tag_count, score, distance_to_tss) VALUES
                    (rec.id, rec.glass_peak_id, run.id, run.peak_type_id,
                    rec.relationship, peak_touches, rec.glass_peak_length, 
                    rec.glass_peak_tag_count, rec.glass_peak_score, distance) 
                    RETURNING * INTO existing_feature;
            ELSE
                UPDATE glass_atlas_%s_%s.peak_feature 
                    SET 
                        peak_type_id = run.peak_type_id,
                        relationship = rec.relationship,
                        touches = peak_touches,
                        length = rec.glass_peak_length,
                        tag_count = rec.glass_peak_tag_count,
                        score = rec.glass_peak_score,
                        distance_to_tss = distance 
                    WHERE id = existing_feature.id;
            END IF;
    	END IF;
    END LOOP;
    
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	
CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.update_peak_features(chr_id integer, run_requires_reload_only boolean)
RETURNS VOID AS $$
DECLARE
    run glass_atlas_mm9.sequencing_run;
BEGIN
    FOR run IN
        SELECT * FROM glass_atlas_mm9.sequencing_run
        WHERE (run_requires_reload_only = false OR requires_reload = true)
            AND peak_type_id IS NOT NULL
    LOOP
        PERFORM glass_atlas_%s_%s.insert_associated_peak_features(run, chr_id);
    END LOOP;
        
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	

""" % tuple([genome, cell_type]*20)

if __name__ == '__main__':
    print sql(genome, cell_type)
