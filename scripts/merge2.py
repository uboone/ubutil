#! /usr/bin/env python
######################################################################
#
# Name: merge2.py
#
# Purpose: Production merge engine.
#
# Created: 24-Oct-2019  Herbert Greenlee
#
# Usage:
#
# merge2.py <options>
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
# --max_projects <n>  - Maximum number of projects.
# --max_groups <n>    - Maximum number of new merge groups to add.   
# --query_limit <n>   - Maximum number of files to query from sam.
# --phase1            - Phase 1 (scan unmerged files).
# --phase2            - Phase 2 (submit & monitor projects).
# --phase3            - Phase 3 (monitor and clean up merged files).
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
#     This script uses module project.py to parse the xml file, but interaction with
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
# the following four tables.
#
# I.  Table unmerged_files
#
#     A. File id (integer, primary key).
#     B. File name (text).
#     C. Merge group id (integar, foreign key).  Many-to-one relation.
#     D. Sam project id (integer, foreigh key).  Many-to-one relation.
#     E. Sam Process id (integer, foreign key).  Many-to-one relation.
#     F. File size in bytes (integer).
#     G. Creation data (text).
#
# II. Table merge_group.
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
# III. Table sam_projects.
#
#    A. Sam project id (integer, primary key).
#    B. Sam project name (text).
#    C. Sam dataset definition (text).
#    D. Merge group id (integer, foreigh key).  Many-to-one relation.
#    E. Batch cluster id (text).
#    F. Submit time (text).
#    G. Sam project status (integer).
#       0 - Not started.
#       1 - Started.
#       2 - Ended.
#       3 - Finished.
#
# II.  Table sam_processes.
#
#    A. Sam process id (integer, primary key).
#    B. Sam project id (integer, foreign key).
#    C. Merged file name (text).
#    D. Process status (integer).  Statuses as follows:
#       0 - Not declared.
#       1 - Declared.
#       2 - Located.
#       3 - Finished.
#       4 - Error.
#
######################################################################

import sys, os, datetime, uuid, traceback, tempfile, subprocess
import threading, Queue
import StringIO
import project, project_utilities, larbatch_posix
import sqlite3


def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0

    for line in file.readlines():
        if line[2:11] == 'merge2.py':
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
                 database, max_size, min_size, max_age, 
                 max_projects, max_groups, query_limit):

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
        self.max_projects = max_projects  # Maximum number of sam projects.
        self.max_groups = max_groups      # Maximum number of new merges groups per invocation.
        self.query_limit = query_limit    # Maximum number of files to query from sam.

        # Cache of directory contents.

        self.dircache = {}

        # Unmerged file add queue.

        self.add_queue = []
        self.add_queue_max = 10   # Maximum size of add queue.

        # Metadata queue.

        self.metadata_queue = []
        self.metadata_queue_max = 10   # Maximum size of metadata queue.

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
CREATE TABLE IF NOT EXISTS sam_projects (
  id integer PRIMARY KEY,
  name text,
  defname text,
  group_id integer,
  cluster_id text,
  submit_time text,
  num_jobs integer,
  max_files_per_job integer,
  status integer,
  FOREIGN KEY (group_id) REFERENCES merge_groups (id)
);'''
        c.execute(q)

        q = '''
CREATE TABLE IF NOT EXISTS sam_processes (
  id integer PRIMARY KEY,
  sam_process_id integer NOT NULL,
  sam_project_id integer NOT NULL,
  merged_file_name text NOT NULL,
  status integer,
  FOREIGN KEY (sam_project_id) REFERENCES sam_projects (id)
);'''
        c.execute(q)

        q = '''
