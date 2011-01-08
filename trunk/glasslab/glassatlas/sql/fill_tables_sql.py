'''
Created on Nov 12, 2010

@author: karmel

Convenience script for filling transcript tables from one schema to another.
'''

source_genome = 'mm11'
dest_genome = 'mm9'
cell_type = 'thiomac'
def sql(source_genome, dest_genome, cell_type):
    return """
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_1" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_1";

INSERT INTO "glass_atlas_%s_%s"."glass_transcript_2" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_2";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_3" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_3";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_4" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_4";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_5" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_5";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_6" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_6";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_7" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_7";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_8" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_8";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_9" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_9";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_10" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_10";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_11" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_11";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_12" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_12";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_13" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_13";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_14" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_14";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_15" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_15";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_16" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_16";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_17" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_17";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_18" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_18";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_19" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_19";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_20" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_20";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_21" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_21";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_22" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_22";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_23" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_23";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_24" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_24";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_25" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_25";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_26" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_26";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_27" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_27";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_28" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_28";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_29" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_29";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_30" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_30";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_31" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_31";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_32" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_32";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_33" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_33";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_34" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_34";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_35" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_35";

INSERT INTO "glass_atlas_%s_%s"."glass_transcript_nucleotides" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_nucleotides";


INSERT INTO "glass_atlas_%s_%s"."glass_transcript_source" SELECT * FROM "glass_atlas_%s_%s"."glass_transcript_source";

INSERT INTO "glass_atlas_%s_%s"."glass_transcribed_rna" SELECT * FROM "glass_atlas_%s_%s"."glass_transcribed_rna";
INSERT INTO "glass_atlas_%s_%s"."glass_transcribed_rna_source" SELECT * FROM "glass_atlas_%s_%s"."glass_transcribed_rna_source";

INSERT INTO "glass_atlas_%s_%s"."glass_transcript_sequence" 
    SELECT id, glass_transcript_id, sequence_transcription_region_id, 
        relationship::text::"glass_atlas_%s_%s"."glass_transcript_transcription_region_relationship" 
    FROM "glass_atlas_%s_%s"."glass_transcript_sequence";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_non_coding" 
    SELECT id, glass_transcript_id, non_coding_transcription_region_id, 
        relationship::text::"glass_atlas_%s_%s"."glass_transcript_transcription_region_relationship" 
    FROM "glass_atlas_%s_%s"."glass_transcript_non_coding";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_conserved" 
    SELECT id, glass_transcript_id, conserved_transcription_region_id, 
        relationship::text::"glass_atlas_%s_%s"."glass_transcript_transcription_region_relationship"
    FROM "glass_atlas_%s_%s"."glass_transcript_conserved";
INSERT INTO "glass_atlas_%s_%s"."glass_transcript_patterned" 
    SELECT id, glass_transcript_id, patterned_transcription_region_id, 
        relationship::text::"glass_atlas_%s_%s"."glass_transcript_transcription_region_relationship"
    FROM "glass_atlas_%s_%s"."glass_transcript_patterned";

INSERT INTO "glass_atlas_%s_%s"."sequencing_run" 
    SELECT "id","type"::text::"glass_atlas_%s_%s"."sequencing_run_type",
        "name","source_table","description","total_tags","percent_mapped","modified","created"
    FROM "glass_atlas_%s_%s"."sequencing_run";


SELECT setval('"glass_atlas_%s_%s"."glass_transcript_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcript_nucleotides_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript_nucleotides"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcript_source_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript_source"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcript_sequence_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript_sequence"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcript_non_coding_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript_non_coding"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcript_conserved_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript_conserved"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcript_patterned_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcript_patterned"), true);
SELECT setval('"glass_atlas_%s_%s"."sequencing_run_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."sequencing_run"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcribed_rna_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcribed_rna"), true);
SELECT setval('"glass_atlas_%s_%s"."glass_transcribed_rna_source_id_seq"', (SELECT max(id) FROM "glass_atlas_%s_%s"."glass_transcribed_rna_source"), true);

""" % tuple([dest_genome, cell_type, source_genome, cell_type]*39 
            + [dest_genome, cell_type, dest_genome, cell_type, source_genome, cell_type]*5 
            + [dest_genome, cell_type]*20)

if __name__ == '__main__':
    print sql(source_genome, dest_genome, cell_type)