'''
Created on Nov 12, 2010

@author: karmel

Convenience script for feature association functions.
'''
genome = 'prep'
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
    glass_peak record;
    rec record;
	padding integer := 2000;
	existing_feature glass_atlas_%s_%s.peak_feature;
	instance glass_atlas_%s_%s.peak_feature_instance;
	distance integer;
BEGIN
    FOR glass_peak IN
        EXECUTE 'SELECT * FROM "' || run.source_table
        || '" WHERE chromosome_id = ' || chr_id
    LOOP
    	-- Find relevant peaks
    	FOR rec in 
    	   SELECT transcript.*, 
               (CASE WHEN start_end OPERATOR(public.=) glass_peak.start_end THEN
                    glass_atlas_%s_%s.glass_transcript_feature_relationship('is equal to')
                WHEN start_end OPERATOR(public.@>) glass_peak.start_end THEN
                    glass_atlas_%s_%s.glass_transcript_feature_relationship('contains')
                WHEN start_end OPERATOR(public.<@) glass_peak.start_end THEN
                    glass_atlas_%s_%s.glass_transcript_feature_relationship('is contained by')
                WHEN start_end OPERATOR(public.&&) glass_peak.start_end THEN
                    glass_atlas_%s_%s.glass_transcript_feature_relationship('overlaps with')
                
                -- Only reach upstream/downstream if not matched with one of the above
                WHEN (strand = 0 
                    AND public.cube(transcription_start - padding, transcription_start)
                        OPERATOR(public.&&) glass_peak.start_end) THEN
                    glass_atlas_%s_%s.glass_transcript_feature_relationship('is downstream of')
                WHEN (strand = 1 
                    AND public.cube(transcription_end, transcription_end + padding)
                        OPERATOR(public.&&) glass_peak.start_end) THEN
                    glass_atlas_%s_%s.glass_transcript_feature_relationship('is downstream of')
                ELSE glass_atlas_%s_%s.glass_transcript_feature_relationship('is upstream of')
                END) as relationship
            FROM glass_atlas_%s_%s.glass_transcript transcript
            WHERE chromosome_id = chr_id
            AND public.cube(transcription_start - padding, transcription_end + padding)
                OPERATOR(public.&&) glass_peak.start_end
        LOOP
            IF (rec.id IS NOT NULL) THEN
            	-- Find or create peak_feature record
            	existing_feature := (SELECT (feature.*)::glass_atlas_%s_%s.peak_feature FROM glass_atlas_%s_%s.peak_feature feature 
            	                        WHERE glass_transcript_id = rec.id
            	                        AND peak_type_id = run.peak_type_id
            	                        AND relationship = rec.relationship);
            	IF existing_feature IS NULL THEN
            	    INSERT INTO glass_atlas_%s_%s.peak_feature 
                        (glass_transcript_id, peak_type_id, relationship) VALUES
                        (rec.id, run.peak_type_id, rec.relationship) RETURNING * INTO existing_feature;
                END IF;
                
                -- Find or create peak_feature_instance record
                instance := (SELECT (inst.*)::glass_atlas_%s_%s.peak_feature_instance
                                FROM glass_atlas_%s_%s.peak_feature_instance inst
                                WHERE peak_feature_id = existing_feature.id
                                AND sequencing_run_id = run.id
                                AND glass_peak_id = glass_peak.id);
                
                -- Find the absolute val of the distance from the midpoint of the peak to the tss 
                distance := (SELECT abs((glass_peak."end" + glass_peak.start)/2::integer
                                        - (CASE WHEN rec.strand = 0 THEN rec.transcription_start ELSE rec.transcription_end END)));
                IF instance IS NULL THEN
                    INSERT INTO glass_atlas_%s_%s.peak_feature_instance
                        (peak_feature_id, sequencing_run_id, glass_peak_id, distance_to_tss) VALUES
                        (existing_feature.id, run.id, glass_peak.id, distance) RETURNING * INTO instance;
                ELSE
                    UPDATE glass_atlas_%s_%s.peak_feature_instance 
                        SET distance_to_tss = distance WHERE id = instance.id;
                END IF;
        	END IF;
        END LOOP;
    END LOOP;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	
CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.update_peak_features(chr_id integer, null_only boolean)
RETURNS VOID AS $$
DECLARE
    run glass_atlas_mm9.sequencing_run;
BEGIN
    IF null_only THEN
        DELETE FROM glass_atlas_%s_%s.peak_feature
            WHERE glass_transcript_id IN 
            (SELECT id FROM glass_atlas_%s_%s.glass_transcript
                WHERE chromosome_id = chr_id
                AND score IS NULL);
    ELSE
        DELETE FROM glass_atlas_%s_%s.peak_feature
            WHERE glass_transcript_id IN 
            (SELECT id FROM glass_atlas_%s_%s.glass_transcript
                WHERE chromosome_id = chr_id);
    END IF;
    DELETE FROM glass_atlas_%s_%s.peak_feature_instance
        WHERE peak_feature_id NOT IN 
        (SELECT id FROM glass_atlas_%s_%s.peak_feature);

    FOR run IN
        SELECT * FROM glass_atlas_mm9.sequencing_run
        WHERE peak_type_id IS NOT NULL
    LOOP
        PERFORM glass_atlas_%s_%s.insert_associated_peak_features(run, chr_id);
    END LOOP;
        
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	

""" % tuple([genome, cell_type]*28)

if __name__ == '__main__':
    print sql(genome, cell_type)
