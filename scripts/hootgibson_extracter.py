#! /usr/bin/env python
#---------------------------------------------------------------
#
# Name: hootgibson_extracter.py
#
# Purpose: Extract data from hoot gibson database into sqlite database.
#          Only extract the subset of data used by swizzler.
#
# Created: 23-Mar-2020,  H. Greenlee
#
# Usage:
#
# $ hootgibson_extracter.py
#
#---------------------------------------------------------------

from __future__ import print_function
import sys, os, datetime
import psycopg2
import sqlite3

# Tables.

tables = [ 'hootversion',
           'versioned_channels',
           'versioned_asics',
           'versioned_motherboards',
           'versioned_servicecables',
           'versioned_servicecards',
           'versioned_coldcables',
           'versioned_intermediateamplifiers',
           'versioned_warmcables',
           'versioned_adcreceivers',
           'versioned_fecards',
           'versioned_crates',
           'versioned_motherboard_mapping',
           'versioned_fem_mapping',
           'versioned_fem_map_ranges',
           'versioned_fem_crate_ranges',
           'versioned_fem_slot_ranges']

#print(tables)

# Open connection to conditions database (postgres).

try:
    host = 'ifdbprod2.fnal.gov'
    port = 5444
    user = 'uboonedaq_web'
    db = 'hootgibson_prod'
    pw = os.environ['HOOT_PASS']
except:
    print("Define environment variable HOOT_PASS")
    sys.exit(1)

conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)
cur = conn.cursor()

# Create sqlite3 database.

sqlite_database = 'hootgibson.db'
if os.path.exists(sqlite_database):
    os.remove(sqlite_database)
sqlite_conn = sqlite3.connect(sqlite_database)
sqlite_cur = sqlite_conn.cursor()

schema = {}    # schema[table] = list of columns.

# Loop over tables to create tables in sqlite database.

for table_name in tables:

    schema[table_name] = []
    print('Processing table %s.' % table_name)

    # Construct sqlite query to create corresponding table.

    qtbl = 'CREATE TABLE IF NOT EXISTS %s (' % table_name

    # Get schema of this table.

    q = 'select column_name, data_type, is_nullable from information_schema.columns where table_name=%s'
    cur.execute(q, (table_name,))
    rows = cur.fetchall()
    first = True
    for row in rows:
        column_name = row[0]
        data_type = row[1]
        null = row[2]

        schema[table_name].append(column_name)

        if not first:
            qtbl += ', '

        # Convert postgres data type to sqlite data type.

        sqlite_type = ''
        if data_type == 'integer':
            sqlite_type = 'integer'
        elif data_type == 'smallint':
            sqlite_type = 'integer'
        elif data_type == 'text':
            sqlite_type = 'text'
        elif data_type == 'character varying':
            sqlite_type = 'text'
        elif data_type == 'character':
            sqlite_type = 'text'
        elif data_type == 'timestamp without time zone':
            sqlite_type = 'integer'
        if sqlite_type == '':
            print('Unknown type %s' % data_type)
            sys.exit(1)

        #print(column_name, data_type, sqlite_type)

        qtbl += '%s %s' % (column_name, sqlite_type)
        first = False

    # Add foreign keys.

    if table_name == 'hootversion':
        for column in schema[table_name]:
            if column.endswith('_vers'):
                reftable = 'versioned_%s' % column[:-5]
                qtbl += ', FOREIGN KEY (%s) REFERENCES %s(%s)' % (column, reftable, column)

    # Complete query.

    qtbl += ');'
    #print(qtbl)
    sqlite_cur.execute(qtbl)

    # Done creating table.

    # Query contents of table from postgres database.

    first = True
    q = 'SELECT '
    for column in schema[table_name]:
        if not first:
            q += ','
        q += column
        first = False

    q += ' FROM %s' % table_name

    #print q
    cur.execute(q)
    rows = cur.fetchall()
    print('%d rows fetched.' % len(rows))
    now = datetime.datetime.now()
    for row in rows:

        # Insert row into sqlite database.

        q = 'INSERT INTO %s (' % table_name
        qval = 'VALUES('
        values = []
        n = 0
        for column in schema[table_name]:
            element = row[n]
            if n > 0:
                q += ','
                qval += ','
            q += column
            qval += '?'
            if type(element) == type(now):
                values.append(int(element.strftime('%s')))
            else:
                values.append(element)
            n += 1
        qval += ')'
        q += ') %s;' % qval
        #print q
        #print values
        sqlite_cur.execute(q, tuple(values))

# Close sqlite database.

sqlite_conn.commit()
sqlite_conn.close()

sys.exit(0)

