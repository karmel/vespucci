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

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s.insert_associated_peak_features(chr_id integer, run glass_atlas_%s.sequencing_run)
RETURNS VOID AS $$
DECLARE
	padded_cube text;
	cube text;
	start_site text;
	end_site text;
	tss integer;
	padding integer := 5000;
	relationship glass_atlas_%s_%s.glass_transcript_feature_relationship;
	existing_feature glass_atlas_%s_%s.peak_feature;
	instance glass_atlas_%s_%s.peak_feature_instance;
	peak_rec record;
	distnace integer;
BEGIN
    FOR glass_peak IN
        EXECUTE 'SELECT * FROM "' || run.source_table || '"
        WHERE chromosome_id = ' || chr_id
    LOOP
	-- Set up cubes of interest
	padded_cube := 'public.cube(' || transcript.transcription_start - padding || ',' || transcript.transcription_end + padding || ')';
	cube := 'public.cube(' || transcript.transcription_start || ',' || transcript.transcription_end || ')';
	IF transcript.strand = 0 THEN
	    start_site := 'public.cube(' || transcript.transcription_start - padding || ',' || transcript.transcription_start || ')';
	    end_site := 'public.cube(' || transcript.transcription_end || ',' || transcript.transcription_end + padding || ')';
	    tss := transcript.transcription_start;
	ELSE
	    end_site := 'public.cube(' || transcript.transcription_start - padding || ',' || transcript.transcription_start || ')';
	    start_site := 'public.cube(' || transcript.transcription_end || ',' || transcript.transcription_end + padding || ')';
	    tss := transcript.transcription_end;
	END IF;
	
	-- Find relevant peaks
	FOR peak_rec in 
	    EXECUTE 'SELECT transcript.id as transcript_id, ' 
           || ' (CASE WHEN start_end OPERATOR(public.=) ' || ' cube ' || ' THEN'
                || ' glass_atlas_%s_%s.glass_transcript_feature_relationship(''is equal to'')'
            || ' WHEN start_end OPERATOR(public.<@) ' || ' cube ' || ' THEN'
                || ' glass_atlas_%s_%s.glass_transcript_feature_relationship(''contains'')'
            || ' WHEN start_end OPERATOR(public.@>) ' || ' cube ' || ' THEN'
                || ' glass_atlas_%s_%s.glass_transcript_feature_relationship(''is contained by'')'
            || ' WHEN start_end OPERATOR(public.&&) ' || ' cube ' || ' THEN'
                || ' glass_atlas_%s_%s.glass_transcript_feature_relationship(''overlaps with'')'
            
            || ' -- Only reach upstream/downstream if not matched with one of the above'
            || ' WHEN start_end OPERATOR(public.&&) ' || ' start_site ' || ' THEN'
                || ' glass_atlas_%s_%s.glass_transcript_feature_relationship(''is downstream of'')'
            || ' WHEN start_end OPERATOR(public.&&) ' || ' end_site ' || ' THEN'
                || ' glass_atlas_%s_%s.glass_transcript_feature_relationship(''is upstream of'')'
            || ' ELSE NULL'
            || ' END) as relationship,'
            || ' start, "end"'
        || ' FROM "' || run.source_table || '" WHERE chromosome = ' || chr_id
        || ' AND start_end OPERATOR(public.&&) ' || padded_cube
    LOOP
        IF peak_rec IS NOT NULL
        	-- Find or create peak_feature record
        	existing_feature := (SELECT * FROM glass_atlas_%s_%s.peak_feature 
        	                        WHERE glass_transcript_id = transcript.id
        	                        AND peak_type_id = run.peak_type_id
        	                        AND relationship = peak_rec.relationship);
        	IF existing_feature IS NULL THEN
        	    INSERT INTO glass_atlas_%s_%s.peak_feature 
                    (glass_transcript_id, peak_type_id, relationship) VALUES
                    (transcript.id, run.peak_type_id, peak_rec.relationship) RETURNING * INTO existing_feature;
            END IF;
            
            -- Find or create peak_feature_instance record
            instance := (SELECT * FROM glass_atlas_%s_%s.peak_feature_instance 
                            WHERE peak_feature_id = existing_feature.id
                            AND sequencing_run_id = run.id
                            AND glass_peak_id = peak_rec.glass_peak_id);
            distance = SELECT abs((peak_rec."end" - peak_rec.start)/2::integer - tss);
            IF instance IS NULL THEN
                INSERT INTO glass_atlas_%s_%s.peak_feature_instance
                    (peak_feature_id, sequencing_run_id, glass_peak_id, distance_to_tss) VALUES
                    (existing_feature.id, run.id, peak_rec.glass_peak_id, distance) RETURNING * INTO instance;
            ELSE
                (PERFORM UPDATE glass_atlas_%s_%s.peak_feature_instance 
                    SET distance_to_tss = distance WHERE id = instance.id);
            END IF;
    	END IF;
    END LOOP;
	RETURN;
END;
$$ LANGUAGE 'plpgsql';
	

""" % tuple([genome, cell_type]*96)

if __name__ == '__main__':
    print sql(genome, cell_type)
