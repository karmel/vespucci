'''
Created on Nov 24, 2010

@author: karmel
'''

def sql():
    return """

CREATE OR REPLACE FUNCTION public.make_box(x1 numeric, y1 numeric, x2 numeric, y2 numeric)
RETURNS box AS $$
DECLARE
    s text;
BEGIN
    s := '((' || x1 || ',' || y1 || '),(' || x2 || ',' || y2 || '))';
    RETURN s::box;
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION public.make_box(x1 numeric, x2 numeric)
RETURNS box AS $$
DECLARE
    s text;
BEGIN
    s := '((' || x1 || ', 0),(' || x2 || ',0))';
    RETURN s::box;
END;
$$ LANGUAGE 'plpgsql';
"""

if __name__ == '__main__':
    print sql()
