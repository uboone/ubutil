#! /usr/bin/env python
######################################################################
#
# Name: merge.py
#
# Purpose: Production merge engine.
#
# Created: 7-Sep-2019  Herbert Greenlee
#
# Usage:
#
# merge.py <options>
#
# Options:
#
# -h|--help           - Print help message.
# --xml <-|file|url>  - A project.py-style xml file.
# --project <project> - Project name.
# --stage <stage>     - Project stage.
# --defname <defname> - Process files belonging to this definition (optional).
# --database <path>   - Path of sqlite database file (default "merge.db").
# --max_size <bytes>  - Maximum merged file size in bytes (default 2.5e9).
# --min_size <bytes>  - Minimum merged file size in bytes (default 1e9).
# --max_age <seconds> - Maximum unmerged file age in seconds (default 72 hours).
#                       Optionally use suffix 'h' for hours, 'd' for days.
# --min_status <status> - Minimum status (default 0).
# --max_status <status> - Maximum status (default 6).
#
######################################################################
#
# Usage Notes.
#
# 1.  About the xml file:
#
#     The xml file used by this script should be a standard project.py
#     batch job xml file.  This file is used when and if this script
#     submits merging batch jobs.
#
#     The xml file option is not needed if there will be no need to submit
#     batch jobs.
#
#     The --project and --stage options are needed only if the xml file
#     contains multiple projects and/or stages.
#     
#     Rather than using a predefined fcl file for batch submissions, this
#     script generates its own customized fcl file and stores it in the 
#     path specified by xml element <fcl>.  Any preexisting fcl file
#     located at this path will be overwritten.
#
#     Some elements of the xml project and stage are overridden internally
#     in this script.  If specified, these elements are ignored, or they
#     may be able to be omitted in the xml file.  Here are the overridden elements:
#
#     <project name=?> - Set to match unmerged file metadata (ub_project.name).
#     <stage name=?> - Set to match unmerged file metadata (ub_project.stage).
#     <version>   - Set to match unmerged file metadata (ub_project.version).
#     <filetype>  - Set to match unmerged file metadata.
#     <runtype>   - Set to match unmerged file metadata.
#     <inputdef>  - Set to each job's specific input dataset.
#     <datatier>  - Set to match unmerged file metadata.
#     <prestart>  - Always true.
#     <numevents> - Set to a large number.
#
#     The value of <numjobs> in the original xml file specifies the maximum number
#     of merging batch jobs that will be submitted by one invocation of this
#     script.
#
#     The value specified in xml element <merge> is the maximum number sam
#     datasets/projects that will be processed by one batch job.  Each dataset/project
#     produces one merged artroot output file.
#
#     This script module project.py to parse the xml file, but interaction with
#     the batch system (via jobsub_submit) is handled internally.
#
#
# Description:
#
# This script interacts with the sam database, its own sqlite database,
# and the batch system to merge data files up to some maximum size optimized
# for storing on tape.
#
# Files to be merged must be declared to sam and have locations known to sam
# (can be disk locations, including pnfs scratch and pnfs persistent).
#
# Files are candidates for being merged if all of the following are true.
#
# 1.  Sam parameter merge.merge is true (1).
#
# 2.  Sam parameter merge.merged is false (0).
#
# 3.  File has a location.
#
# 4.  Files belong to the same merge group (see below).
#
# This script uses a database that has a schema consisting of the
# the following three tables.
#
# I.  Table unmerged_files
#
#     A. File id (integer, primary key).
#
#     B. File name (text).
#
#     C. Merge file id (integer, foreign key).  Many-to-one relation.
#
#     D. File size in bytes (integer).
#
#     E. Creation data (text).
#
#     F. Merge group id (integer, foreign key).  Many-to-one relation.
#
# II.  Table merged_files.
#
#    A. File id (integer, primary key).
#
#    B. File name (text).
#
#    C. Batch job id (text).
#
#    D. Sam project (text).
#
#    E. Status (integer).  Statuses as follows:
#
#       0 - Ready to merge.
#       1 - Merging locallly (in this script).
#       2 - Batch job submitted.
#       3 - Declared.
#       4 - Located.
#       5 - Finished.
#       6 - Error.
#
# III. Table merge_group.
#
#    A. Merge group id (integer, primary key).
#    B. File type (text).
#    C. File format (text).
#    D. Data tier (text).
#    E. Data stream (text).
#    F. Project name (text).
#    G. Project stage (text).
#    H. Project version (text).
#    I. Run number (integer).
#     
#
#
######################################################################

from __future__ import print_function
import sys, os, datetime, uuid, traceback, tempfile, subprocess
import threading
try:
    import queue as Queue
except ImportError:
    import Queue
import project, project_utilities, larbatch_posix
import sqlite3


def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0

    for line in file.readlines():
        if line[2:10] == 'merge.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:].rstrip())
            else:
                print()

