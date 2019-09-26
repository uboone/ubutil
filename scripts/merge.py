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
#     This script imports project.py as a python module and uses project.py
#     functions to interpret the xml file and to submit batch jobs.
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
#     script.  However, merging batch jobs are submitted singly.
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

import sys, os, datetime, uuid, traceback
import StringIO
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
                print line[2:],
            else:
                print

class MergeEngine:

    # Constructor.

    def __init__(self, xmlfile, projectname, stagename, defname,
                 database, max_size, min_size, max_age):

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
                print 'XML file not found: %s' % xmlfile

            # Use project.py to parse xml file and extract project and stage objects.

            self.probj = project.get_project(xmlpath, projectname, stagename)
            self.stobj = self.probj.get_stage(stagename)

            # Extract the fcl path from stage object.
            # If not already absolute path, convert to absolute path.

            if type(self.stobj.fclname) == type([]) and len(self.stobj.fclname) > 0:
                self.fclpath = os.path.abspath(self.stobj.fclname[0])
            elif type(self.stobj.fclname) == type('') or type(self.stobj.fclname) == type(u''):
                self.fclpath = os.path.abspath(self.stobj.fclname)

            # Store the absolute path back in stage object.

            self.stobj.fclname = [self.fclpath]

            # Don't let project.py think this is a generator job.

            self.stobj.maxfluxfilemb = 0

            # Save the maximum number of batch jobs to submit.

            self.numjobs = self.stobj.num_jobs

        # Other tunable parameters.

        self.defname = defname     # File selectionn dataset definition.
        self.max_size = max_size   # Maximum merge file size in bytes.
        self.min_size = min_size   # Minimum merge file size in bytes.
        self.max_age = max_age     # Maximum unmerged file age in seconds.

        # Done.

        return


    # Destructor.

    def __del__(self):

        self.conn.close()


    # Open database connection.

    def open_database(self, database):

        conn = sqlite3.connect(database)

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

        print 'Querying unmerged files from sam.'
        extra_clause = ''
        if self.defname != '':
            extra_clause = 'and defname: %s' % self.defname
        dim = 'merge.merge 1 and merge.merged 0 %s with availability physical' % extra_clause
        files = self.samweb.listFiles(dim)
        print '%d unmerged files.' % len(files)
        print 'Updating unmerged_files table in database.'
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
                print 'File %s is already on tape.' % f

                # Since file is on tape, remove any disk locations.
                # This shouldn't really ever happen.
            
                for loc in locs:
                    if loc['location_type'] == 'disk':
                        print 'Removing disk location.'
                        self.samweb.removeFileLocation(f, loc['full_path'])

                # Modify metadata to set merge.merged flag to be true, so that this
                # file will become invisible to merging.

                mdmod = {'merge.merged': 1}
                print 'Updating metadata to set merged flag.'
                self.samweb.modifyFileMetadata(f, mdmod)

            else:

                print 'Adding unmerged file %s' % f
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

            print "Creating merge group:"
            print "  file_type = %s" % gtuple[0]
            print "  file_format = %s" % gtuple[1]
            print "  data_tier = %s" % gtuple[2]
            print "  data_stream = %s" % gtuple[3]
            print "  project = %s" % gtuple[4]
            print "  stage = %s" % gtuple[5]
            print "  version = %s" % gtuple[6]
            print "  run = %d" % gtuple[7]

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

        print 'Calculating new merges.'

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

        print 'Creating merge with %d files.' % len(file_ids)

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

        print 'Resetting merged file.'

        # Querey unmerged files.

        c = self.conn.cursor()
        q = 'SELECT id, name FROM unmerged_files WHERE merge_id=?'
        c.execute(q, (merge_id,))
        rows = c.fetchall()

        # Loop over unmerged files.

        for row in rows:
            id = row[0]
            f = row[1]
            print 'Checking unmerged file: %s' % f

            # Get location(s).

            locs = self.samweb.locateFile(f)
            for loc in locs:
                if loc['location_type'] == 'disk':
                    dir = os.path.join(loc['mount_point'], loc['subdir'])
                    fp = os.path.join(dir, f)
                    if larbatch_posix.exists(fp):
                        print 'Location OK.'
                    else:
                        print 'Removing bad location from sam.'
                        self.samweb.removeFileLocation(f, loc['full_path'])

            # Delete unmerged file from database.

            print 'Deleting unmerged file from database.'
            q = 'DELETE FROM unmerged_files WHERE id=?'
            c.execute(q, (id,))

        # Delete merged file from database.

        print 'Deleting merged file from database.'
        q = 'DELETE FROM merged_files WHERE id=?'
        c.execute(q, (merge_id,))
        self.conn.commit()
        return
        

    # Update status of ongoing merges.

    def update_status(self):

        # In this function, we make a double loop over merged files and statuses.

        c = self.conn.cursor()

        # First loop over statuses in reverse order.

        for status in range(5,-1,-1):

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
                        print '\nStatus=%d, file %s' % (status, merged_file)
                    else:
                        print '\nStatus=%d, unnamed file' % status

                    if status == 6:

                        print 'Error status for file %s' % merged_file

                    elif status == 5:

                        print 'Processing finished for file %s' % merged_file
                        c = self.conn.cursor()
                        q = 'DELETE FROM merged_files WHERE id=?'
                        c.execute(q, (merge_id,))
                        self.conn.commit()

                    elif status == 4:

                        # Do cleanup for this merged file.

                        print 'Doing cleanup for merged file %s' % merged_file

                        # First query unmerged files corresponsing to this merged file.

                        unmerged_files = []
                        q = 'SELECT name FROM unmerged_files WHERE merge_id=?'
                        c.execute(q, (merge_id,))
                        rows = c.fetchall()
                        for row in rows:
                            unmerged_files.append(row[0])

                        # Loop over unmerged files.

                        for f in unmerged_files:

                            print 'Doing cleanup for unmerged file %s' % f

                            # First modify the sam metadata of unmerged files 
                            # to set merge.merged=1.  That will make this
                            # unmerged file invisible to this script.

                            mdmod = {'merge.merged': 1}
                            print 'Updating metadata.'
                            self.samweb.modifyFileMetadata(f, mdmod)

                            # Remove (disk) locations of unmerged file.

                            locs = self.samweb.locateFile(f)
                            if len(locs) > 0:
                                print 'Cleaning disk locations.'
                                for loc in locs:
                                    if loc['location_type'] == 'disk':

                                        # Delete unmerged file from disk.

                                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                                        fp = os.path.join(dir, f)
                                        print 'Deleting file from disk.'
                                        if larbatch_posix.exists(fp):
                                            larbatch_posix.remove(fp)

                                        # Remove location from sam.

                                        print 'Removing location from sam.'
                                        self.samweb.removeFileLocation(f, loc['full_path'])

                            # Delete unmerged file from merge database.

                            print 'Deleting file from merge database: %s' % f
                            c = self.conn.cursor()
                            q = 'DELETE FROM unmerged_files WHERE name=?'
                            c.execute(q, (f,))

                        # End of loop over unmerged files.
                        # Cleaning done.
                        # Update status of merged file to 5

                        print 'Cleaning finished.'
                        q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                        c.execute(q, (5, merge_id))
                        self.conn.commit()

                    elif status == 3:

                        # Check whether this file has a location.

                        print 'Checking location for file %s' % merged_file
                        locs = self.samweb.locateFile(merged_file)

                        # If file has been located, advance to state 4.

                        if len(locs) > 0:
                            print 'File located.'
                            q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                            c.execute(q, (4, merge_id))
                            self.conn.commit()
                        else:
                            print 'File not located.'

                    elif status == 2:

                        # Check whether this file has been declared to sam.

                        print 'Checking metadata for file %s' % merged_file
                        md = None
                        try:
                            md = self.samweb.getMetadata(merged_file)
                        except:
                            md = None

                        # If file has been declared, advance status to 3.

                        if md != None:
                            print 'File declared.'
                            q = '''UPDATE merged_files SET status=? WHERE id=?;'''
                            c.execute(q, (3, merge_id))
                            self.conn.commit()
                        else:
                            print 'File not declared.'

                            # File is not (yet) declared.

                            if prjname == '' or prjname == None:

                                # If the project name is invalid, set the status
                                # back to zero.

                                print 'Malformed project name: %s' % prjname
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

                                        print 'Project ended: %s' % prjname
                                        self.reset(merge_id)

                                    else:

                                        print 'Project recently ended: %s' % prjname

                                else:
                                    print 'Project running: %s' % prjname


                    elif status == 0:

                        # Ready to merge.

                        if file_format == 'artroot':

                            # At this point we should submit a merging batch job.
                            # Check whether this is pssible.

                            if self.fclpath == None:
                                print 'No batch submission because no xml file was specified.'
                                break
                            if self.numjobs == 0:
                                print 'Maximum number of batch submissions exceeded.'
                                break
                            print '%d batch submissions remaining.' % self.numjobs
                            self.numjobs -= 1

                            # Query unmerged files associated with this merged files.

                            unmerged_files = []
                            q = 'SELECT name FROM unmerged_files WHERE merge_id=?'
                            c.execute(q, (merge_id,))
                            rows = c.fetchall()
                            for row in rows:
                                unmerged_files.append(row[0])

                            # Query parents of unmerged files (i.e. grandparents of merged file).

                            grandparents = set([])
                            for unmerged_file in unmerged_files:
                                md = self.samweb.getMetadata(unmerged_file)
                                for parent in md['parents']:
                                    pname = parent['file_name']
                                    if not pname in grandparents:
                                        grandparents.add(pname)

                            # Append the grandparent set to the stage object.
                            # This attribute is checked by experiment_utilities.get_sam_metadata

                            if hasattr(self.stobj, 'mixparents'):
                                delattr(self.stobj, 'mixparents')
                            if len(grandparents) > 0:
                                self.stobj.mixparents = grandparents

                            # Query sam metadata from first unmerged file.
                            # We will use this to generate metadata for merged files.

                            md = self.samweb.getMetadata(unmerged_files[0])
                            input_name = md['file_name']
                            app_family = md['application']['family']
                            app_version = md['application']['version']
                            group = md['group']
                            run_type = md['runs'][0][2]

                            # Generate a unique output file name.
                            # We do that in this script, rather than letting the batch
                            # job pick the file name, so that we can properly update the
                            # merged_files database table.  We use a name that roughly
                            # matches the RootOutput pattern "%ifb_%tc_merged.root".

                            tstr = datetime.datetime.strftime(datetime.datetime.now(), 
                                                              '%Y%m%d%H%M%S')
                            output_name = '%s_%s_merged.root' % (input_name.split('.')[0], tstr)
                            print 'Assigning name %s' % output_name

                            # Generate a fcl file customized for this merged file.

                            if os.path.exists(self.fclpath):
                                os.remove(self.fclpath)
                            fcl = open(self.fclpath, 'w')
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
                            fcl.write('}\n')
                            fcl.write('source:\n')
                            fcl.write('{\n')
                            fcl.write('  module_type: RootInput\n')
                            fcl.write('}\n')
                            fcl.write('physics:\n')
                            fcl.write('{\n')
                            fcl.write('  stream1:  [ %s ]\n' % data_stream)
                            fcl.write('}\n')
                            fcl.write('outputs:\n')
                            fcl.write('{\n')
                            fcl.write('  %s:\n' % data_stream)
                            fcl.write('  {\n')
                            fcl.write('    module_type: RootOutput\n')
                            fcl.write('    fileName: "%s"\n' % output_name)
                            fcl.write('    dataTier: "%s"\n' % data_tier)
                            fcl.write('    streamName:  "%s"\n' % data_stream)
                            fcl.write('    compressionLevel: 3\n')
                            fcl.write('  }\n')
                            fcl.write('}\n')
                            fcl.write('microboone_tfile_metadata:\n')
                            fcl.write('{\n')
                            fcl.write('  JSONFileName: "ana_hist.root.json"\n')
                            fcl.write('  GenerateTFileMetadata: false\n')
                            fcl.write('  dataTier:  "root-tuple"\n')
                            fcl.write('  fileFormat: "root"\n')
                            fcl.write('}\n')
                            fcl.close()

                            # Make sam dataset for unmerged files.

                            dim = 'file_name '
                            first = True
                            for unmerged_file in unmerged_files:
                                if not first:
                                    dim += ','
                                first = False
                                dim += unmerged_file

                            defname='merge_%s' % uuid.uuid4()
                            print 'Creating sam definition %s' % defname
                            self.samweb.createDefinition(defname, dim,
                                                         user=project_utilities.get_user(), 
                                                         group=project_utilities.get_experiment())


                            # Submit batch job.

                            print 'Submitting batch job.'
                            jobid, prjname = self.submit(defname, file_type, run_type, 
                                                         data_tier, 
                                                         ubproject, ubstage, ubversion)
                            print 'Submitted batch job %s' % jobid
                            print 'Sam project %s' % prjname

                            # Update status in the merged_tables database table.
                            # This is where we store the output file name.
                            # We also store the project name and the jobid.
                            # In principle, the project name is chosen by project.py,
                            # but we know that project.py uses the sam default project name.

                            submit_time = datetime.datetime.strftime(datetime.datetime.now(), 
                                                                     '%Y-%m-%d %H:%M:%S')
                            q = '''UPDATE merged_files
                                   SET name=?,jobid=?,submit_time=?,sam_project=?,status=?
                                   WHERE id=?;'''
                            c.execute(q, (output_name, jobid, submit_time, prjname, 2, merge_id))
                            self.conn.commit()

        # Done

        return


    # Submit batch job to merge files in sam dataset.
    # Returns a 2-tuple of (batch job id, sam project name).

    def submit(self, defname, file_type, run_type, data_tier, ubproject, ubstage, ubversion):

        jobid = None
        sam_project = None

        # Update project and stage objects.

        self.probj.name = ubproject
        self.probj.version = ubversion
        self.probj.file_type = file_type
        self.probj.run_type = run_type

        self.stobj.name = ubstage
        self.stobj.inputdef = defname
        self.stobj.data_tier = data_tier

        self.stobj.prestart = 1
        self.stobj.num_events = 1000000000
        self.stobj.num_jobs = 1

        # Submit job.

        try:
            real_stdout = sys.stdout
            real_stderr = sys.stderr
            sys.stdout = StringIO.StringIO()
            sys.stderr = StringIO.StringIO()

            # Submit jobs.

            jobid = project.dosubmit(self.probj, self.stobj, recur=True)
            strout = sys.stdout.getvalue()
            strerr = sys.stderr.getvalue()
            sys.stdout = real_stdout
            sys.stderr = real_stderr

            # Parse output to extract sam project.

            for line in strout.splitlines():
                print line
                if line.startswith('Starting project'):
                    words = line.split()
                    if len(words) >= 3:
                        sam_project = words[2]
                        if sam_project[-1] == '.':
                            sam_project = sam_project[:-1]    # Remove trailing period.

        except:
            jobid = None
            sam_project = None
            sys.stdout = real_stdout
            sys.stderr = real_stderr
            print 'Exception raised by project.dosubmit:'
            e = sys.exc_info()
            for item in e:
                print item
            for line in traceback.format_tb(e[2]):
                print line

        # Done.

        return jobid, sam_project


    # Return the number of status 0 files in the database.

    def nstat0(self):
        c = self.conn.cursor()
        q = 'SELECT count(*) FROM merged_files WHERE status=0'
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
        print 'Quitting because similar process is already running.'
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
        else:
            print 'Unknown option %s' % args[0]
            return 1

    # Create merge engine.

    engine = MergeEngine(xmlfile, projectname, stagename, defname,
                         database, max_size, min_size, max_age)
    n0 = engine.nstat0()
    if n0 == 0:
        engine.update_unmerged_files()
        engine.update_merges()
    engine.update_status()

    # Done.

    print '\nFinished.'
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
