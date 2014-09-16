'''
Created on Sep 27, 2010

@author: karmel
'''
from __future__ import division
import re
from django.db import models, connection
from vespucci.genomereference.datatypes import Chromosome
from vespucci.utils.datatypes.basic_model import Int8RangeField, DynamicTable
from vespucci.utils.database import execute_query
from vespucci.config import current_settings


class AtlasPeak(DynamicTable):
    '''
    Peaks derived from HOMER, MACS, or Sicer peak-finding software
    can be loaded in to be compared to transcripts.
    '''

    chromosome = models.ForeignKey(Chromosome)
    start = models.IntegerField(max_length=12)
    end = models.IntegerField(max_length=12)
    strand = models.IntegerField(max_length=2)

    start_end = Int8RangeField(max_length=255)

    length = models.IntegerField(max_length=12)
    summit = models.IntegerField(max_length=12)
    tag_count = models.DecimalField(max_digits=8, decimal_places=2,
                                    null=True, default=None)
    raw_tag_count = models.DecimalField(max_digits=8, decimal_places=2,
                                        null=True, default=None)

    score = models.DecimalField(max_digits=8, decimal_places=2,
                                null=True, default=None)
    p_value = models.DecimalField(max_digits=6, decimal_places=4,
                                  null=True, default=None)
    p_value_exp = models.IntegerField(max_length=12, null=True, default=None,
                            help_text='Exponent of 10 in p_value x 10^y')
    log_ten_p_value = models.DecimalField(max_digits=10, decimal_places=2,
                                          null=True, default=None)
    fold_enrichment = models.DecimalField(max_digits=10, decimal_places=2,
                                          null=True, default=None)
    fdr_threshold = models.DecimalField(max_digits=6, decimal_places=4,
                                        null=True, default=None)
    fdr_threshold_exp = models.IntegerField(max_length=12, null=True, default=None,
                            help_text='Exponent of 10 in fdr_threshold x 10^y')


    @classmethod
    def create_table(cls, name):
        '''
        Create table that will be used for these peaks,
        dynamically named.
        '''
        cls.set_table_name('peak_' + name)

        table_sql = """
        CREATE TABLE "{0}" (
            id int4,
            chromosome_id int4,
            "start" int8,
            "end" int8,
            "strand" int2,
            start_end int8range,
            "length" int4,
            summit int8,
            tag_count decimal(8,2) default NULL,
            raw_tag_count decimal(8,2) default NULL,
            score decimal(8,2) default NULL,
            p_value decimal(6,4) default NULL,
            p_value_exp int4 default NULL,
            log_ten_p_value decimal(10,2) default NULL,
            fold_enrichment decimal(10,2) default NULL,
            fdr_threshold decimal(6,4) default NULL,
            fdr_threshold_exp int4 default NULL
            );
        CREATE SEQUENCE "{0}_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "{0}_id_seq" OWNED BY "{0}".id;
        ALTER TABLE "{0}" ALTER COLUMN id 
            SET DEFAULT nextval('"{0}_id_seq"'::regclass);
        ALTER TABLE ONLY "{0}" ADD CONSTRAINT {1}_pkey PRIMARY KEY (id);
        """.format(cls._meta.db_table, cls.name)
        execute_query(table_sql)

        cls.table_created = True

    @classmethod
    def add_indices(cls):
        update_query = """
        CREATE INDEX {0}_chr_idx ON "{1}" USING btree (chromosome_id);
        CREATE INDEX {0}_start_end_idx ON "{1}" USING gist (start_end);
        """.format(cls.name, cls._meta.db_table)
        execute_query(update_query)

    @classmethod
    def init_from_macs_row(cls, row):
        '''
        From a standard tab-delimited MACS peak file, create model instance.
        '''
        connection.close()
        chrom = str(row[0]).strip()
        if not re.match(current_settings.CHR_MATCH, chrom): return None
        return cls(chromosome=Chromosome.objects.get(name=chrom),
                     start=int(row[1]),
                     end=int(row[2]),
                     start_end=(int(row[1]), int(row[2])),
                     length=int(row[3]),
                     summit=int(row[4]),
                     tag_count=str(row[5]),
                     log_ten_p_value=str(row[6]),
                     fold_enrichment=str(row[7])
                     )
    @classmethod
    def init_from_homer_row(cls, row):
        '''
        From a standard tab-delimited Homer peak file, create model instance.
        '''
        connection.close()
        chrom = str(row['chr']).strip()
        if not re.match(current_settings.CHR_MATCH, chrom): return None

        try: p_val = str(row['p-value vs Control']).lower().split('e')
        except KeyError:
            try: p_val = str(row['p-value vs Local']).lower().split('e')
            except KeyError: p_val = None
        try: fold_change = str(row['Fold Change vs Control'])
        except KeyError:
            try: fold_change = str(row['Fold Change vs Local'])
            except KeyError: fold_change = None
        return cls(chromosome=Chromosome.objects.get(name=chrom),
                     start=int(row['start']),
                     end=int(row['end']),
                     strand=int(row['strand'] == '-'),
                     start_end=(int(row['start']), int(row['end'])),
                     length=int(row['end']) - int(row['start']),
                     tag_count=str(row['Normalized Tag Count']),
                     score=str(row.get('findPeaks Score', 0)),
                     p_value=p_val and str(p_val[0]) or None,
                     p_value_exp=p_val and len(p_val) > 1 and p_val[1] or 0,
                     fold_enrichment=fold_change
                     )


    @classmethod
    def init_from_sicer_row(cls, row):
        '''
        From a standard tab-delimited SICER peak file, create model instance.
        '''
        connection.close()
        chrom = str(row[0]).strip()
        if not re.match(current_settings.CHR_MATCH, chrom): return None

        p_val = str(row[5]).split('e')  # '1.34e-12' --> 1.34, -12
        fdr = str(row[7]).split('e')
        return cls(chromosome=Chromosome.objects.get(name=chrom),
                     start=int(row[1]),
                     end=int(row[2]),
                     start_end=(int(row[1]), int(row[2])),
                     length=int(row[2]) - int(row[1]),
                     tag_count=str(row[3]),
                     p_value=p_val[0],
                     p_value_exp=len(p_val) > 1 and p_val[1] or 0,
                     fold_enrichment=str(row[6]),
                     fdr_threshold=fdr[0],
                     fdr_threshold_exp=len(fdr) > 1 and fdr[1] or 0
                     )
    @classmethod
    def init_from_bed_row(cls, row):
        '''
        From a standard tab-delimited BED peak file, create model instance.
        '''
        return cls(chromosome=Chromosome.objects.get(name=str(row[0]).strip()),
                     start=int(row[1]),
                     end=int(row[2]),
                     start_end=(int(row[1]), int(row[2])),
                     length=int(row[2]) - int(row[1]),
                     score=str(row[4]),
                     )