CREATE TABLE IF NOT EXISTS unmerged_files (
  id integer PRIMARY KEY,
  name text NOT NULL,
  group_id integer,
  sam_project_id integer,
  sam_process_id integer,
  size integer,
  create_date text,
  FOREIGN KEY (group_id) REFERENCES merge_groups (id),
  FOREIGN KEY (sam_project_id) REFERENCES sam_projects (id),
  FOREIGN KEY (sam_process_id) REFERENCES sam_processes (id)
);'''
        c.execute(q)

        # Done

        return conn


    # Flush metadata queue.

    def flush_metadata(self):

        if len(self.metadata_queue) > 0:
            for md in self.metadata_queue:
                print 'Updating metadata for file %s' % md['file_name']
            self.samweb.modifyMetadata(self.metadata_queue)
            self.metadata_queue = []

        # Done.

        return


    # Delayed bulk modify metadata function.

    def modifyFileMetadata(self, f, md):

        # Add file name to metadata.

        md['file_name'] = f

        # Add metadata to queue.

        self.metadata_queue.append(md)

        # Maybe flush queue.

        if len(self.metadata_queue) >= self.metadata_queue_max:
            self.flush_metadata()

        # Done.

        return


    # Optimized file existence checker.
    # Directory contents are cached.

    def exists(self, fp):

        result = False

        npath = os.path.normpath(fp)
        dir = os.path.dirname(npath)
        base = os.path.basename(npath)
        if dir == '':
            dir = '.'
        if not self.dircache.has_key(dir):
            self.dircache[dir] = set(larbatch_posix.listdir(dir))
        if base in self.dircache[dir]:
            result = True
        return result


    # Function to return dimension corresponding to group id.

    def get_group_dim(self, group_id):

        c = self.conn.cursor()
        q = '''SELECT file_type, file_format, data_tier, data_stream,
               project, stage, version, run
               FROM merge_groups WHERE id=?'''
        c.execute(q, (group_id,))
        row = c.fetchone()
        dim = '''file_type %s and file_format %s and data_tier %s and data_stream %s
                 and ub_project.name %s and ub_project.stage %s and ub_project.version %s
                 and run_number %d
                 and merge.merge 1 and merge.merged 0''' % row
        return dim


    # This function queries mergeable files from sam and updates the unmerged_tables table.

    def update_unmerged_files(self):

        if self.query_limit == 0 or self.max_groups == 0:
            return

        print 'Querying unmerged files from sam.'
        extra_clause = ''
        if self.defname != '':
            extra_clause = 'and defname: %s' % self.defname
        dim = 'merge.merge 1 and merge.merged 0 %s with availability physical with limit %d' % (
            extra_clause, self.query_limit)
        files = self.samweb.listFiles(dim)
        print '%d unmerged files.' % len(files)
        print 'Updating unmerged_files table in database.'

        nadd = 0
        for f in files:
            ok = self.add_unmerged_file(f)
            if ok:
                nadd += 1
                if nadd >= self.max_groups:
                    break

        # Done.

        return


    # Check disk locations of file.  All location checks are done in this function.
    # Return value is 2-tuple: (on_disk, on_tape).
    # If file has a tape locations, delete file from fisk and 
    # remove all disk locations from sam.
    # Disk locations are checked for validity.
    # If disk location does not exist, remove disk location from sam.
    # Tape locations are not checked.

    def check_location(self, f, do_check_disk):

        print 'Checking location of file %s' % f
        on_disk = False
        on_tape = False

        # Get location(s).

        locs = self.samweb.locateFile(f)

        # First see if file is on tape.

        for loc in locs:
            if loc['location_type'] == 'tape':
                on_tape = True

        if on_tape:

            print 'File is on tape.'

            # File is on tape
            # Delete and remove any disk locations from sam.

            for loc in locs:
                if loc['location_type'] == 'disk':

                    # Delete unmerged file from disk.

                    dir = os.path.join(loc['mount_point'], loc['subdir'])
                    fp = os.path.join(dir, f)
                    print 'Deleting file from disk.'
                    if self.exists(fp):
                        larbatch_posix.remove(fp)
                    print 'Removing disk location from sam.'
                    self.samweb.removeFileLocation(f, loc['full_path'])

        else:

            # File is not on tape.
            # Check disk locations, if requested to do so.

            if do_check_disk:

                print 'Checking disk locations.'
                for loc in locs:
                    if loc['location_type'] == 'disk':
                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                        fp = os.path.join(dir, f)
                        if self.exists(fp):
                            print 'Location OK.'
                        on_disk = True
                    else:
                        print 'Removing bad location from sam.'
                        self.samweb.removeFileLocation(f, loc['full_path'])

        # Done

        return (on_disk, on_tape)


    # Delete desk locations for this file.

    def delete_disk_locations(self, f):

        print 'Deleting disk locations for file %s' % f

        # Get location(s).

        locs = self.samweb.locateFile(f)
        for loc in locs:
            if loc['location_type'] == 'disk':

                # Delete unmerged file from disk.

                dir = os.path.join(loc['mount_point'], loc['subdir'])
                fp = os.path.join(dir, f)
                print 'Deleting file from disk.'
                if self.exists(fp):
                    larbatch_posix.remove(fp)
                print 'Removing disk location from sam.'
                self.samweb.removeFileLocation(f, loc['full_path'])

        # Done

        return


    # Process all files in the add queue.

    def flush_add_queue(self):

        if len(self.add_queue) == 0:
            return

        # Get metadata of all files in add queue.

        mds = self.samweb.getMultipleMetadata(self.add_queue)

        # Get locations of all files in add queue.

        locdict = self.samweb.locateFiles(self.add_queue)

        # Loop over files.

        c = self.conn.cursor()
        for md in mds:

            f = md['file_name']
            print 'Checking unmerged file %s' % f
            locs = locdict[f]

            # See if this file is on tape already.

            on_tape = False
            on_disk = False
            for loc in locs:
                if loc['location_type'] == 'tape':
                    on_tape = True

            if on_tape:

                print 'File is already on tape.'

                # File is on tape
                # Modify metadata to set merge.merged flag to be true, so that this
                # file will no longer be considered for merging.

                mdmod = {'merge.merged': 1}
                print 'Updating metadata to set merged flag.'
                self.modifyFileMetadata(f, mdmod)

                # Delete and remove any disk locations from sam.
                # This shouldn't ever really happen.

                for loc in locs:
                    if loc['location_type'] == 'disk':

                        # Delete unmerged file from disk.

                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                        fp = os.path.join(dir, f)
                        print 'Deleting file from disk.'
                        if self.exists(fp):
                            larbatch_posix.remove(fp)
                        print 'Removing disk location from sam.'
                        self.samweb.removeFileLocation(f, loc['full_path'])

            else:

                # File is not on tape.
                # Check disk locations.

                print 'Checking disk locations.'
                for loc in locs:
                    if loc['location_type'] == 'disk':
                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                        fp = os.path.join(dir, f)
                        if self.exists(fp):
                            print 'Location OK.'
                        on_disk = True
                    else:
                        print 'Removing bad location from sam.'
                        self.samweb.removeFileLocation(f, loc['full_path'])

            

            if on_disk:

                # File has valid disk location.

                print 'Adding unmerged file %s' % f
                group_id = self.merge_group(md)
                size = md['file_size']
                sam_project_id = 0
                sam_process_id = 0
                create_date = md['create_date']
                q = '''INSERT INTO unmerged_files
                       (name, group_id, sam_project_id, sam_process_id,
                       size, create_date)
                       VALUES(?,?,?,?,?,?);'''
                c.execute(q, (f, group_id, sam_project_id, sam_process_id, size,
                              create_date))
                self.conn.commit()

            else:

                # No valid location.

                print 'File does not have a valid location.'

        # Done.

        self.add_queue = []
        self.flush_metadata()
        return


    # Function to bulk-add a collection of unmerged files to unmerged_files table.
    # Return True if files were added.

    def add_unmerged_files(self, flist):

        # Loop over files in list to determine which ones need to be added.

        add_files = []
        c = self.conn.cursor()
        for f in flist:

            # Query database to see if this file already exists.

            q = 'SELECT id FROM unmerged_files WHERE name=?'
            c.execute(q, (f,))
            rows = c.fetchall()
            if len(rows) == 0:
                print 'Adding %s' % f
                add_files.append(f)
            else:
                print 'Ignoring %s' % f

        # Loop over files in add list and do bulk adds.

        for f in add_files:            
            self.add_queue.append(f)
            if len(self.add_queue) >= self.add_queue_max:
                self.flush_add_queue()
        if len(self.add_queue) > 0:
            self.flush_add_queue()

        # Done.

        return


    # Add example file and group partners to database.

    def add_unmerged_file(self, f):

        result = False
        print 'Checking example file %s' % f

        # Query database to see if this file already exists.

        c = self.conn.cursor()
        q = 'SELECT id FROM unmerged_files WHERE name=?'
        c.execute(q, (f,))
        rows = c.fetchall()

        if len(rows) == 0:

            print 'Adding example unmerged file %s' % f

            # Add this file and group partners.

            md = self.samweb.getMetadata(f)
            group_id = self.merge_group(md)
            dim = self.get_group_dim(group_id)
            group_files = self.samweb.listFiles(dim)
            self.add_unmerged_files(group_files)
            result = True

        else:

            print 'File is already in database.'

        # Done.

        return result


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
        q = '''SELECT id FROM merge_groups WHERE
               file_type=?
               and file_format=?
               and data_tier=?
               and data_stream=?
               and project=?
               and stage=?
               and version=?
               and run=?'''
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
            self.conn.commit()

        else:

            group_id = rows[0][0]

        # Done

        return group_id


    # Function to update sam projects by assigning currently unaffiliated unmerged files
    # to sam projects.

    def update_sam_projects(self):

        # Loop over merge groups with unassigned files.

        c = self.conn.cursor()
        q = '''SELECT DISTINCT group_id FROM unmerged_files
               WHERE sam_project_id=0 AND sam_process_id=0 ORDER BY group_id;'''
        c.execute(q)
        rows = c.fetchall()
        for row in rows:

            group_id = row[0]
            print 'Checking merge group %d.' % group_id

            # Check the number of sam projects.

            q = 'SELECT COUNT(*) FROM sam_projects WHERE status<2;'
            c.execute(q)
            mrow = c.fetchone()
            nprj = mrow[0]
            print '%d sam projects.' % nprj
            if nprj >= self.max_projects:

                print 'Quitting because number of projects is at the maximum.'
                break


            # Query unassigned files in this merge group.
            # Track the total size and oldest file in this merge group.

            file_ids = []
            total_size = 0
            nfiles = 0
            oldest_create_date = ''
            dim = ''

            q = '''SELECT id, name, size, create_date FROM unmerged_files
                   WHERE group_id=? and sam_project_id=? ORDER BY create_date;'''
            c.execute(q, (group_id, 0))
            newrows = c.fetchall()
            for newrow in newrows:
                id = newrow[0]
                name = newrow[1]
                size = newrow[2]
                create_date = newrow[3]

                file_ids.append(id)
                total_size += size
                nfiles += 1
                if oldest_create_date == '':
                    oldest_create_date = create_date
                if dim == '':
                    dim = 'file_name %s' % name
                else:
                    dim += ',%s' % name

            # See if this merge group meets the criteria for starting a sam project,
            # which is size greater than minimu size or oldest create data older
            # than minimum age.
            # Calculate age of oldest unmerged file.

            create_project = False
            print 'Checking merge group.'
            print 'Total size = %d' % total_size
            print 'Oldest create date = %s' % oldest_create_date

            if total_size >= self.min_size:

                print 'Create sam project because total size is greater than minimum size.'
                create_project = True

            if not create_project:
                t = datetime.datetime.strptime(oldest_create_date, '%Y-%m-%dT%H:%M:%S+00:00')
                now = datetime.datetime.utcnow()
                dt = now - t
                if dt.total_seconds() > self.max_age:
                    print 'Create sam project because oldest file is older than maximum age.'
                    create_project = True

            if create_project:

                # Create sam dataset definition.

                defname = 'merge_%s' % uuid.uuid4()
                print 'Creating dataset definition %s' % defname
                self.samweb.createDefinition(defname, dim,
                                             user=project_utilities.get_user(), 
                                             group=project_utilities.get_experiment())


                # Calculate number of batch jobs and maximum files per job

                num_jobs = (total_size - 1) / self.max_size + 1
                if num_jobs > nfiles:
                    num_jobs = nfiles
                max_files_per_job = (nfiles - 1) / num_jobs + 1
                print 'Number of files = %d' % nfiles
                print 'Number of batch jobs = %d' % num_jobs
                print 'Maximum files per job = %d' % max_files_per_job

                # Insert a new row into sam_projects table.

                q = '''INSERT INTO sam_projects
                       (name, defname, group_id, cluster_id, submit_time,
                        num_jobs, max_files_per_job, status)
                        VALUES(?,?,?,?,?,?,?,?);'''
                c.execute(q, ('', defname, group_id, '', '',
                              num_jobs, max_files_per_job, 0))
                sam_project_id = c.lastrowid

                # Update unmerged files table.

                q = 'UPDATE unmerged_files SET sam_project_id=? WHERE group_id=?;'
                c.execute(q, (sam_project_id, group_id))
                self.conn.commit()


    # Function to determine whether to end a project.

    def should_stop_project(self, prjstat):

        result = False

        # Check the project start time.

        if prjstat.has_key('project_start_time'):
            startstr = prjstat['project_start_time']
            print 'Project start time = %s' % startstr
            t = datetime.datetime.fromtimestamp(0)
            try:
                t = datetime.datetime.strptime(startstr, '%Y-%m-%dT%H:%M:%S.%f+00:00')
            except:
                print 'Malformed time stamp.'
                t = datetime.datetime.fromtimestamp(0)
            now = datetime.datetime.utcnow()
            dt = now - t
            dtsec = dt.total_seconds()
            print 'Project age = %d seconds' % dtsec

            # If start time is older than 24 hours, stop this project.

            if dtsec > 24*3600:
                result = True

        else:

            # Project status is malformed.
            # Stop project.

            result = True

        # Done

        return result


    # Update statuses of sam projects.
    # This function may start projects and submit batch jobs.

    def update_sam_project_status(self):

        # In this function, we make a double loop over sam projects and statuses.

        c = self.conn.cursor()

        # First loop over statuses in reverse order.

        for status in range(3, -1, -1):

            # Query and loop over sam projects with this status.

            q = '''SELECT name, id, defname, num_jobs, max_files_per_job
                   FROM sam_projects WHERE status=? ORDER BY id;'''
            c.execute(q, (status,))
            rows = c.fetchall()
            for row in rows:
                sam_project = row[0]
                sam_project_id = row[1]
                defname = row[2]
                num_jobs = row[3]
                max_files_per_job = row[4]

                print '\nStatus=%d, sam project %s' % (status, sam_project)

                if status == 3:

                    # Finished.
                    # Delete this project.

                    print 'Deleting project %s' % sam_project

                    # First validate locations of any unmerged files associated with this process.

                    q = 'SELECT name FROM unmerged_files WHERE sam_project_id=?'
                    c.execute(q, (sam_project,))
                    rows = c.fetchall()
                    if len(rows) > 0:
                        print 'Checking locations of remaining unmerged files.'
                        for row in rows:
                            f = row[0]
                            self.check_location(f, True)

                    q = 'UPDATE unmerged_files SET sam_project_id=? WHERE sam_project_id=?;'
                    c.execute(q, (0, sam_project_id))

                    q = 'UPDATE sam_processes SET sam_project_id=? WHERE sam_project_id=?;'
                    c.execute(q, (0, sam_project_id))

                    q = 'DELETE FROM sam_projects WHERE id=?'
                    c.execute(q, (sam_project_id,))

                    self.conn.commit()

                if status == 2:

                    # Project ended.

                    prjsum = self.samweb.projectSummary(sam_project)

                    # Loop over processes.

                    procs = prjsum['processes']

                    if len(procs) == 0:
                        print 'No processes.'

                    for proc in procs:
                        pid = proc['process_id']
                        print 'SAM process id = %d' % pid

                        # Query files consumed by this process.

                        consumed_files = []
                        dim = 'consumer_process_id %d and consumed_status consumed' % pid
                        files = self.samweb.listFiles(dim)
                        for f in files:
                            consumed_files.append(f)
                        print 'Number of consumed files = %d' % len(consumed_files)

                        if len(consumed_files) > 0:

                            # Determine file names produced by this process.
                            # Just look at children of first consumed file.

                            dim = '''ischildof:( file_name %s )
                                 with availability anylocation''' % consumed_files[0]
                            files = self.samweb.listFiles(dim)
                            for f in files:

                                # Need to verify process_id.

                                md = self.samweb.getMetadata(f)
                                if md.has_key('process_id'):
                                    if pid == md['process_id']:

                                        print 'Output file = %s' % f

                                        # Add line to sam_processes table.

                                        q = '''INSERT INTO sam_processes
                                               (sam_process_id, sam_project_id,
                                               merged_file_name, status)
                                               VALUES(?,?,?,?);'''
                                        c.execute(q, (pid, sam_project_id, f, 1))
                                        merge_id = c.lastrowid
                                        self.conn.commit()

                                        # Update unmerged files table.

                                        for consumed_file in consumed_files:
                                            print 'Unmerged file %s' % consumed_file

                                        # Update process id join with unmerged file.

                                        placeholders = ('?,'*len(consumed_files))[:-1]
                                        q = '''UPDATE unmerged_files SET sam_process_id=? 
                                               WHERE name IN (%s);''' % placeholders
                                        c.execute(q, (merge_id,) + tuple(consumed_files))
                                        self.conn.commit()

                    # Update project status to 3.

                    q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                    c.execute(q, (3, sam_project_id))
                    self.conn.commit()

                elif status == 1:

                    # Project running.
                    # Check status of this project.

                    prj_ended = False
                    prj_started = False
                    prjstat = {}
                    try:
                        prjstat = self.samweb.projectSummary(sam_project)
                        prj_started = True
                    except:
                        prj_started = False
                        prjstat = {}
                    if prjstat.has_key('project_end_time'):
                        endstr = prjstat['project_end_time']
                        if len(endstr) > 1:

                            # Calculate how long since the project ended.

                            t = datetime.datetime.strptime(endstr,
                                                           '%Y-%m-%dT%H:%M:%S.%f+00:00')
                            now = datetime.datetime.utcnow()
                            dt = now - t
                            dtsec = dt.total_seconds()

                            if dtsec > 600:

                                print 'Project ended: %s' % sam_project
                                prj_ended = True

                            else:

                                print 'Project cooling off (ended %d seconds ago): %s' % (
                                    dtsec, sam_project)

                    if prj_ended:

                        # Update project status to 2.

                        q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                        c.execute(q, (2, sam_project_id))
                        self.conn.commit()

                    elif prj_started and prjstat.has_key('project_status') and \
                         prjstat['project_status'] == 'reserved':

                        # Project is in an unkillable state.
                        # Just forget about this project.

                        print 'Forgetting about this project.'
                        q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                        c.execute(q, (2, sam_project_id))
                        self.conn.commit()

                    elif prj_started:

                        # Project has started, but has not ended.

                        print 'Project %s has started, but has not yet ended.' % sam_project

                        # Figure out if we should stop this project.

                        stop_project = self.should_stop_project(prjstat)

                        if stop_project:
                            print 'Stop project %s' % sam_project
                            stop_ok = False
                            try:
                                self.samweb.stopProject(sam_project)
                                stop_ok = True
                            except:
                                print 'Unable to stop project.'
                                stop_ok = False

                            # If we failed to stop this project, assume that it is dead
                            # and advance the status to 2.

                            print 'Forgetting about this project.'
                            q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                            c.execute(q, (2, sam_project_id))
                            self.conn.commit()


                    else:

                        # Project has not started.

                        print 'Project %s has not started.' % sam_project

                        # Check submit time.

                        q = '''SELECT submit_time FROM sam_projects WHERE id=?'''
                        c.execute(q, (sam_project_id,))
                        row = c.fetchone()
                        stime_str = row[0]
                        stime = datetime.datetime.strptime(stime_str, '%Y-%m-%d %H:%M:%S')
                        print 'Submit time = %s' % stime_str

                        now = datetime.datetime.now()
                        now_str = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
                        print 'Current time = %s' % now_str

                        dt = now - stime
                        print 'Project age = %s' % dt

                        if dt.total_seconds() > 24*3600:

                            # If project age is greater than 24 hours, start and then
                            # immediately stop this project, so that no batch job can
                            # start it later.
                            # A subsequent invocation of this script will handle
                            # the ended project.

                            print 'Start project %s' % sam_project
                            self.samweb.startProject(sam_project,
                                                     defname=defname, 
                                                     station=project_utilities.get_experiment(),
                                                     group=project_utilities.get_experiment(),
                                                     user=project_utilities.get_user())

                            print 'Stop project %s' % sam_project
                            self.samweb.stopProject(sam_project)


                elif status == 0:

                    # Project not started.
                    # Submit batch jobs.
                    # Submit function will update project status to 1 if 
                    # batch submission is successful.

                    self.submit(sam_project_id)


    # Function to start sam project and submit batch jobs.

    def submit(self, sam_project_id):

        # Query information about this sam project.

        c = self.conn.cursor()
        q = '''SELECT defname, num_jobs, max_files_per_job FROM sam_projects
               WHERE id=?;'''
        c.execute(q, (sam_project_id,))
        row = c.fetchone()
        defname = row[0]
        num_jobs = row[1]
        max_files_per_job = row[2]
        
        # Query first unmerged file associated with this sam project.

        q = 'SELECT name FROM unmerged_files WHERE sam_project_id=?'
        c.execute(q, (sam_project_id,))
        row = c.fetchone()
        unmerged_file = row[0]

        # Query sam metadata from first unmerged file.
        # We will use this to generate metadata for merged files.

        md = self.samweb.getMetadata(unmerged_file)
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

        # Generate a fcl file customized for this merged file.

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
        fcl.write('  FileCatalogMetadataMicroBooNE:\n')
        fcl.write('  {\n')
        fcl.write('    FCLName: "%s"\n' % os.path.basename(self.fclpath))
        fcl.write('    FCLVersion: "%s"\n' % app_version)
        fcl.write('    ProjectName: "%s"\n' % ubproject)
        fcl.write('    ProjectStage: "%s"\n' % ubstage)
        fcl.write('    ProjectVersion: "%s"\n' % ubversion)
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
        fcl.write('    fileName: "%ifb_%tc_merged.root"\n')
        fcl.write('    dataTier: "%s"\n' % data_tier)
        fcl.write('    streamName:  "%s"\n' % data_stream)
        fcl.write('    compressionLevel: 3\n')
        fcl.write('  }\n')
        fcl.write('}\n')
        fcl.close()


        # Generate project name and stash the name in the database.

        prjname = self.samweb.makeProjectName(defname)
        print 'Submitting batch job for project %s' % prjname

        # Start project now.

        if num_jobs > 1:
            print 'Starting sam project %s' % prjname
            self.samweb.startProject(prjname,
                                     defname=defname, 
                                     station=project_utilities.get_experiment(),
                                     group=project_utilities.get_experiment(),
                                     user=project_utilities.get_user())
        else:
            print 'Project will be started by batch job.'

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
                raise RuntimeError, 'Worker initialization script %s does not exist.\n' % \
                    self.stobj.init_script
            work_init_script = os.path.join(tmpworkdir, os.path.basename(self.stobj.init_script))
            if self.stobj.init_script != work_init_script:
                larbatch_posix.copy(self.stobj.init_script, work_init_script)

        # Copy worker initialization source script to work directory.

        if self.stobj.init_source != '':
            if not larbatch_posix.exists(self.stobj.init_source):
                raise RuntimeError, 'Worker initialization source script %s does not exist.\n' % \
                    self.stobj.init_source
            work_init_source = os.path.join(tmpworkdir, os.path.basename(self.stobj.init_source))
            if self.stobj.init_source != work_init_source:
                larbatch_posix.copy(self.stobj.init_source, work_init_source)

        # Copy worker end-of-job script to work directory.

        if self.stobj.end_script != '':
            if not larbatch_posix.exists(self.stobj.end_script):
                raise RuntimeError, 'Worker end-of-job script %s does not exist.\n' % \
                    self.stobj.end_script
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
                print 'Helper script %s not found.' % helper

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
                print 'Helper python module %s not found.' % helper_module

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
            raise RuntimeError, 'Failed to create work tarball in %s' % tmpworkdir

        # Construct jobsub_submit command.

        command = ['jobsub_submit']

        # Add jobsub_submit boilerplate options.  Copied from project.py.

        command.append('--group=%s' % project_utilities.get_experiment())
        command.extend(['-N', '%d' % num_jobs])
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
        command.extend([' --nfile', '%d' % max_files_per_job])
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
            print 'Validation will be done on the worker node %d' % self.stobj.validate_on_worker
            command.extend([' --validate'])
            command.extend([' --declare'])
        if self.stobj.copy_to_fts == 1:
            command.extend([' --copy'])
        command.extend(['--sam_station', project_utilities.get_experiment()])
        command.extend(['--sam_group', project_utilities.get_experiment()])
        command.extend(['--sam_defname', defname])
        command.extend(['--sam_project', prjname])
        if num_jobs == 1:
            command.append('--sam_start')

        # Invoke the job submission command and capture the output.

        print 'Invoke jobsub_submit'
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
            clusid = ''
            for line in jobout.split('\n'):
                if "JobsubJobId" in line:
                    jobid = line.strip().split()[-1]
            if jobid != '':
                words = jobid.split('@')
                if len(words) == 2:
                    clus = words[0].split('.')[0]
                    server = words[1]
                    clusid = '%s@%s' % (clus, server)
                    batchok = True

        if batchok:

            # Batch job submission succeeded.

            print 'Batch job submission succeeded.'
            print 'Job id = %s' % jobid
            print 'Cluster id = %s' % clusid

            # Update sam_projects table with information about this job submission.

            submit_time = datetime.datetime.strftime(datetime.datetime.now(), 
                                                     '%Y-%m-%d %H:%M:%S')
            q = '''UPDATE sam_projects
                   SET name=?,cluster_id=?,submit_time=?,status=?
                   WHERE id=?;'''
            c.execute(q, (prjname, clusid, submit_time, 1, sam_project_id))

            # Done updating database in this function.

            self.conn.commit()

        else:

            # Batch job submission failed.

            print 'Batch job submission failed.'
            print jobout
            print joberr

            # Stop sam projects.

            for prj in sam_projects.split(':'):
                print 'Stopping sam project %s' % prj
                self.samweb.stopProject(prj)


    # Update statuses of sam processes / merged files.

    def update_sam_process_status(self):

        # In this function, we make a double loop over sam processes and statuses.

        c = self.conn.cursor()

        # First loop over statuses in reverse order.

        for status in range(4, -1, -1):

            # Query and loop over sam processes with this status.

            q = '''SELECT id, sam_process_id, merged_file_name
                   FROM sam_processes WHERE status=? ORDER BY id;'''
            c.execute(q, (status,))
            rows = c.fetchall()
            for row in rows:
                merge_id = row[0]
                sam_process_id = row[1]
                merged_file = row[2]

                print '\nStatus=%d, file name %s' % (status, merged_file)

                if status == 3:

                    # Finished.

                    # Finished.
                    # Delete this process.

                    # First validate locations of any unmerged files associated with this process.

                    q = 'SELECT name FROM unmerged_files WHERE sam_process_id=?'
                    c.execute(q, (merge_id,))
                    rows = c.fetchall()
                    if len(rows) > 0:
                        print 'Checking locations of remaining unmerged files.'
                        for row in rows:
                            f = row[0]
                            self.check_location(f, True)

                    print 'Deleting process.'

                    q = 'UPDATE unmerged_files SET sam_process_id=? WHERE sam_process_id=?;'
                    c.execute(q, (0, merge_id))

                    q = 'DELETE FROM sam_processes WHERE id=?'
                    c.execute(q, (merge_id,))

                    self.conn.commit()

                if status == 2:

                    # Located.
                    # Do cleanup for this merged file.

                    print 'Doing cleanup for merged file %s' % merged_file

                    # First query unmerged files corresponsing to this merged file.

                    unmerged_files = []
                    q = 'SELECT name FROM unmerged_files WHERE sam_process_id=?'
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
                        self.modifyFileMetadata(f, mdmod)

                        # Delete disk locations for unmerged file.

                        self.delete_disk_locations(f)

                        # Print message about deleting file from database.

                        print 'Deleting file from merge database: %s' % f

                    # Done looping over unmerged files.

                    self.flush_metadata()

                    # Construct a query to do the database deletions in a single query.

                    print 'Deleting unmerged files from database.'
                    placeholders = ('?,' * len(unmerged_files))[:-1]
                    q = 'DELETE FROM unmerged_files WHERE name IN (%s);' % placeholders
                    c.execute(q, unmerged_files)
                    self.conn.commit()

                    # End of loop over unmerged files.
                    # Cleaning done.
                    # Update status of sam process to 3

                    print 'Cleaning finished.'
                    q = '''UPDATE sam_processes SET status=? WHERE id=?;'''
                    c.execute(q, (3, merge_id))
                    self.conn.commit()
  
                if status == 1:

                    # Declared.
                    # Check whether this file has a location.

                    on_disk, on_tape = self.check_location(merged_file, False)

                    if on_tape:

                        print 'File located.'
                        q = 'UPDATE sam_processes SET status=? WHERE id=?;'
                        c.execute(q, (2, merge_id))
                        self.conn.commit()

                    else:

                        print 'File not located.'

                        # Check metadata of this file.

                        md = self.samweb.getMetadata(merged_file)

                        # Get age of this file.

                        t = datetime.datetime.strptime(md['create_date'],
                                                       '%Y-%m-%dT%H:%M:%S+00:00')
                        now = datetime.datetime.utcnow()
                        dt = now - t

                        # If this file too old, set error status.

                        if dt.total_seconds() > 3*24*3600:
                            print 'File is too old.  Set error status.'
                            q = '''UPDATE sam_processes SET status=? WHERE id=?;'''
                            c.execute(q, (4, merge_id))
                            self.conn.commit()

                if status == 0:

                    # Not declared (shouldn't happen).

                    pass

    # Function to remove unused merged groups from database.

    def clean_merge_groups(self):

        print '\nCleaning merge groups.'

        # Loop over merge groups.

        c = self.conn.cursor()
        q = 'SELECT id FROM merge_groups ORDER BY id;'
        c.execute(q)
        rows = c.fetchall()
        for row in rows:
            group_id = row[0]

            # Check whether any unmerged files belong to this merge group.

            q = 'SELECT COUNT(*) FROM unmerged_files WHERE group_id=?;'
            c.execute(q, (group_id,))
            row = c.fetchone()
            n = row[0]
            if n == 0:
                print 'Deleting group %d' % group_id

                q = 'DELETE FROM merge_groups WHERE id=?'
                c.execute(q, (group_id,))

        # Done.

        self.conn.commit()
        return


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
                    if len(words) > 0 and words[0].endswith('merge2.py'):
                        result = 1
                    if len(words) > 1 and \
                       words[0].endswith('python') and words[1].endswith('merge2.py'):
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
    max_projects = 500
    max_groups = 100
    query_limit = 10000
    do_phase1 = False
    do_phase2 = False
    do_phase3 = False

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
        elif args[0] == '--max_projects' and len(args) > 1:
            max_projects = int(args[1])
            del args[0:2]
        elif args[0] == '--max_groups' and len(args) > 1:
            max_groups = int(args[1])
            del args[0:2]
        elif args[0] == '--query_limit' and len(args) > 1:
            query_limit = int(args[1])
            del args[0:2]
        elif args[0] == '--phase1':
            do_phase1 = True
            del args[0]
        elif args[0] == '--phase2':
            do_phase2 = True
            del args[0]
        elif args[0] == '--phase3':
            do_phase3 = True
            del args[0]
        else:
            print 'Unknown option %s' % args[0]
            return 1

    # If no phase option, do all three phases.

    if not do_phase1 and not do_phase2 and not do_phase3:
        do_phase1 = True
        do_phase2 = True
        do_phase3 = True

    # Create merge engine.

    engine = MergeEngine(xmlfile, projectname, stagename, defname,
                         database, max_size, min_size, max_age,
                         max_projects, max_groups, query_limit)
    if do_phase1:
        engine.update_unmerged_files()
    if do_phase2:
        engine.update_sam_projects()
        engine.update_sam_project_status()
    if do_phase3:
        engine.update_sam_process_status()
        engine.clean_merge_groups()

    # Done.

    print '\nFinished.'
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