class MergeEngine:

    # Constructor.

    def __init__(self, xmlfile, projectname, stagename, defname,
                 database, max_size, min_size, max_age,
                 min_status, max_status):

        # Open database connection.

        self.conn = self.open_database(database)

        # Create samweb object.

        self.samweb = project_utilities.samweb()

        # Extract project and stage objects from xml file (if specified).

        self.probj = None
        self.stobj = None
        self.fclpath = None
        self.numjobs = 0

        if xmlfile != '':
            xmlpath = project.normxmlpath(xmlfile)
            if not os.path.exists(xmlpath):
                print('XML file not found: %s' % xmlfile)

            # Use project.py to parse xml file and extract project and stage objects.

            self.probj = project.get_project(xmlpath, projectname, stagename)
            self.stobj = self.probj.get_stage(stagename)

            # Extract the fcl path from stage object.
            # If not already absolute path, convert to absolute path.

            if type(self.stobj.fclname) == type([]) and len(self.stobj.fclname) > 0:
                self.fclpath = os.path.abspath(self.stobj.fclname[0])
            elif type(self.stobj.fclname) == type(b'') or type(self.stobj.fclname) == type(u''):
                self.fclpath = os.path.abspath(self.stobj.fclname)

            # Store the absolute path back in stage object.

            self.stobj.fclname = [self.fclpath]

            # Don't let project.py think this is a generator job.

            self.stobj.maxfluxfilemb = 0

            # Save the maximum number of batch jobs to submit.

            self.numjobs = self.stobj.num_jobs

            # Save the maximum number of datasets/projects per batch job.

            self.numprj = int(self.stobj.merge)

        # Other tunable parameters.

        self.defname = defname     # File selectionn dataset definition.
        self.max_size = max_size   # Maximum merge file size in bytes.
        self.min_size = min_size   # Minimum merge file size in bytes.
        self.max_age = max_age     # Maximum unmerged file age in seconds.
        self.min_status = min_status # Minimum status.
        self.max_status = max_status # Maximum status.

        # Batch job merge queue.
        # This is a list of merged file ids to be processed in one batch job.

        self.merge_queue = []

        # Done.

        return


    # Destructor.

    def __del__(self):

        self.conn.close()


    # Open database connection.

    def open_database(self, database):

        conn = sqlite3.connect(database, 60.)

        # Create tables.

        c = conn.cursor()

        q = '''
CREATE TABLE IF NOT EXISTS merge_groups (
  id integer PRIMARY KEY,
  file_type text NOT NULL,
  file_format text NOT NULL,
  data_tier text NOT NULL,
  data_stream text NOT NULL,
  project text NOT NULL,
  stage text NOT NULL,
  version text NOT NULL,
  run integer
);'''
        c.execute(q)

        q = '''
CREATE TABLE IF NOT EXISTS merged_files (
  id integer PRIMARY KEY,
  name text,
  group_id,
  jobid text,
  submit_time text,
  sam_project text,
  status integer,
  FOREIGN KEY (group_id) REFERENCES merge_groups (id)
);'''
        c.execute(q)

        q = '''
CREATE TABLE IF NOT EXISTS unmerged_files (
  id integer PRIMARY KEY,
  name text NOT NULL,
  merge_id integer,
  group_id integer,
  size integer,
  create_date text,
  FOREIGN KEY (merge_id) REFERENCES merged_files (id),
  FOREIGN KEY (group_id) REFERENCES merge_groups (id)
);'''
        c.execute(q)

        # Done

        return conn


    # This function queries mergeable files from sam and updates the unmerged_tables table.

    def update_unmerged_files(self):

        print('Querying unmerged files from sam.')
        extra_clause = ''
        if self.defname != '':
            extra_clause = 'and defname: %s' % self.defname
        dim = 'merge.merge 1 and merge.merged 0 %s with availability physical' % extra_clause
        files = self.samweb.listFiles(dim)
        print('%d unmerged files.' % len(files))
        print('Updating unmerged_files table in database.')
        for f in files:
            self.add_unmerged_file(f)

        # Done.

        self.conn.commit()
        return


    # Maybe add one unmerged file to unmerged_files table.

    def add_unmerged_file(self, f):

        # Query database to see if this file already exists.

        c = self.conn.cursor()
        q = 'SELECT id FROM unmerged_files WHERE name=?'
        c.execute(q, (f,))
        rows = c.fetchall()

        if len(rows) == 0:

            # File does not exist.
            # First check location, whether this file is on tape yet or not.

            locs = self.samweb.locateFile(f)
            on_tape = 0
            for loc in locs:
                if loc['location_type'] == 'tape':
                    on_tape = 1
            if on_tape:
                print('File %s is already on tape.' % f)

                # Since file is on tape, remove any disk locations.
                # This shouldn't really ever happen.
            
                for loc in locs:
                    if loc['location_type'] == 'disk':
                        print('Removing disk location.')
                        self.samweb.removeFileLocation(f, loc['full_path'])

                # Modify metadata to set merge.merged flag to be true, so that this
                # file will become invisible to merging.

                mdmod = {'merge.merged': 1}
                print('Updating metadata to set merged flag.')
                self.samweb.modifyFileMetadata(f, mdmod)

            else:

                print('Adding unmerged file %s' % f)
                md = self.samweb.getMetadata(f)
                group_id = self.merge_group(md)
                size = md['file_size']
                merge_id = 0
                create_date = md['create_date']
                q = '''INSERT INTO unmerged_files (name, merge_id, group_id, size, create_date)
                       VALUES(?,?,?,?,?);'''
                c.execute(q, (f, merge_id, group_id, size, create_date))

        # Done.

        return


    # Function to return the merge group id corresponding to a sam metadata dictionary.
    # If necessary, add a new merge group to merge_groups table.

    def merge_group(self, md):

        group_id = -1

        # Create group 8-tuple.

        file_type = md['file_type']
        file_format = md['file_format']
        data_tier = md['data_tier']
        data_stream = md['data_stream']
        ubproject = md['ub_project.name']
        ubstage = md['ub_project.stage']
        ubversion = md['ub_project.version']
        runs = md['runs']
        run = 0
        if len(runs) > 0:
            run = runs[0][0]
        gtuple = (file_type, file_format, data_tier, data_stream,
                  ubproject, ubstage, ubversion, run)

        # Query merge group id

        c = self.conn.cursor()
        q = '''
SELECT id FROM merge_groups WHERE
  file_type=?
  and file_format=?
  and data_tier=?
  and data_stream=?
  and project=?
  and stage=?
  and version=?
  and run=?
'''
        c.execute(q, gtuple)
        rows = c.fetchall()
        if len(rows) == 0:

            print("Creating merge group:")
            print("  file_type = %s" % gtuple[0])
            print("  file_format = %s" % gtuple[1])
            print("  data_tier = %s" % gtuple[2])
            print("  data_stream = %s" % gtuple[3])
            print("  project = %s" % gtuple[4])
            print("  stage = %s" % gtuple[5])
            print("  version = %s" % gtuple[6])
            print("  run = %d" % gtuple[7])

            q = '''INSERT INTO merge_groups
                   (file_type, file_format, data_tier, data_stream, project, stage, version, run)
                   VALUES(?,?,?,?,?,?,?,?);'''
            c.execute(q, gtuple)
            group_id = c.lastrowid

        else:

            group_id = rows[0][0]

        # Done

        return group_id


    # Calculate merges for eligible unmerged files.
    # Newly identified merges are added to the merged_files table.

    def update_merges(self):

        print('Calculating new merges.')

        # Query and loop over group ids. that have new mergeable files.

        c = self.conn.cursor()
        q = 'SELECT DISTINCT group_id FROM unmerged_files WHERE merge_id=0 ORDER BY group_id;'
        c.execute(q);
        rows = c.fetchall()
        for row in rows:
            group_id = row[0]

            # Query mergable files in this group.

            file_ids = []
            total_size = 0
            oldest_create_date = ''

            q = '''SELECT id, name, size, create_date FROM unmerged_files
                   WHERE merge_id=0 and group_id=? ORDER BY create_date;'''
            c.execute(q, (group_id,))
            rows = c.fetchall()
            for row in rows:
                id = row[0]
                name = row[1]
                size = row[2]
                create_date = row[3]

                # Close the current merge?

                if len(file_ids) > 0 and total_size + size > self.max_size:

                    # Close the current merge.

                    self.add_merge(file_ids, group_id)
                    file_ids = []
                    total_size = 0
                    oldest_create_date = ''

                # Add this file to the current merge

                file_ids.append(id)
                total_size += size
                if oldest_create_date == '':
                    oldest_create_date = create_date

            # Handle final candidate merge.

            if len(file_ids) > 0:
                if total_size >= self.min_size:

                    # Add final merge because it is above the minimum size.

                    self.add_merge(file_ids, group_id)

                else:

                    # Calculate age of oldest unmerged file.

                    t = datetime.datetime.strptime(oldest_create_date, '%Y-%m-%dT%H:%M:%S+00:00')
                    now = datetime.datetime.utcnow()
                    dt = now - t
                    if dt.total_seconds() > self.max_age:

                        # Add final merge because it is too old.

                        self.add_merge(file_ids, group_id)

        # Done.

        self.conn.commit()
        return


    # Add one merge to database.
    # This function creates a new row in the merged_files table.

    def add_merge(self, file_ids, group_id):

        # Add a placeholder row to the merged_files table.

        c = self.conn.cursor()
        q = '''INSERT INTO merged_files (name, group_id, jobid, submit_time, sam_project, status)
               VALUES(?,?,?,?,?,?);'''
        c.execute(q, ('', group_id, '', '', '', 0))
        merge_id = c.lastrowid

        print('Creating merge with %d files.' % len(file_ids))

        # Update the merge_id in each unmerged file row.

        q = 'UPDATE unmerged_files SET merge_id=? WHERE id=?;'
        for id in file_ids:
            c.execute(q, (merge_id, id))

        # Done.

        return


    # Reset merged file.
    # This function is called when an error or inconsistency has been detectored.
    # This may be caused by a failed merging batch job.
    # When this happens, we take the following remedial action.
    # 
    # 1.  Check locations of unmerged files.  If file location does not exist,
    #     remove location from sam.
    #
    # 2.  Delete unmerged files from unmerged_files table.
    #
    # 3.  Delete merged file from merged_files table.
    #
    # Unmerged files with good locations will be rediscovered and merged on subsequent
    # invocations of this merge.py.

    def reset(self, merge_id):

        print('Resetting merged file.')

        # Querey unmerged files.

        c = self.conn.cursor()
        q = 'SELECT id, name FROM unmerged_files WHERE merge_id=?'
        c.execute(q, (merge_id,))
        rows = c.fetchall()

        # Loop over unmerged files.

        for row in rows:
            id = row[0]
            f = row[1]
            print('Checking unmerged file: %s' % f)

            # Get location(s).

            locs = self.samweb.locateFile(f)
            for loc in locs:
                if loc['location_type'] == 'disk':
                    dir = os.path.join(loc['mount_point'], loc['subdir'])
                    fp = os.path.join(dir, f)
                    if larbatch_posix.exists(fp):
                        print('Location OK.')
                    else:
                        print('Removing bad location from sam.')
                        self.samweb.removeFileLocation(f, loc['full_path'])

            # Delete unmerged file from database.

            print('Deleting unmerged file from database.')
            q = 'DELETE FROM unmerged_files WHERE id=?'
            c.execute(q, (id,))

        # Delete merged file from database.

        print('Deleting merged file from database.')
        q = 'DELETE FROM merged_files WHERE id=?'
        c.execute(q, (merge_id,))
        self.conn.commit()
        return
        

    # Update status of ongoing merges.

    def update_status(self):

        # In this function, we make a double loop over merged files and statuses.

        c = self.conn.cursor()

        # First loop over statuses in reverse order.

        for status in range(self.max_status, self.min_status-1, -1):

            # Query and loop over merged files with this status.

            q = '''SELECT name, id, group_id, sam_project
                   FROM merged_files WHERE status=? ORDER BY id;'''
            c.execute(q, (status,))
            rows = c.fetchall()
            for row in rows:
                merged_file = row[0]
                merge_id = row[1]
                group_id = row[2]
                prjname = row[3]

                # Query metadata belonging to this merge group.

                q = '''SELECT file_type, file_format, data_tier, data_stream,
                       project, stage, version
                       FROM merge_groups WHERE id=?'''
                c.execute(q, (group_id,))
                row = c.fetchone()
                if row != None:
                    file_type = row[0]
                    file_format = row[1]
                    data_tier = row[2]
                    data_stream = row[3]
                    ubproject = row[4]
                    ubstage = row[5]
                    ubversion = row[6]

                    if merged_file != '':
                        print('\nStatus=%d, file %s' % (status, merged_file))
                    else:
                        print('\nStatus=%d, unnamed file' % status)

                    if status == 6:

                        print('Declaring file bad %s' % merged_file)
                        mdmod = {'content_status': 'bad'}
                        print('Updating metadata.')
                        self.samweb.modifyFileMetadata(merged_file, mdmod)

                        # Reset this merged file.

                        self.reset(merge_id)

                    elif status == 5:

                        print('Processing finished for file %s' % merged_file)
                        c = self.conn.cursor()
                        q = 'DELETE FROM merged_files WHERE id=?'
                        c.execute(q, (merge_id,))
                        self.conn.commit()

                    elif status == 4:

                        # Do cleanup for this merged file.

                        print('Doing cleanup for merged file %s' % merged_file)

                        # First query unmerged files corresponsing to this merged file.

                        unmerged_files = []
                        q = 'SELECT name FROM unmerged_files WHERE merge_id=?'
                        c.execute(q, (merge_id,))
                        rows = c.fetchall()
                        for row in rows:
                            unmerged_files.append(row[0])

                        # Loop over unmerged files.

                        for f in unmerged_files:

                            print('Doing cleanup for unmerged file %s' % f)

                            # First modify the sam metadata of unmerged files 
                            # to set merge.merged=1.  That will make this
                            # unmerged file invisible to this script.

                            mdmod = {'merge.merged': 1}
                            print('Updating metadata.')
                            self.samweb.modifyFileMetadata(f, mdmod)

                            # Remove (disk) locations of unmerged file.

                            locs = self.samweb.locateFile(f)
                            if len(locs) > 0:
                                print('Cleaning disk locations.')
                                for loc in locs:
                                    if loc['location_type'] == 'disk':

                                        # Delete unmerged file from disk.

                                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                                        fp = os.path.join(dir, f)
                                        print('Deleting file from disk.')
                                        if larbatch_posix.exists(fp):
                                            larbatch_posix.remove(fp)

                                        # Remove location from sam.

                                        print('Removing location from sam.')
                                        self.samweb.removeFileLocation(f, loc['full_path'])

                            # Delete unmerged file from merge database.

                            print('Deleting file from merge database: %s' % f)
                            c = self.conn.cursor()
                            q = 'DELETE FROM unmerged_files WHERE name=?'
                            c.execute(q, (f,))

                        # End of loop over unmerged files.
                        # Cleaning done.
                        # Update status of merged file to 5

                        print('Cleaning finished.')
                        q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                        c.execute(q, (5, merge_id))
                        self.conn.commit()

                    elif status == 3:

                        # Check whether this file has a location.

                        print('Checking location for file %s' % merged_file)
                        locs = self.samweb.locateFile(merged_file)

                        # If file has been located, advance to state 4.

                        if len(locs) > 0:
                            print('File located.')
                            q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                            c.execute(q, (4, merge_id))
                            self.conn.commit()
                        else:
                            print('File not located.')

                            # Check metadata of this file.

                            md = self.samweb.getMetadata(merged_file)

                            # Get age of this file.

                            t = datetime.datetime.strptime(md['create_date'],
                                                           '%Y-%m-%dT%H:%M:%S+00:00')
                            now = datetime.datetime.utcnow()
                            dt = now - t

                            # If this file too old, set error status.

                            if dt.total_seconds() > 3*24*3600:
                                print('File is too old.  Set error status.')
                                q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                                c.execute(q, (6, merge_id))
                                self.conn.commit()

                    elif status == 2:

                        # Check whether this file has been declared to sam.

                        print('Checking metadata for file %s' % merged_file)
                        md = None
                        try:
                            md = self.samweb.getMetadata(merged_file)
                        except:
                            md = None

                        # If file has been declared, advance status to 3.

                        if md != None:
                            print('File declared.')
                            q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                            c.execute(q, (3, merge_id))
                            self.conn.commit()
                        else:
                            print('File not declared.')

                            # File is not (yet) declared.

                            if prjname == '' or prjname == None:

                                # If the project name is invalid, set the status
                                # back to zero.

                                print('Malformed project name: %s' % prjname)
                                self.reset(merge_id)

                            else:

                                # Rather than trying to monitor the batch system, we only
                                # monitor the sam project.  If the project has been ended
                                # for a minimum amount of time without the output file being
                                # declared, reset this merged file.

                                prjstat = self.samweb.projectSummary(prjname)
                                endstr = prjstat['project_end_time']
                                if len(endstr) > 1:

                                    # Calculate how long since the project ended.

                                    t = datetime.datetime.strptime(endstr,
                                                                   '%Y-%m-%dT%H:%M:%S.%f+00:00')
                                    now = datetime.datetime.utcnow()
                                    dt = now - t

                                    if dt.total_seconds() > 600:

                                        # Batch job failed.
                                        # Set status back to 0.

                                        print('Project ended: %s' % prjname)
                                        self.reset(merge_id)

                                    else:

                                        print('Project recently ended: %s' % prjname)

                                else:
                                    print('Project running: %s' % prjname)


                    elif status == 0:

                        n2 = self.nstat2()
                        print('%d sam projects with status 2' % n2)
                        if n2 >= 200:
                            print('Quitting because there are too many jobs with status 2')
                            break

                        # Ready to merge.

                        if file_format == 'artroot':

                            # At this point we should submit a merging batch job.
                            # Check whether this is pssible.

                            if self.fclpath == None:
                                print('No batch submission because no xml file was specified.')
                                break
                            if self.numjobs == 0:
                                print('Maximum number of batch submissions exceeded.')
                                break
                            print('%d batch submissions remaining.' % self.numjobs)

                            # Add this file to the merge queue.

                            self.merge_queue.append(merge_id)
                            if len(self.merge_queue) >= self.numprj:
                                self.process_merge_queue()
                                self.numjobs -= 1

        # Done looping over statuses.

        # Finish submitting files left in merge queue.

        if len(self.merge_queue) > 0:
            self.process_merge_queue()

        # Done

        return

    # Submit batch jobs for each file in merge queue.

    def process_merge_queue(self):

        if len(self.merge_queue) == 0:
            return

        # Open combined fcl file.

        if os.path.exists(self.fclpath):
            os.remove(self.fclpath)
        fcl = open(self.fclpath, 'w')

        # Loop over merge queue.

        sam_defnames = ''   # Colon-separated list.
        sam_projects = ''   # Colon-separated list.

        output_names_dict = {}
        sam_projects_dict = {}

        nmerge = -1
        for merge_id in self.merge_queue:
            nmerge += 1

            # Query unmerged files associated with this merged file.

            unmerged_files = []
            c = self.conn.cursor()
            q = 'SELECT name FROM unmerged_files WHERE merge_id=?'
            c.execute(q, (merge_id,))
            rows = c.fetchall()
            for row in rows:
                unmerged_files.append(row[0])

            # Query parents of unmerged files (i.e. grandparents of merged file).

            grandparents = set([])
            for unmerged_file in unmerged_files:
                md = self.samweb.getMetadata(unmerged_file)
                if 'parents' in md:
                    for parent in md['parents']:
                        pname = parent['file_name']
                        if not pname in grandparents:
                            grandparents.add(pname)

            # Query sam metadata from first unmerged file.
            # We will use this to generate metadata for merged files.

            md = self.samweb.getMetadata(unmerged_files[0])
            input_name = md['file_name']
            app_family = md['application']['family']
            app_version = md['application']['version']
            group = md['group']
            file_type = md['file_type']
            run_type = md['runs'][0][2]
            ubproject = md['ub_project.name']
            ubstage = md['ub_project.stage']
            ubversion = md['ub_project.version']
            data_tier = md['data_tier']
            data_stream = md['data_stream']

            # Generate a unique output file name.
            # We use a name that roughly matches the RootOutput pattern
            # "%ifb_%tc_merged.root".

            tstr = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
            output_name = '%s_%s_merged.root' % (input_name.split('.')[0], tstr)

            # Keep this name short enough so that condor_lar.sh won't shorten it.

            if len(output_name) > 190:
                output_name = '%s_%s.root' % (output_name[:140], uuid.uuid4())
                print('Assigning name %s' % output_name)
                if len(output_name) > 190:
                    print('Output name is too long.')
                    sys.exit(1)

            # Remember output name for database update later.

            output_names_dict[merge_id] = output_name

            # Generate a fcl file customized for this merged file.

            fcl.write('#---STAGE %d\n\n' % nmerge)
            fcl.write('process_name: Merge\n')
            fcl.write('services:\n')
            fcl.write('{\n')
            fcl.write('  scheduler: { defaultExceptions: false }\n')
            fcl.write('  FileCatalogMetadata:\n')
            fcl.write('  {\n')
            fcl.write('    applicationFamily: "%s"\n' % app_family)
            fcl.write('    applicationVersion: "%s"\n' % app_version)
            fcl.write('    fileType: "%s"\n' % file_type)
            fcl.write('    group: "%s"\n' % group)
            fcl.write('    runType: "%s"\n' % run_type)
            fcl.write('  }\n')
            fcl.write('  FileCatalogMetadataMicroBooNE:\n')
            fcl.write('  {\n')
            fcl.write('    FCLName: "%s"\n' % os.path.basename(self.fclpath))
            fcl.write('    FCLVersion: "%s"\n' % app_version)
            fcl.write('    ProjectName: "%s"\n' % ubproject)
            fcl.write('    ProjectStage: "%s"\n' % ubstage)
            fcl.write('    ProjectVersion: "%s"\n' % ubversion)
            if len(grandparents) > 0:
                fcl.write('    Parameters: [ ')
                first = True
                ngp = 0
                for grandparent in grandparents:
                    if not first:
                        fcl.write(',\n                  ')
                    first = False
                    fcl.write('"mixparent%d", "%s"' % (ngp, grandparent))
                    ngp += 1
                fcl.write(' ]\n')
            fcl.write('  }\n')
            fcl.write('}\n')
            fcl.write('source:\n')
            fcl.write('{\n')
            fcl.write('  module_type: RootInput\n')
            fcl.write('}\n')
            fcl.write('physics:\n')
            fcl.write('{\n')
            fcl.write('  stream1:  [ out1 ]\n')
            fcl.write('}\n')
            fcl.write('outputs:\n')
            fcl.write('{\n')
            fcl.write('  out1:\n')
            fcl.write('  {\n')
            fcl.write('    module_type: RootOutput\n')
            fcl.write('    fileName: "%s"\n' % output_name)
            fcl.write('    dataTier: "%s"\n' % data_tier)
            fcl.write('    streamName:  "%s"\n' % data_stream)
            fcl.write('    compressionLevel: 3\n')
            fcl.write('  }\n')
            fcl.write('}\n')
            fcl.write('#---END_STAGE\n')

            # Make sam dataset for unmerged files.

            dim = 'file_name '
            first = True
            for unmerged_file in unmerged_files:
                if not first:
                    dim += ','
                first = False
                dim += unmerged_file

            defname='merge_%s' % uuid.uuid4()
            if len(sam_defnames) > 0:
                sam_defnames += ':'
            sam_defnames += defname
            print('Creating sam definition %s' % defname)
            self.samweb.createDefinition(defname, dim,
                                         user=project_utilities.get_user(), 
                                         group=project_utilities.get_experiment())

            # Generate sam project name

            prjname = self.samweb.makeProjectName(defname)
            if len(sam_projects) > 0:
                sam_projects += ':'
            sam_projects += prjname

            # Start sam project.

            print('Starting project %s' % prjname)
            self.samweb.startProject(prjname,
                                     defname=defname, 
                                     station=project_utilities.get_experiment(),
                                     group=project_utilities.get_experiment(),
                                     user=project_utilities.get_user())

            # Remember sam project name.

            sam_projects_dict[merge_id] = prjname

        # Done looping over merged files.
        # Close combined fcl file.

        fcl.close()

        # Temporary directory where we will copy the batch script.

        tmpdir = tempfile.mkdtemp()

        # Temporary directory where we will assemble other files for batch worker.

        tmpworkdir = tempfile.mkdtemp()

        # Copy fcl file to work directory.

        workfcl = os.path.join(tmpworkdir, os.path.basename(self.fclpath))
        if os.path.abspath(self.fclpath) != os.path.abspath(workfcl):
            larbatch_posix.copy(self.fclpath, workfcl)

        # Copy and rename batch script to work directory.

        workname = 'merge-%s-%s-%s.sh' % (ubstage, ubproject, self.probj.release_tag)
        workscript = os.path.join(tmpdir, workname)
        if self.stobj.script != workscript:
            larbatch_posix.copy(self.stobj.script, workscript)

        # Copy worker initialization script to work directory.

        if self.stobj.init_script != '':
            if not larbatch_posix.exists(self.stobj.init_script):
                raise RuntimeError('Worker initialization script %s does not exist.\n' % \
                    self.stobj.init_script)
            work_init_script = os.path.join(tmpworkdir, os.path.basename(self.stobj.init_script))
            if self.stobj.init_script != work_init_script:
                larbatch_posix.copy(self.stobj.init_script, work_init_script)

        # Copy worker initialization source script to work directory.

        if self.stobj.init_source != '':
            if not larbatch_posix.exists(self.stobj.init_source):
                raise RuntimeError('Worker initialization source script %s does not exist.\n' % \
                    self.stobj.init_source)
            work_init_source = os.path.join(tmpworkdir, os.path.basename(self.stobj.init_source))
            if self.stobj.init_source != work_init_source:
                larbatch_posix.copy(self.stobj.init_source, work_init_source)

        # Copy worker end-of-job script to work directory.

        if self.stobj.end_script != '':
            if not larbatch_posix.exists(self.stobj.end_script):
                raise RuntimeError('Worker end-of-job script %s does not exist.\n' % \
                    self.stobj.end_script)
            work_end_script = os.path.join(tmpworkdir, os.path.basename(self.stobj.end_script))
            if self.stobj.end_script != work_end_script:
                larbatch_posix.copy(self.stobj.end_script, work_end_script)

        # Copy helper scripts to work directory.

        helpers = ('root_metadata.py',
                   'validate_in_job.py',
                   'mkdir.py',
                   'emptydir.py')

        for helper in helpers:

            # Find helper script in execution path.

            jobinfo = subprocess.Popen(['which', helper],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            jobout, joberr = jobinfo.communicate()
            rc = jobinfo.poll()
            helper_path = jobout.splitlines()[0].strip()
            if rc == 0:
                work_helper = os.path.join(tmpworkdir, helper)
                if helper_path != work_helper:
                    larbatch_posix.copy(helper_path, work_helper)
            else:
                print('Helper script %s not found.' % helper)

        # Copy helper python modules to work directory.
        # Note that for this to work, these modules must be single files.

        helper_modules = ('larbatch_posix',
                          'project_utilities',
                          'larbatch_utilities',
                          'experiment_utilities',
                          'extractor_dict')

        for helper_module in helper_modules:

            # Find helper module files.

            jobinfo = subprocess.Popen(['python'],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            jobinfo.stdin.write('import %s\nprint %s.__file__\n' % (helper_module, helper_module))
            jobout, joberr = jobinfo.communicate()
            rc = jobinfo.poll()
            helper_path = jobout.splitlines()[-1].strip()
            if rc == 0:
                #print 'helper_path = %s' % helper_path
                work_helper = os.path.join(tmpworkdir, os.path.basename(helper_path))
                if helper_path != work_helper:
                    larbatch_posix.copy(helper_path, work_helper)
            else:
                print('Helper python module %s not found.' % helper_module)

        # Make a tarball out of all of the files in tmpworkdir in stage.workdir

        tmptar = '%s/work.tar' % tmpworkdir
        jobinfo = subprocess.Popen(['tar','-cf', tmptar, '-C', tmpworkdir,
                                    '--mtime=2018-01-01',
                                    '--exclude=work.tar', '.'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        jobout, joberr = jobinfo.communicate()
        rc = jobinfo.poll()
        if rc != 0:
            raise RuntimeError('Failed to create work tarball in %s' % tmpworkdir)

        # Construct jobsub_submit command.

        command = ['jobsub_submit']

        # Add jobsub_submit boilerplate options.  Copied from project.py.

        command.append('--group=%s' % project_utilities.get_experiment())
        role = project_utilities.get_role()
        if self.probj.role != '':
            role = self.probj.role
        command.append('--role=%s' % role)
        if self.stobj.resource != '':
            command.append('--resource-provides=usage_model=%s' % self.stobj.resource)
        elif self.probj.resource != '':
            command.append('--resource-provides=usage_model=%s' % self.probj.resource)
        if self.stobj.lines != '':
            command.append('--lines=%s' % self.stobj.lines)
        elif self.probj.lines != '':
            command.append('--lines=%s' % self.probj.lines)
        if self.stobj.site != '':
            command.append('--site=%s' % self.stobj.site)
        if self.stobj.blacklist != '':
            command.append('--blacklist=%s' % self.stobj.blacklist)
        if self.stobj.cpu != 0:
            command.append('--cpu=%d' % self.stobj.cpu)
        if self.stobj.disk != '':
            command.append('--disk=%s' % self.stobj.disk)
        if self.stobj.memory != 0:
            command.append('--memory=%d' % self.stobj.memory)
        if self.probj.os != '':
            command.append('--OS=%s' % self.probj.os)
        if self.stobj.jobsub != '':
            for word in self.stobj.jobsub.split():
                command.append(word)
        opt = project_utilities.default_jobsub_submit_options()
        if opt != '':
            for word in opt.split():
                command.append(word)

        # Copy tarball containing fcl file and helpers.

        command.extend(['-f', 'dropbox://%s' % tmptar])

        # Batch script.

        workurl = "file://%s" % workscript
        command.append(workurl)

        # Add batch script options.

        command.extend([' --group', project_utilities.get_experiment()])
        command.extend([' -c', os.path.basename(self.fclpath)])
        command.extend([' --ups', project_utilities.get_ups_products()])
        if self.probj.release_tag != '':
            command.extend([' -r', self.probj.release_tag])
        command.extend([' -b', self.probj.release_qual])
        if self.probj.local_release_tar != '':
            command.extend([' --localtar', self.probj.local_release_tar])
        command.extend([' --outdir', self.stobj.outdir])
        command.extend([' --logdir', self.stobj.logdir])
        if self.stobj.schema != '':
            command.extend([' --sam_schema', self.stobj.schema])
        if self.stobj.init_script != '':
            command.extend([' --init-script', os.path.basename(self.stobj.init_script)])
        if self.stobj.init_source != '':
            command.extend([' --init-source', os.path.basename(self.stobj.init_source)])
        if self.stobj.end_script != '':
            command.extend([' --end-script', os.path.basename(self.stobj.end_script)])
        command.extend([' --init', project_utilities.get_setup_script_path()])
        if self.stobj.validate_on_worker == 1:
            print('Validation will be done on the worker node %d' % self.stobj.validate_on_worker)
            command.extend([' --validate'])
            command.extend([' --declare'])
        if self.stobj.copy_to_fts == 1:
            command.extend([' --copy'])
        command.extend(['--sam_station', project_utilities.get_experiment()])
        command.extend(['--sam_group', project_utilities.get_experiment()])
        command.extend(['--sam_defname', sam_defnames])
        command.extend(['--sam_project', sam_projects])

        # Invoke the job submission command and capture the output.

        print('Invoke jobsub_submit')
        submit_timeout = 3600000
        q = Queue.Queue()
        jobinfo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        thread = threading.Thread(target=project_utilities.wait_for_subprocess, args=[jobinfo, q])
        thread.start()
        thread.join(timeout=submit_timeout)
        if thread.is_alive():
            jobinfo.terminate()
            thread.join()
        rc = q.get()
        jobout = q.get()
        joberr = q.get()

        # Clean up.

        if larbatch_posix.isdir(tmpdir):
            larbatch_posix.rmtree(tmpdir)
        if larbatch_posix.isdir(tmpworkdir):
            larbatch_posix.rmtree(tmpworkdir)

        # Test whether job submission succeeded.

        batchok = False
        if rc == 0:

            # Extract jobsub id from captured output.

            jobid = ''
            for line in jobout.split('\n'):
                if "JobsubJobId" in line:
                    jobid = line.strip().split()[-1]
            if jobid != '':
                batchok = True

        if batchok:

            # Batch job submission succeeded.

            print('Batch job submission succeeded.')
            print('Job id = %s' % jobid)

            # Update merged_files table with information about this job submission.

            submit_time = datetime.datetime.strftime(datetime.datetime.now(), 
                                                     '%Y-%m-%d %H:%M:%S')
            for merge_id in self.merge_queue:
                q = '''UPDATE merged_files
                SET name=?,jobid=?,submit_time=?,sam_project=?,status=?
                WHERE id=?;'''
                c.execute(q, (output_names_dict[merge_id], jobid, submit_time,
                              sam_projects_dict[merge_id], 2, merge_id))

            # Done updating database in this function.

            self.conn.commit()

        else:

            # Batch job submission failed.

            print('Batch job submission failed.')
            print(jobout)
            print(joberr)

            # Stop sam projects.

            for prj in sam_projects.split(':'):
                print('Stopping sam project %s' % prj)
                self.samweb.stopProject(prj)

        # Done.

        self.merge_queue = []
        return


    # Return the number of status 0 files in the database.

    def nstat0(self):
        c = self.conn.cursor()
        q = 'SELECT COUNT(*) FROM merged_files WHERE status=0'
        c.execute(q)
        row = c.fetchone()
        n0 = row[0]
        return n0

    # Return the number of status 2 files in the database.

    def nstat2(self):
        c = self.conn.cursor()
        q = 'SELECT COUNT(DISTINCT sam_project) FROM merged_files WHERE status=2'
        c.execute(q)
        row = c.fetchone()
        n0 = row[0]
        return n0


# Check whether a similar process is already running.
# Return true if yes.

def check_running(argv):

    result = 0

    # Look over pids in /proc.

    for pid in os.listdir('/proc'):
        if pid.isdigit() and int(pid) != os.getpid():
            procfile = os.path.join('/proc', pid)
            try:
                pstat = os.stat(procfile)

                # Only look at processes that match this process uid.

                if pstat.st_uid == os.getuid():

                    # Get command line.

                    cmdfile = os.path.join('/proc', pid, 'cmdline')
                    cmd = open(cmdfile).read()
                    words = cmd.split('\0')
                    if len(words) > 0 and words[0].endswith('merge.py'):
                        result = 1
                    if len(words) > 1 and \
                       words[0].endswith('python') and words[1].endswith('merge.py'):
                        result = 1
            except:
                pass

    # Done.

    return result


# Main procedure.

def main(argv):

    if check_running(argv):
        print('Quitting because similar process is already running.')
        sys.exit(0)

    # Parse arguments.

    xmlfile = ''
    projectname = ''
    stagename = ''
    database = 'merge.db'
    defname = ''
    max_size = 2500000000
    min_size = 1000000000
    max_age = 3*24*3600
    min_status = 0
    max_status = 6

    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help' :
            help()
            return 0
        elif args[0] == '--xml' and len(args) > 1:
            xmlfile = args[1]
            del args[0:2]
        elif args[0] == '--project' and len(args) > 1:
            projectname = args[1]
            del args[0:2]
        elif args[0] == '--stage' and len(args) > 1:
            stagename = args[1]
            del args[0:2]
        elif args[0] == '--database' and len(args) > 1:
            database = args[1]
            del args[0:2]
        elif args[0] == '--defname' and len(args) > 1:
            defname = args[1]
            del args[0:2]
        elif args[0] == '--max_size' and len(args) > 1:
            max_size = int(args[1])
            del args[0:2]
        elif args[0] == '--min_size' and len(args) > 1:
            min_size = int(args[1])
            del args[0:2]
        elif args[0] == '--max_age' and len(args) > 1:
            if args[1][-1] == 'h' or args[1][-1] == 'H':
                max_age = 3600 * int(args[1][:-1])
            elif args[1][-1] == 'd' or args[1][-1] == 'D':
                max_age = 24 * 3600 * int(args[1][:-1])
            else:
                max_age = int(args[1])
            del args[0:2]
        elif args[0] == '--min_status' and len(args) > 1:
            min_status = int(args[1])
            del args[0:2]
        elif args[0] == '--max_status' and len(args) > 1:
            max_status = int(args[1])
            del args[0:2]
        else:
            print('Unknown option %s' % args[0])
            return 1

    # Create merge engine.

    engine = MergeEngine(xmlfile, projectname, stagename, defname,
                         database, max_size, min_size, max_age,
                         min_status, max_status)
    if min_status == 0:
        n0 = engine.nstat0()
        if n0 == 0:
            engine.update_unmerged_files()
            engine.update_merges()
    engine.update_status()

    # Done.

    print('\nFinished.')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
