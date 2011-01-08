'''
Created on Nov 24, 2010

@author: karmel
'''

def sql():
    return """
CREATE OR REPLACE FUNCTION public.admin_link(id integer)
RETURNS text AS $$
BEGIN
    RETURN '<a href="/admin/Transcription_ThioMac/glasstranscriptthiomac/' || id || '" target="_blank">' || id || '</a>';
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION public.admin_link_rna(id integer)
RETURNS text AS $$
BEGIN
    RETURN '<a href="/admin/Transcription_ThioMac/glasstranscribedrnathiomac/' || id || '" target="_blank">' || id || '</a>';
END;
$$ LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION public.ucsc_link_mm9(chr_name character, transcription_start bigint, transcription_end bigint, strand smallint)
RETURNS text AS $$
DECLARE
    file_name character(10);
BEGIN
    IF strand = 0 THEN file_name := 'sense';
    ELSE file_name := 'antisense';
    END IF;
    
    RETURN '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?hgS_doLoadUrl=submit&amp;hgS_loadUrlName=http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2Fglasstranscript_' || file_name ||'_strands.txt&amp;db=mm9&amp;position=' || chr_name || '%3A+' || transcription_start || '-' || transcription_end || '" target="_blank">View</a>';
END;
$$ LANGUAGE 'plpgsql';
"""

if __name__ == '__main__':
    print sql()