#! /usr/bin/env python
#---------------------------------------------------------------
#
# Name: siov_extracter_sparsify.py
#
# Purpose: Extract and sparsify data from conditions database into sqlite databases.
#
# Created: 9-Dec-2019,  H. Greenlee
#
# Usage:
#
# $ iov_extracter.py [-d|--devel]
#
# Options:
#
# -d - Use development database.
#
# Notes:
#
# 1.  Source ~uboonepro/.sqlaccess/prod_access.sh to define environment variables
#     for database access.
#
#---------------------------------------------------------------

from __future__ import print_function
import sys, os, datetime
import psycopg2
import sqlite3

# Calibration database names.

calibs = ['channelstatus_data']
         
calibs_dev = ['channelstatus_data']

# Table suffixes.

suffixes = ['tags', 'iovs', 'tag_iovs', 'data']

# Parse command line.

devel = 0
dev = ''
args = sys.argv[1:]
while len(args) > 0:
    if args[0] == '-d' or args[0] == '--devel' :
        devel = 1
        dev = '_dev'
        del args[0]
    else:
        print('Unknown option %s' % args[0])
        del args[0]
        sys.exit(1)


# Open connection to conditions database (postgres).

try:
    host = os.environ['PUB_PSQL_READER_HOST']
    port = int(os.environ['PUB_PSQL_READER_PORT'])
    user = os.environ['PUB_PSQL_READER_USER']
    db = os.environ['PUB_PSQL_READER_DB']
    pw = os.environ['PUB_PSQL_READER_PASS']
except:
    print("Source ~/.sqlaccess/prod_access.sh first.")


if devel:
    host = 'ifdb04.fnal.gov'
    db = 'microboone_dev'
    calibs = calibs_dev

conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)
cur = conn.cursor()

# Loop over calibration databases.

for calib in calibs:

    print('Calibration database %s.' % calib)

    # Create sqlite3 database for thie calibration.

    sqlite_database = '%s.db' % calib
    if os.path.exists(sqlite_database):
        os.remove(sqlite_database)
    sqlite_conn = sqlite3.connect(sqlite_database)
    sqlite_cur = sqlite_conn.cursor()

    # Dictionary of columns.

    schema = {}    # schema[table] = list of columns.

    # Loop over tables.

    for suffix in suffixes:

        # Handle data table separately.

        table_name = '%s_%s' % (calib, suffix)
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
            elif data_type == 'bigint':
                sqlite_type = 'integer'
            elif data_type == 'text':
                sqlite_type = 'text'
            elif data_type == 'timestamp without time zone':
                sqlite_type = 'integer'
            elif data_type == 'boolean':
                sqlite_type = 'integer'
            elif data_type == 'real':
                sqlite_type = 'real'
            if sqlite_type == '':
                print('Unknown type %s' % data_type)
                sys.exit(1)

            #print column_name, data_type, sqlite_type

            qtbl += '%s %s' % (column_name, sqlite_type)

            # Add primary keys and constraints.

            if first and (suffix == 'tags' or suffix == 'iovs'):
                qtbl += ' PRIMARY KEY'
            elif null == 'NO':
                qtbl += ' NOT NULL'
            first = False

        # Add foreign keys.

        if suffix == 'tag_iovs':
            qtbl += ', FOREIGN KEY (iov_id) REFERENCES %s_iovs(iov_id)' % calib
            qtbl += ', FOREIGN KEY (tag) REFERENCES %s_tags(tag)' % calib
        elif suffix == 'data':
            qtbl += ', FOREIGN KEY (__iov_id) REFERENCES %s_iovs(iov_id)' % calib

        # Complete query.

        qtbl += ');'
        #print qtbl
        sqlite_cur.execute(qtbl)

        # Done creating table.
        # For data table, we are done for now.

        if suffix == 'data':
            continue

        # Query contents of table from postgres database.

        first = True
        q = 'SELECT '
        for column in schema[table_name]:
            if not first:
                q += ','
            q += column
            first = False

        q += ' FROM %s' % table_name

        # For data table, append iov_id constraint.

        if suffix == 'data':
            print('iov id = %d' % iov_id)
            q += ' WHERE __iov_id = %d' % iov_id
        q += ';'

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


    # Done looping over tables for thie calibration database.

    # Now populate sparsified data table.


    columns = schema['%s_data' % calib]
    processed_iovs = set()

    # Query tags in time order and loop over them.

    q = 'select tag from %s_tags order by created' % calib
    cur.execute(q)
    tag_rows = cur.fetchall()
    for tag_row in tag_rows:
        tag = tag_row[0]
        print('Data table tag %s' % tag)

        # Query iovs in time order and loop over them.

        q = 'select %s_iovs.iov_id, begin_time from %s_iovs,%s_tag_iovs' % (calib, calib, calib)
        q += ' where %s_iovs.iov_id=%s_tag_iovs.iov_id' % (calib, calib)
        q += ' and %s_tag_iovs.tag=\'%s\'' % (calib, tag)
        q += ' and %s_iovs.active=true' % calib
        q += ' order by begin_time'
        cur.execute(q)
        iov_rows = cur.fetchall()
        print('%d iovs for tag %s' % (len(iov_rows), tag))
        last_iov_id = -1
        for iov_row in iov_rows:
            iov_id = iov_row[0]
            begin_time = iov_row[1]

            # Have we already processed this iov?

            if iov_id in processed_iovs:
                print('Already processed iov %d' % iov_id)
            else:
                print('Processing iov %d' % iov_id)
                processed_iovs.add(iov_id)

                # Query data for this iov_id.

                this_iov_channels = set()
                q = ''
                for column in columns:
                    if q == '':
                        q = 'select '
                    else:
                        q += ','
                    q += column
                q += ' from %s_data' % calib
                q += ' where __iov_id=%d' % iov_id
                cur.execute(q)
                rows = cur.fetchall()
                for row in rows:
                    this_iov_channels.add(row[1:])

                # Query data for previous iov_id (if any)

                previous_iov_channels = set()
                if last_iov_id >= 0:
                    q = ''
                    for column in columns:
                        if q == '':
                            q = 'select '
                        else:
                            q += ','
                        q += column
                    q += ' from %s_data' % calib
                    q += ' where __iov_id=%d' % last_iov_id
                    cur.execute(q)
                    rows = cur.fetchall()
                    for row in rows:
                        previous_iov_channels.add(row[1:])

                # Find changed channels.

                diff_channels = this_iov_channels - previous_iov_channels
                print('%d changed channels.' % len(diff_channels))

                # Insert changed channels into data table.

                for diff_element in diff_channels:
                    q = 'INSERT INTO %s_data (__iov_id,channel' % calib
                    qval = 'VALUES(%d,%d' % (iov_id,diff_element[0])
                    n = 0
                    for column in columns[2:]:
                        n += 1
                        value = diff_element[n]
                        q += ',%s' % column
                        qval += ',%s' % value
                    qval += ')'
                    q += ') %s;' % qval
                    sqlite_cur.execute(q)

            # Done with iov.

            last_iov_id = iov_id
                


    # Close sqlite database.

    sqlite_conn.commit()
    sqlite_conn.close()

# Done looping over calibration databases.

sys.exit(0)

