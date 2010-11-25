'''
Created on Nov 24, 2010

@author: karmel
'''

sql = """CREATE OR REPLACE FUNCTION public.ucsc_link_mm9(chr_name character, transcription_start bigint, transcription_end bigint, strand_0 boolean)
RETURNS text AS $$
DECLARE
    file_name character(10);
BEGIN
    IF strand_0 = true THEN file_name := 'sense';
    ELSE file_name := 'antisense';
    END IF;
    
    RETURN '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?hgS_doLoadUrl=submit&amp;hgS_loadUrlName=http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2F' || file_name ||'_strands.txt&amp;db=mm9&amp;position=' || chr_name || '%3A+' || transcription_start || '-' || transcription_end || '" target="_blank">View</a>';
END;
$$ LANGUAGE 'plpgsql';
"""

print sql