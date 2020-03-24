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

# Tables and columns.
# All data types are integers.
# Columns ending in "_vers," other than first, are foreign keys.

tables = { 'hootversion' : ('version_set',
                            'history_version_born_on',
                            'begin_validity_timestamp',
                            'end_validity_timestamp',
                            'adcreceivers_vers',
                            'channels_vers',
                            'crates_vers',
                            'fem_mapping_vers'),
           'versioned_adcreceivers' : ('adcreceivers_vers',
                                       'crate_id',
                                       'daq_slot'),
           'versioned_channels' : ('channels_vers',
                                   'larsoft_channel'),
           'versioned_crates' : ('crates_vers',
                                 'crate_id'),
           'versioned_fem_mapping' : ('fem_mapping_vers',
                                      'fem_channel')}

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

# Loop over tables to create tables in sqlite database.

for table_name in tables:

    # Create table.

    print('Creating table %s' % table_name)

    fkeys = []
    first = True
    qtbl = 'CREATE TABLE IF NOT EXISTS %s (' % table_name

    # Add columns.

    for column in tables[table_name]:
        if not first:
            qtbl += ', '
            if column.endswith('_vers'):
                fkeys.append(column)
        qtbl += '%s INTEGER' % column
        first = False

    # Add foreign keys.

    for fkey in fkeys:
        reftable = 'versioned_%s' % fkey[:-5]
        qtbl += ', FOREIGN KEY (%s) REFERENCES %s(%s)' % (fkey, reftable, fkey)

    # Complete query.

    qtbl += ')'
    #print(qtbl)

    # Execute query to create table.

    sqlite_cur.execute(qtbl)

# Loop over tables to extract data from postgres and insert into sqlite.

now = datetime.datetime.now()
for table_name in tables:

    print('Extracting data from table %s' % table_name)

    q = 'SELECT '

    # Loop over columns.

    first = True
    for column in tables[table_name]:
        if not first:
            q += ','
        q += column
        first = False

    q += ' FROM %s' % table_name

    # Execute query.

    #print(q)
    cur.execute(q)
    rows = cur.fetchall()
    print('%d rows fetched.' % len(rows))

    # Loop over rows.

    for row in rows:

        # Insert this row into sqlite database.

        q = 'INSERT INTO %s (' % table_name
        qval = 'VALUES('
        values = []
        n = 0
        for column in tables[table_name]:
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
        #print(q)
        #print(values)
        sqlite_cur.execute(q, tuple(values))

# Close sqlite database.

sqlite_conn.commit()
sqlite_conn.close()

sys.exit(0)

