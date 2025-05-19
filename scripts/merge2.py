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
# --logdir <dir>      - Specify directory to store log files.
#                       If specified each invocation generates a unique set of log files.
#                       If not specified, output to stdout and stderr (no log files).
# --max_size <bytes>  - Maximum merged file size in bytes (default 2.5e9).
# --min_size <bytes>  - Minimum merged file size in bytes (default 1e9).
# --max_count <n>     - Maximum number of files to merge per merged file (default no limit).
# --max_age <seconds> - Maximum unmerged file age in seconds (default 72 hours).
#                       Optionally use suffix 'h' for hours, 'd' for days.
# --max_projects <n>  - Maximum number of projects.
# --max_groups <n>    - Maximum number of new merge groups to add.   
# --query_limit <n>   - Maximum number of files to query from sam.
# --file_limit <n>    - Maximum number of unmerged files in database.
# --group_runs <n>    - Allow merging accross runs within groups of <n> runs.
# --phase1            - Phase 1 (scan unmerged files).
# --phase2            - Phase 2 (submit & monitor projects).
# --phase3            - Phase 3 (monitor and clean up merged files).
# --nobatch           - Inform the script that no merging batch jobs are
#                       running or pending.  This sets various timeouts
#                       related to sam projects to zero.
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
#    I. Run number or run group (integer).
#    J. Application family (text).
#    K. Application name (text).
#    L. Fcl name (text).
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
# IV.  Table sam_processes.
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
# V.  Table run_groups.
#
#     A.  Run number (integer, primary key).
#     B.  Run group id (integer).
#     C.  Epoch (text).
#     D.  Quality (text).
#
#
#
# About merging within and accross runs:
#
# Files are merged if they belong to the same merge group.  Files are assigned to the
# same merge group if they have compatible metadata values.  Currently 11 metadata values
# are checked for compatibility.  All 11 metadata values must agree exactly.  The 11 
# values are the seven cardinal metadata, plus fcl name, application family, application
# name, and run number (or run group).
#
# By default, files are not merged accross runs.  This is to allow selection of merged
# files by run number at the sam level.  If command line option --group_runs is specified,
# merging accros runs is allowed within run groups.
#
# Run groups are defined by table run_groups.  Run groups consist of collections of nearby
# runs, all belonging to the same epoch, and all having the same data quality (good or bad).
# New run groups are created as new run numbers are encountered.
#
# Epochs are continuous run ranges, which are hard-wired in this script.  For reference,
# the 18 epochs are the 18 letter epochs listed on this web page:
#
# https://microboone-exp.fnal.gov/at_work/AnalysisTools/data/ub_datasets_optfilter.html
#
# Also refer to this web page:
#
# https://cdcvs.fnal.gov/redmine/projects/uboonecode/wiki/Prodhistory
#
# Run quality is defined as good or bad.  For reference, good and bad runs are defined
# using the "hardcoded" sam dataset definitions on the following web page:
#
# https://cdcvs.fnal.gov/redmine/projects/uboone-physics-analysis/wiki/MCC9_Good_Runs_Lists
#
# Each run group is identified by a run group id, which is a smallish positive integer.
# In the case of run groups, table merge_groups holds the negative of the run group id in
# the run column to signal that this merge group corresponds to a run group rather than a
# single run.
#
# Run group 0 is a special run group id that signals that a particular file was not able 
# to be assigned to either a single run or a run group, possibly because the sam metadata 
# of the file being merged contains multiple incompatible run numbers.
#
######################################################################

from __future__ import print_function
import sys, os, time, datetime, uuid, traceback, tempfile, subprocess, random
import threading
try:
    import queue as Queue
except ImportError:
    import Queue
import project, project_utilities, larbatch_posix
from larbatch_utilities import convert_str
from larbatch_utilities import convert_bytes
import sqlite3

# Global variables.

using_jobsub_lite = None
worktarname = None


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
                print(line[2:].rstrip())
            else:
                print()


# SubmitStruct is a struct-like class containing information about batch job submissions.
# Each instance of this class represents a started jobsub_submit subprocess.

class SubmitStruct:

    # Constructor.

    def __init__(self, start_time, jobinfo, tmpdirs, sam_project_id, prjname, prj_started, command):

        self.start_time = start_time           # Process start time (time.time()).
        self.jobinfo = jobinfo                 # subprocess.Popen object.
        self.tmpdirs = tmpdirs                 # Temporary directories.
        self.sam_project_id = sam_project_id   # Sqlite sam project id.
        self.prjname = prjname                 # Sam project name.
        self.prj_started = prj_started         # Number of jobs in batch cluster.
        self.command = command                 # Batch submit command.


class MergeEngine:

    # Constructor.

    def __init__(self, xmlfile, projectname, stagename, defname,
                 database, max_size, min_size, max_count, max_age, 
                 max_projects, max_groups, query_limit, file_limit,
                 group_runs, nobatch):

        # Open database connection.

        print('Opening database.')
        self.conn = self.open_database(database)

        # Create samweb object.

        self.samweb = project_utilities.samweb()

        # Extract project and stage objects from xml file (if specified).

        self.probj = None
        self.stobj = None
        self.fclpath = None
        self.numjobs = 0

        # Statistics.

        self.total_unmerged_files_added = 0
        self.total_unmerged_files_deleted = 0
        self.total_sam_projects_added = 0
        self.total_sam_projects_deleted = 0
        self.total_sam_projects_started = 0
        self.total_sam_projects_ended = 0
        self.total_sam_projects_noprocs = 0
        self.total_sam_projects_killed = 0
        self.total_sam_processes = 0
        self.total_sam_processes_succeeded = 0
        self.total_sam_processes_failed = 0
        
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

            # Randomize the fcl name by appending a uuid.

            dir = os.path.dirname(self.fclpath)
            base = os.path.splitext(os.path.basename(self.fclpath))
            self.fclpath = '%s/%s_%s%s' % (dir, base[0], uuid.uuid4(), base[1])

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
        self.max_count = max_count # Maximum number of files to merge per merged file.
        self.max_age = max_age     # Maximum unmerged file age in seconds.
        self.max_projects = max_projects  # Maximum number of sam projects.
        self.max_groups = max_groups      # Maximum number of new merges groups per invocation.
        self.query_limit = query_limit    # Maximum number of files to query from sam.
        self.file_limit = file_limit      # Maximum number of unmerged files.
        self.group_runs = group_runs      # Group runs multiplicity / flag.
        self.nobatch = nobatch     # Flag indicating that no batch jobs are pending.

        # Cache of directory contents.

        self.dircache = {}

        # Run epochs.

        self.epochs = {'A':  (3420, 3984),     # Run 1a open trigger 2 FEM.
                       'B':  (3985, 4951),     # Run 1b open trigger 3 FEM.
                       'C1': (4952, 6998),     # Run 1c normal software trigger.
                       'C2': (6999, 8316),     # Run 1 shutdown.
                       'D1': (8317, 8405),     # Run 2 open trigger.
                       'D2': (8406, 11048),    # Run 2a before CRT.
                       'E1': (11049, 11951),   # Run 2b after CRT.
                       'E2': (11952, 13696),   # Run 2 shutdown.
                       'F':  (13697, 14116),   # Run 3a before CRT clock fix.
                       'G1': (14117, 17566),   # Run 3b after CRT clock fix.
                       'G2': (17567, 18960),   # Run 3 shutdown.
                       'H':  (18961, 19752),   # Run 4a
                       'I':  (19753, 21285),   # Run 4b
                       'J':  (21286, 22269),   # Run 4c
                       'K':  (22270, 23259),   # Run 4d
                       'L':  (23260, 23542),   # Run 4 shutdown 1
                       'M':  (23543, 24319),   # Run 4 shutdown 2
                       'N':  (24320, 25769),   # Run 5
                       'O':  (25770, 1000000)} # Run 6

        # Good runs.

        self.good_runs = set()
        self.good_run_datasets = ['goodruns_mcc9_run1_open_trigger_hardcoded',
                                  'goodruns_mcc9_run1_hardcoded',
                                  'goodruns_mcc9_run2_hardcoded',
                                  'goodruns_mcc9_run3_hardcoded',
                                  'goodruns_mcc9_run4_hardcoded',
                                  'goodruns_mcc9_run5_hardcoded']

        # Populate good run list.

        print('Populating good run list.')
        for ds in self.good_run_datasets:
            print('Checking dataset %s' % ds)
            start_num = len(self.good_runs)
            result = self.samweb.descDefinitionDict(ds)
            dim = result['dimensions']
            go = False
            for comma_words in dim.split(','):
                for word in comma_words.split():
                    if word == 'run_number':
                        go = True
                    elif go:
                        run = int(word)
                        if not run in self.good_runs:
                            self.good_runs.add(run)
            print('%d good runs' % (len(self.good_runs) - start_num))
        print('Total good runs = %d' % len(self.good_runs))
                    
        # Unmerged file add queue.

        self.add_queue = []
        self.add_queue_max = 10   # Maximum size of add queue.

        # Metadata queue.

        self.metadata_queue = []
        self.metadata_queue_max = 10   # Maximum size of metadata queue.

        # Submit process queue.

        self.submit_queue = set()         # Contains SubmitStruct objects.
        self.submit_queue_max = 20        # Maximum size of submit process queue.
        self.submit_queue_timeout = 600   # Seconds.
        self.submit_max_rate = 10.        # Maximum submit rate (submits / second).
        self.submit_start_time = 0.       # Time of first submission.
        self.submit_num_submit = 0        # Number of submissions.

        # Delete project queue.

        self.delete_project_queue = []
        self.delete_project_queue_max = 100   # Maximum size of delete project queue.

        # Delete process queue.

        self.delete_process_queue = []
        self.delete_process_queue_max = 100   # Maximum size of delete process queue.

        # Delete merge group queue.

        self.delete_merge_group_queue = []
        self.delete_merge_group_queue_max = 100   # Maximum size of delete merge group queue.

        # Delete unmerged files queue.

        self.delete_unmerged_queue = []
        self.delete_unmerged_queue_max = 100   # Maximum size of delete unmerged file queue.

        # Done.

        return


    # Destructor.

    def __del__(self):

        self.conn.close()


    # Open database connection.

    def open_database(self, database):

        conn = sqlite3.connect(database, 600.)

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
  run integer,
  app_family NOT NULL,
  app_name NOT NULL,
  fcl_name NOT NULL
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

        q = '''
CREATE TABLE IF NOT EXISTS run_groups (
  run integer NOT NULL PRIMARY KEY,
  run_group_id integer NOT NULL,
  epoch text,
  quality text NOT NULL
);'''
        c.execute(q)

        # Done

        conn.commit()
        return conn


    # Flush delete unmerged file queue, leaving queue empty.

    def flush_delete_unmerged_queue(self):

        if len(self.delete_unmerged_queue) > 0:

            # Delete all unmerged file names in delete queue.

            print('Flushing delete unmerged file queue.')
            print('Delete unmerged file queue has %d members.' % len(self.delete_unmerged_queue))

            c = self.conn.cursor()
            placeholders = ('?,'*len(self.delete_unmerged_queue))[:-1]
            q = 'DELETE FROM unmerged_files WHERE name IN (%s)' % placeholders
            c.execute(q, self.delete_unmerged_queue)

            self.conn.commit()
            self.total_unmerged_files_deleted += len(self.delete_unmerged_queue)

            # Clear delete queue.

            self.delete_unmerged_queue = []
            print('Done flushing delete unmerged file queue.')

        # Done

        return


    # Deferred delete unmerged file from unmerged_files table.

    def delete_unmerged_file(self, f):
        self.delete_unmerged_queue.append(f)
        if len(self.delete_unmerged_queue) >= self.delete_unmerged_queue_max:
            self.flush_delete_unmerged_queue()
        return


    # Flush metadata queue.

    def flush_metadata(self):

        if len(self.metadata_queue) > 0:
            for md in self.metadata_queue:
                print('Updating metadata for file %s' % md['file_name'])
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
        if dir not in self.dircache:
            self.dircache[dir] = set()
            try:
                self.dircache[dir] = set(larbatch_posix.listdir(dir))
            except:
                self.dircache[dir] = set()
        if base in self.dircache[dir]:
            result = True
        return result


    # Remove file from disk and from directory cache.

    def remove(self, fp):

        # Test whether file exists.
        # If test is positive, this will also ensure that file is in directory cache.

        if self.exists(fp):

            npath = os.path.normpath(fp)
            dir = os.path.dirname(npath)
            base = os.path.basename(npath)
            if dir == '':
                dir = '.'

            # Remove file from disk.

            try:
                larbatch_posix.remove(npath)
            except:
                pass

            # Remove file from directory cache.

            self.dircache[dir].remove(base)

        return


    # Get multiple metadata function.
    # Similar as samweb.getMultipleMetadata, but no implicit maximum size.

    def get_multiple_metadata(self, file_names):
        result = []
        q = []
        print('Getting multiple metadata for %d files.' % len(file_names))

        # Loop over files.

        for f in file_names:
            #print('Getting multiple metadata for file %s' %f)
            q.append(f)

            # Maybe flush queue.

            if len(q) >= self.metadata_queue_max:
                mds = self.samweb.getMultipleMetadata(q)
                for md in mds:
                    result.append(md)
                q = []

        # Final queue flush.

        if len(q) > 0:
            mds = self.samweb.getMultipleMetadata(q)
            for md in mds:
                result.append(md)

        # Done.

        print('Got metadata for %d files.' % len(result))
        return result


    # This function queries mergeable files from sam and updates the unmerged_tables table.

    def update_unmerged_files(self):

        if self.query_limit == 0 or self.max_groups == 0:
            return

        print('Querying unmerged files from sam.')
        extra_clause = ''
        if self.defname != '':
            extra_clause = 'and defname: %s' % self.defname
        dim = 'merge.merge 1 and merge.merged 0 %s with availability physical with limit %d' % (
            extra_clause, self.query_limit)
        files = self.samweb.listFiles(dim)
        print('%d unmerged files.' % len(files))

        # Store unmerged files in a python set.

        unmerged_files = set(files)

        # Query all existing unmerged files from our database.

        c = self.conn.cursor()
        q = 'SELECT name FROM unmerged_files;'
        c.execute(q)
        rows = c.fetchall()
        self.conn.commit()

        for row in rows:
            f = row[0]
            unmerged_files.discard(f)
        print('%d unmerged files remaining after initial purge.' % len(unmerged_files))

        print('Updating unmerged_files table in database.')

        nadd = 0

        # Add files in groups of 500.

        while len(unmerged_files) > 0:
            add_list = []
            while len(unmerged_files) > 0 and len(add_list) < 500:
                add_list.append(unmerged_files.pop())
            add_files = self.add_unmerged_files(add_list)
            print('\n%d Files added.' % len(add_files))
            print('%d unmerged files remaining.' % len(unmerged_files))

            # Check number of unaffiliated unmerged files.

            q = 'select count(*) from unmerged_files where sam_process_id=0 and sam_project_id=0'
            c.execute(q)
            row = c.fetchone()
            n = row[0]
            self.conn.commit()
            print('%d unaffiliated unmerged files.' % n)
            if n > self.file_limit:
                break

        # Done.

        return


    # Check disk locations of file.  All location checks are done in this function.
    # Return value is 2-tuple: (on_disk, on_tape).
    # If file has a tape locations, delete file from disk and 
    # remove all disk locations from sam.
    # Disk locations are checked for validity.
    # If disk location does not exist, remove disk location from sam.
    # Tape locations are not checked.
    # Also check content status.  If status is not "good", remove and delete
    # disk locations.

    def check_location(self, f, do_check_disk):

        c = None

        print('Checking location of file %s' % f)
        on_disk = False
        on_tape = False

        # Get location(s).

        locs = self.samweb.locateFile(f)

        # First see if file is on tape.

        for loc in locs:
            if loc['location_type'] == 'tape' or loc['location'].find('/tape/') >= 0:
                on_tape = True

        if on_tape:

            print('File is on tape.')

            # File is on tape
            # Delete and remove any disk locations from sam.

            for loc in locs:
                if loc['location_type'] == 'disk' and loc['location'].find('/tape/') < 0:

                    # Delete unmerged file from disk.

                    dir = os.path.join(loc['mount_point'], loc['subdir'])
                    fp = os.path.join(dir, f)
                    print('Deleting file from disk.')
                    self.remove(fp)
                    print('Removing disk location from sam.')
                    self.samweb.removeFileLocation(f, loc['full_path'])

        else:

            # File is not on tape.
            # Check disk locations, if requested to do so.

            if do_check_disk:

                # Check content status.

                content_good = False
                md = self.samweb.getMetadata(f)
                if 'content_status' in md:
                    if md['content_status'] == 'good':
                        content_good = True
                if content_good:
                    print('Content status good.')
                else:
                    print('Content status bad.')

                # Check disk locations.

                print('Checking disk locations.')
                for loc in locs:
                    if loc['location_type'] == 'disk' and loc['location'].find('/tape/') < 0:
                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                        fp = os.path.join(dir, f)
                        if content_good and self.exists(fp):
                            print('Location OK.')
                            on_disk = True
                        else:
                            print('Removing bad disk location from sam.')
                            self.samweb.removeFileLocation(f, loc['full_path'])
                            self.remove(fp)
                    else:
                        print('Removing bad location from sam.')
                        self.samweb.removeFileLocation(f, loc['full_path'])

        # If file has no valid locations, forget about this file.

        if not on_tape and do_check_disk and not on_disk:
            print('File has no valid locations.')
            print('Forget about this file.')
            if c == None:
                c = self.conn.cursor()
            q = 'DELETE FROM unmerged_files WHERE name=?;'
            c.execute(q, (f,))
            self.conn.commit()
            self.total_unmerged_files_deleted += 1

        # Done

        return (on_disk, on_tape)


    # Delete desk locations for this file.

    def delete_disk_locations(self, f):

        print('Deleting disk locations for file %s' % f)

        # Get location(s).

        locs = self.samweb.locateFile(f)
        for loc in locs:
            if loc['location_type'] == 'disk' and loc['location'].find('/tape/') < 0:

                # Delete unmerged file from disk.

                dir = os.path.join(loc['mount_point'], loc['subdir'])
                fp = os.path.join(dir, f)
                print('Deleting file from disk.')
                self.remove(fp)
                print('Removing disk location from sam.')
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
            print('Checking unmerged file %s' % f)
            locs = locdict[f]

            # See if this file is on tape already.

            on_tape = False
            on_disk = False
            for loc in locs:
                if loc['location_type'] == 'tape' or loc['location'].find('/tape/') >= 0:
                    on_tape = True

            if on_tape:

                print('File is already on tape.')

                # File is on tape
                # Modify metadata to set merge.merge flag to be false, so that this
                # file will no longer be considered for merging.

                mdmod = {'merge.merge': 0}
                print('Updating metadata to reset merge flag.')
                self.modifyFileMetadata(f, mdmod)

                # Delete and remove any disk locations from sam.
                # This shouldn't ever really happen.

                for loc in locs:
                    if loc['location_type'] == 'disk' and loc['location'].find('/tape/') < 0:

                        # Delete unmerged file from disk.

                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                        fp = os.path.join(dir, f)
                        print('Deleting file from disk.')
                        self.remove(fp)
                        print('Removing disk location from sam.')
                        self.samweb.removeFileLocation(f, loc['full_path'])

            else:

                # File is not on tape.
                # Check disk locations.

                print('Checking disk locations.')
                for loc in locs:
                    if loc['location_type'] == 'disk' and loc['location'].find('/tape/') < 0:
                        dir = os.path.join(loc['mount_point'], loc['subdir'])
                        fp = os.path.join(dir, f)
                        if larbatch_posix.exists(fp):
                            print('Location OK.')
                            on_disk = True
                        else:
                            print('Removing bad location from sam.')
                            self.samweb.removeFileLocation(f, loc['full_path'])

            

            if on_disk:

                # File has valid disk location.

                print('Adding unmerged file %s' % f)
                group_id = self.merge_group(md)
                if group_id > 0:
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
                    self.total_unmerged_files_added += 1
                    #self.conn.commit()

                else:

                    # Unmergable.

                    print('Deleting unmergable file %s' % f)
                    self.delete_disk_locations(f)


            else:

                # No valid location.

                print('File does not have a valid location.')

        # Done.

        #self.conn.commit()
        self.add_queue = []
        self.flush_metadata()
        return


    # Function to bulk-add a collection of unmerged files to unmerged_files table.
    # Return final add list as python set.

    def add_unmerged_files(self, flist):

        # Make sure add list is in form of a python set.

        add_files = set(flist)
        print('\n%d files in initial add group.' % len(add_files))

        # Query database to see which of these files already exist.
        # Limit size of queries to what sqlite can handle.

        c = self.conn.cursor()
        uq = []
        existing_files = []
        for f in add_files:
            uq.append(f)

            # Maybe flush add queue.

            if len(uq) >= 500:
                placeholders = ('?,'*len(uq))[:-1]
                q = 'SELECT name FROM unmerged_files WHERE name IN (%s);' % placeholders
                c.execute(q, uq)
                rows = c.fetchall()
                for row in rows:
                    existing_files.append(row[0])
                uq = []

        # Final queue flush.

        if len(uq) > 0:
            placeholders = ('?,'*len(uq))[:-1]
            q = 'SELECT name FROM unmerged_files WHERE name IN (%s);' % placeholders
            c.execute(q, uq)
            rows = c.fetchall()
            for row in rows:
                existing_files.append(row[0])

        # Remove existing files from add queue.

        for f in existing_files:
            print('Ignoring %s' % f)
            add_files.discard(f)
        print('%d files in final add list.' % len(add_files))

        # Loop over files in add list and do bulk adds.

        for f in add_files:            
            print('Adding %s' % f)
            self.add_queue.append(f)
            if len(self.add_queue) >= self.add_queue_max:
                self.flush_add_queue()
        if len(self.add_queue) > 0:
            self.flush_add_queue()

        # Done.

        return add_files


    # Get quality of specified run.

    def get_quality(self, run):

        result = 'bad'

        if run in self.good_runs:
            result = 'good'

        return result


    # Get epoch of specified run.

    def get_epoch(self, run):

        result = ''

        # Loop over epochs

        for key in self.epochs:
            limits = self.epochs[key]
            if run >= limits[0] and run <= limits[1]:
                result = key
                break

        # Done.

        return result


    # Find the run group corresponding to a single run.

    def run_group_single(self, run):

        result = 0
        print('Querying run group for run %d' % run)

        # Query run_groups table to see if this run already has a run group.

        c = self.conn.cursor()
        q = 'SELECT run_group_id FROM run_groups WHERE run=?'
        c.execute(q, (run,))
        rows = c.fetchall()
        if len(rows) > 0:
            result = rows[0][0]

        else:

            # Define a new run group.
            # Get epoch and quality of current run.

            epoch = self.get_epoch(run)
            quality = self.get_quality(run)

            # Calculate absolute lower and upper bounds for a new run group.

            run_low = self.group_runs * (run // self.group_runs)
            run_high = run_low + self.group_runs - 1

            # Find runs with matching epoch and quality.

            runs = set()
            for r in range(run_low, run_high+1):
                if self.get_epoch(r) == epoch and self.get_quality(r) == quality:
                    runs.add(r)

            # Filter out any existing runs.

            q = 'SELECT run FROM run_groups WHERE run >= ? and run <= ?;'
            c.execute(q, (run_low, run_high))
            rows = c.fetchall()
            for row in rows:
                r = row[0]
                if r in runs:
                    runs.remove(r)

            # Get a new run group id.

            q = 'SELECT MAX(run_group_id) FROM run_groups;'
            c.execute(q)
            row = c.fetchone()
            if row[0] == None:
                run_group_id = 1
            else:
                run_group_id = row[0] + 1

            # Assign runs to this run group id.

            for r in runs:
                q = 'INSERT INTO run_groups (run, run_group_id, epoch, quality) VALUES(?,?,?,?);'
                c.execute(q, (r, run_group_id, epoch, quality))
            self.conn.commit()

            result = run_group_id

        return result


    # Find the run group corresponding to a set of runs.

    def run_group(self, runs):

        # If all runs have the same run group, return that run group.
        # Otherwise, return 0

        result = 0
        rgs = set()
        for run in runs:
            rg = self.run_group_single(run)
            if not rg in rgs:
                rgs.add(rg)
        if len(rgs) == 1:
            result = rgs.pop()
        return result


    # Function to return the merge group id corresponding to a sam metadata dictionary.
    # If necessary, add a new merge group to merge_groups table.
    # If the return value is zero, this metadata does not correspond to any merge group.

    def merge_group(self, md):

        group_id = -1

        # Check that all nine required metadata fields are included.  If not return 0.
        # Metadata field 'data_stream' is optional.

        if not 'file_type' in md:
            return 0
        if not 'file_format' in md:
            return 0
        if not 'data_tier' in md:
            return 0
        if not 'ub_project.name' in md:
            return 0
        if not 'ub_project.stage' in md:
            return 0
        if not 'ub_project.version' in md:
            return 0
        if not 'runs' in md:
            return 0
        if not 'application' in md:
            return 0
        else:
            if not 'family' in md['application']:
                return 0
            if not 'name' in md['application']:
                return 0
        if not 'fcl.name' in md:
            return 0

        # Create group 11-tuple.

        file_type = md['file_type']
        file_format = md['file_format']
        data_tier = md['data_tier']
        if 'data_stream' in md:
            data_stream = md['data_stream']
        else:
            data_stream = 'none'
        ubproject = md['ub_project.name']
        ubstage = md['ub_project.stage']
        ubversion = md['ub_project.version']
        runs = set()
        for rst in md['runs']:   # rst = (run, subrun, run_type)
            runs.add(rst[0])
        run = 0
        if self.group_runs > 0:
            run = -self.run_group(runs)
            print('Run group = %d' % -run)
        else:
            if len(runs) == 1:
                run = runs.pop()
                print('Run = %d' % run)
            else:
                print('Setting run number to zero because file contains more than one run.')
                print('Runs = %s' % list(runs))
        app_family = md['application']['family']
        app_name = md['application']['name']
        fcl_name = md['fcl.name']
        gtuple = (file_type, file_format, data_tier, data_stream,
                  ubproject, ubstage, ubversion, run, app_family, app_name, fcl_name)

        # Filter undefined merge groups.

        if data_stream == 'outmucs' and run >= 24320:
            return 0

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
               and run=?
               and app_family=?
               and app_name=?
               and fcl_name=?'''
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
            print("  app_family = %s" % gtuple[8])
            print("  app_name = %s" % gtuple[9])
            print("  fcl_name = %s" % gtuple[10])

            q = '''INSERT INTO merge_groups
                   (file_type, file_format, data_tier, data_stream, project, stage, version, run, app_family, app_name, fcl_name)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?);'''
            c.execute(q, gtuple)
            group_id = c.lastrowid

        else:

            group_id = rows[0][0]

        # Done

        #self.conn.commit()
        return group_id


    # Function to update sam projects by assigning currently unaffiliated unmerged files
    # to sam projects.

    def update_sam_projects(self):

        # Figure out the maximum number of new sam projects we can create.
        # If this is zero or negative, we are done.

        c = self.conn.cursor()
        q = 'SELECT COUNT(*) FROM sam_projects WHERE status<2;'
        c.execute(q)
        mrow = c.fetchone()
        max_new_projects = self.max_projects - mrow[0]

        print('Number of projects = %d' % mrow[0])
        print('Maximum number of new projects = %d' % max_new_projects)

        if max_new_projects <= 0:
            print('No new projects are allowed.')
            return

        # Get the current time for age calculation.

        now = datetime.datetime.utcnow()
        print('Current time = %s' % now)


        # Query unassigned files with view to identifying merge groups that can
        # be upgraded to sam projects.

        q = '''SELECT id, name, group_id, size, create_date FROM unmerged_files
               WHERE sam_project_id=0 AND sam_process_id=0 ORDER BY create_date;'''
        c.execute(q)
        rows = c.fetchall()
        print('Checking %d unassigned unmerged files' % len(rows))

        # Loop over files.

        new_project_groups = set()
        group_size = {}

        for row in rows:

            id = row[0]
            name = row[1]
            group_id = row[2]
            size = row[3]
            create_date = row[4]

            # Skip this file if this group id is already tagged.

            if group_id in new_project_groups:
                continue

            # Check whether we have exceeded the maximum number of new sam projects.

            if len(new_project_groups) >= max_new_projects:
                print('\nNo more new projects are allowed.')
                break
            else:
                #print('\nRemaining new projects = %d' % (max_new_projects - len(new_project_groups)))
                pass

            # Calculate file age.

            t = datetime.datetime.strptime(create_date, '%Y-%m-%dT%H:%M:%S+00:00')
            dt = now - t
            age = dt.total_seconds()

            #print('\nChecking file %s' % name)
            #print('Group id = %s' % group_id)
            #print('Age = %d seconds (%8.2f days)' % (age, float(age)/86400))
            #print('Size = %d' % size)
            if age > self.max_age:
                print('\nCreate project for file %s because file is older than maximum age.' % name)
                print('Group id = %s' % group_id)
                print('Age = %d seconds (%8.2f days)' % (age, float(age)/86400))
                print('Size = %d' % size)
                new_project_groups.add(group_id)
                continue

            # Check total size of this group_id

            if group_id in group_size:
                group_size[group_id] += size
            else:
                group_size[group_id] = size
            #print('Group size = %d' % group_size[group_id])
            if group_size[group_id] >= self.min_size:
                print('\nCreate project for file %s because group size is greater than minimum size.' % name)
                print('Group id = %s' % group_id)
                print('Age = %d seconds (%8.2f days)' % (age, float(age)/86400))
                print('Size = %d' % size)
                print('Group size = %d' % group_size[group_id])
                new_project_groups.add(group_id)
                continue

        # Done with loop over files.

        print('%d new projects will be created.' % len(new_project_groups))

        # Loop over new project groups.

        for group_id in new_project_groups:

            print('\nCreating new project for group id %d.' % group_id)

            # Query files in this group.
            # Calculate total size of this group.
            # Construct sam dimension for this group.

            q = 'SELECT name, size FROM unmerged_files WHERE group_id=?;'
            c.execute(q, (group_id,))
            rows = c.fetchall()
            file_names = []
            total_size = 0
            dim = ''         # Sam dimension.
            for row in rows:
                name = row[0]
                size = row[1]
                file_names.append(name)
                total_size += size
                if dim == '':
                    dim = 'file_name \'%s\'' % name
                else:
                    dim += ',\'%s\'' % name
            nfiles = len(file_names)
            print('This group contains %d files.' % nfiles)

            # Make sure this group is not empty (this shouldn't ever happen).

            if nfiles == 0:
                print('Skipping empty group.')
                continue

            # Perform duplciate file check for files in this group.

            create_project = True
            parents = set()
            mds = self.get_multiple_metadata(file_names)
            for md in mds:
                f = md['file_name']
                if 'parents' in md:
                    for parentdict in md['parents']:
                        if 'file_name' in parentdict:
                            parent = parentdict['file_name']
                            if not parent.startswith('CRT'):
                                if parent not in parents:
                                    parents.add(parent)
                                else:

                                    # If we find a file with a duplicate parent, delete
                                    # that file.

                                    print('Unmerged file %s has duplicate parent.' % f)
                                    self.delete_disk_locations(f)
                                    self.delete_unmerged_file(f)
                                    create_project = False

                                    # Find all files with this same parent.

                                    print('All files with this parent:')
                                    for md2 in mds:
                                        if 'parents' in md2:
                                            for parentdict2 in md2['parents']:
                                                if 'file_name' in parentdict2:
                                                    parent2 = parentdict2['file_name']
                                                    if parent2 == parent:
                                                        print(md2['file_name'])

                else:

                    # This unmerged file doesn't have any parents.

                    print('Unmerged file %s is an orphan.' % f)
                    self.delete_disk_locations(f)
                    self.delete_unmerged_file(f)
                    create_project = False

            # If we got a duplicate parent, abort this project creation.
            # We should get this project on a subsequent invocation, with 
            # the duplicate processed file having been deleted.

            if create_project:
                print('Duplicate parent check OK.')
            else:
                print('Duplicate parent check failed.')
                #self.flush_delete_unmerged_queue()

            # Create project in merge database.

            if create_project:

                # Create sam dataset definition.

                defname = 'merge_%s' % uuid.uuid4()
                print('Creating dataset definition %s' % defname)
                self.samweb.createDefinition(defname, dim,
                                             user=project_utilities.get_user(), 
                                             group=project_utilities.get_experiment())


                # Calculate number of batch jobs and maximum files per job

                num_jobs = int((total_size - 1) / self.max_size) + 1
                if num_jobs > nfiles:
                    num_jobs = nfiles
                max_files_per_job = int((nfiles - 1) / num_jobs) + 1
                if max_files_per_job > self.max_count and self.max_count > 0:
                    max_files_per_job = self.max_count
                    num_jobs = int((nfiles - 1) / max_files_per_job) + 1
                print('Number of files = %d' % nfiles)
                print('Number of batch jobs = %d' % num_jobs)
                print('Maximum files per job = %d' % max_files_per_job)

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
                self.total_sam_projects_added += 1

        # Done

        self.flush_delete_unmerged_queue()
        return


    # Function to determine whether to end a project.

    def should_stop_project(self, prjstat):

        result = False

        # Check the project start time.

        if 'project_start_time' in prjstat:
            startstr = prjstat['project_start_time']
            print('Project start time = %s' % startstr)
            t = datetime.datetime.fromtimestamp(0)
            try:
                t = datetime.datetime.strptime(startstr, '%Y-%m-%dT%H:%M:%S.%f+00:00')
            except:
                print('Malformed time stamp.')
                t = datetime.datetime.fromtimestamp(0)
            now = datetime.datetime.utcnow()
            dt = now - t
            dtsec = dt.total_seconds()
            print('Project age = %d seconds' % dtsec)

            # If start time is older than 24 hours, stop this project.

            if self.nobatch or dtsec > 24*3600:
                result = True

        else:

            # Project status is malformed.
            # Stop project.

            result = True

        # Done

        return result


    # Flush delete project queue, leaving queue empty.

    def flush_delete_project_queue(self):

        if len(self.delete_project_queue) > 0:

            # Delete all sam project ids in delete queue.

            print('Flushing delete project queue.')
            print('Delete project queue has %d members.' % len(self.delete_project_queue))

            c = self.conn.cursor()
            placeholders = ('?,'*len(self.delete_project_queue))[:-1]
            q = 'UPDATE unmerged_files SET sam_project_id=? WHERE sam_project_id IN (%s);' % placeholders
            c.execute(q, [0] + self.delete_project_queue)

            q = 'UPDATE sam_processes SET sam_project_id=? WHERE sam_project_id IN (%s);' % placeholders
            c.execute(q, [0] + self.delete_project_queue)

            q = 'DELETE FROM sam_projects WHERE id IN (%s)' % placeholders
            c.execute(q, self.delete_project_queue)

            self.conn.commit()
            self.total_sam_projects_deleted += len(placeholders)

            # Clear delete queue.

            self.delete_project_queue = []
            print('Done flushing delete project queue.')

        # Done

        return


    # Deferred delete project id.

    def delete_project(self, sam_project_id):
        self.delete_project_queue.append(sam_project_id)
        if len(self.delete_project_queue) >= self.delete_project_queue_max:
            self.flush_delete_project_queue()
        return


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
            self.conn.commit()
            for row in rows:
                sam_project = row[0]
                sam_project_id = row[1]
                defname = row[2]
                num_jobs = row[3]
                max_files_per_job = row[4]

                print('\nStatus=%d, sam project %s' % (status, sam_project))

                if status == 3:

                    # Finished.
                    # Delete this project.

                    print('Deleting project %s' % sam_project)

                    # Maybe validate locations of any unmerged files associated with this process.
                    # Only do this if there is no corresponding sam process.

                    q = 'SELECT name FROM unmerged_files WHERE sam_project_id=? AND sam_process_id=0'
                    c.execute(q, (sam_project_id,))
                    rows = c.fetchall()
                    if len(rows) > 0:
                        print('Checking locations of remaining unmerged files.')
                        for row in rows:
                            f = row[0]
                            self.check_location(f, True)

                    # Add project to delete queue.

                    print('Adding project to delete queue.')
                    print('Delete project queue now has %d members.' % len(self.delete_project_queue))
                    self.delete_project(sam_project_id)

                if status == 2:

                    # Project ended.

                    prjsum = {}
                    try:
                        prjsum = self.samweb.projectSummary(sam_project)
                    except:
                        prjsum = {}

                    # Loop over processes.

                    procs = []
                    if 'processes' in prjsum:
                        procs = prjsum['processes']

                    self.total_sam_processes += len(procs)
                    if len(procs) == 0:
                        print('No processes.')
                        self.total_sam_projects_noprocs += 1

                    for proc in procs:
                        pid = proc['process_id']
                        print('SAM process id = %d' % pid)

                        # Query files consumed by this process.

                        consumed_files = []
                        dim = 'consumer_process_id %d and consumed_status consumed' % pid
                        files = self.samweb.listFiles(dim)
                        for f in files:
                            consumed_files.append(f)
                        print('Number of consumed files = %d' % len(consumed_files))

                        if len(consumed_files) == 0:
                            print('SAM project %s did not consume any files.' % sam_project)
                            self.total_sam_processes_failed += 1
                        if len(consumed_files) > 0:

                            # Determine file names produced by this process.
                            # Look at children of consumed files.

                            dim = ''
                            for consumed_file in consumed_files:
                                if dim == '':
                                    dim = 'ischildof:( file_name \'%s\'' % consumed_file
                                else:
                                    dim += ',\'%s\'' % consumed_file
                            dim += ' ) with availability anylocation'

                            files = self.samweb.listFiles(dim)

                            # If no files were produced by this project, forget about the
                            # consumed unmerged files.  These files will remain on disk and
                            # they will subsequently be rediscovered.

                            if len(files) == 0:

                                print('SAM project %s consumed %d files, but did not produce any files.' % (sam_project, len(consumed_files)))
                                self.total_sam_processes_failed += 1

                                # Loop over consumed files.

                                for f in consumed_files:

                                    # First do a location check on this file.

                                    self.check_location(f, True)

                                    # Forget about this file.
                                    # This will force a recalculation of the merge group when (if)
                                    # this file is rediscovered via a sam query.

                                    print('Forgetting about %s' % f)
                                    self.delete_unmerged_file(f)
                                self.flush_delete_unmerged_queue()

                            else:
                                self.total_sam_processes_succeeded += 1

                            # Loop over produced files.

                            for f in files:

                                # Need to verify process_id.

                                md = self.samweb.getMetadata(f)
                                if 'process_id' in md:
                                    if pid == md['process_id']:

                                        print('Output file = %s' % f)

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
                                            print('Unmerged file %s' % consumed_file)

                                        # Update process id join with unmerged file.
                                        # Make sure query doesn't get too large for sqlite
                                        # to handle.

                                        uq = []
                                        for f in consumed_files:
                                            uq.append(f)

                                            # Maybe flush queue.

                                            if len(uq) >= 500:
                                                placeholders = ('?,'*len(uq))[:-1]
                                                q = '''UPDATE unmerged_files SET sam_process_id=? 
                                                       WHERE name IN (%s);''' % placeholders
                                                c.execute(q, (merge_id,) + tuple(uq))
                                                uq = []

                                        # Final queue flush.

                                        if len(uq) > 0:
                                            placeholders = ('?,'*len(uq))[:-1]
                                            q = '''UPDATE unmerged_files SET sam_process_id=? 
                                                   WHERE name IN (%s);''' % placeholders
                                            c.execute(q, (merge_id,) + tuple(uq))
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
                    if 'project_end_time' in prjstat:
                        endstr = prjstat['project_end_time']
                        endstr = endstr.split('+')[0]
                        endstr = endstr.split('.')[0]
                        if len(endstr) > 1:

                            # Calculate how long since the project ended.

                            t = datetime.datetime.strptime(endstr, '%Y-%m-%dT%H:%M:%S')
                            now = datetime.datetime.utcnow()
                            dt = now - t
                            dtsec = dt.total_seconds()

                            #if dtsec > 10800:
                            if self.nobatch or dtsec > 1800:

                                print('Project ended: %s' % sam_project)
                                prj_ended = True

                            else:

                                print('Project cooling off (ended %d seconds ago): %s' % (
                                    dtsec, sam_project))

                    if prj_ended:

                        # Update project status to 2.

                        q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                        c.execute(q, (2, sam_project_id))
                        self.conn.commit()
                        self.total_sam_projects_ended += 1

                    elif prj_started and 'project_status' in prjstat and \
                         (prjstat['project_status'] == 'reserved' or \
                          prjstat['project_status'] == 'starting'):

                        # Project is in an unkillable state.
                        # Just forget about this project.

                        print('Forgetting about this project.')
                        q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                        c.execute(q, (2, sam_project_id))
                        self.conn.commit()
                        self.total_sam_projects_killed += 1

                    elif prj_started:

                        # Project has started, but has not ended.

                        print('Project %s has started, but has not yet ended.' % sam_project)

                        # Figure out if we should stop this project.

                        stop_project = self.should_stop_project(prjstat)

                        if stop_project:
                            print('Stop project %s' % sam_project)
                            try:
                                self.samweb.stopProject(sam_project)
                            except:
                                print('Unable to stop project.')

                            # Advance the status to 2.

                            q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                            c.execute(q, (2, sam_project_id))
                            self.conn.commit()
                            self.total_sam_projects_killed += 1


                    else:

                        # Project has not started.

                        print('Project %s has not started.' % sam_project)

                        # Check submit time.

                        q = '''SELECT submit_time FROM sam_projects WHERE id=?'''
                        c.execute(q, (sam_project_id,))
                        row = c.fetchone()
                        self.conn.commit()
                        stime_str = row[0]
                        stime = datetime.datetime.strptime(stime_str, '%Y-%m-%d %H:%M:%S')
                        print('Submit time = %s' % stime_str)

                        now = datetime.datetime.now()
                        now_str = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
                        print('Current time = %s' % now_str)

                        dt = now - stime
                        print('Project age = %s' % dt)

                        if self.nobatch or dt.total_seconds() > 24*3600:

                            # If project age is greater than 24 hours, start and then
                            # immediately stop this project, so that no batch job can
                            # start it later.
                            # A subsequent invocation of this script will handle
                            # the ended project.

                            print('Start project %s' % sam_project)
                            try:
                                self.samweb.startProject(sam_project,
                                                         defname=defname, 
                                                         station=project_utilities.get_experiment(),
                                                         group=project_utilities.get_experiment(),
                                                         user=project_utilities.get_user())

                                print('Stop project %s' % sam_project)
                                self.samweb.stopProject(sam_project)
                            except:
                                print('Failed to start or end project.')

                            # Advance the status to 2.

                            q = 'UPDATE sam_projects SET status=? WHERE id=?;'
                            c.execute(q, (2, sam_project_id))
                            self.conn.commit()
                            self.total_sam_projects_killed += 1


                elif status == 0:

                    # Project not started.
                    # Submit batch jobs.
                    # Submit function will update project status to 1 if 
                    # batch submission is successful.

                    self.submit(sam_project_id)

            # Done looping over sam projects.
            # Maybe flush submit queue.

            if status == 0:
                self.flush_submit_queue(0)

            # Flush delete project queue.

            self.flush_delete_project_queue()

        # Done looping over statuses.

        return


    # Function to perform post-submit processing.  Does following actions.
    #
    # 1.  Checks exit status (success/fail).
    # 2.  Delete temporary files.
    # 3.  Extract job id and cluster id from jobsub_submit output.
    # 4.  Update database.
    #
    # The argument is an object of type SubmitStruct

    def postsubmit(self, sub):

        print('\nDoing post-submission tasks for sam project %s' % sub.prjname)

        # Check exit status and output from jobsub_submit.

        jobid = ''
        clusid = ''
        batchok = False
        jobout, joberr = sub.jobinfo.communicate(input)
        jobout = convert_str(jobout)
        joberr = convert_str(joberr)
        rc = sub.jobinfo.poll()
        if rc == 0:

            # Extract jobsub id from captured output.

            for line in jobout.split('\n'):
                if "JobsubJobId" in line:
                    jobid = line.strip().split()[-1]
                elif "Use job id" in line:
                    jobid = line.strip().split()[3]
            if jobid != '':
                words = jobid.split('@')
                if len(words) == 2:
                    clus = words[0].split('.')[0]
                    server = words[1]
                    clusid = '%s@%s' % (clus, server)
                    batchok = True

        if batchok:

            # Batch job submission succeeded.

            print('Batch job submission succeeded.')
            #print('Submit command: %s' % sub.command)
            #print('\nJobsub output:')
            #print(jobout)
            #print('\nJobsub error output:')
            #print(joberr)
            print('Job id = %s' % jobid)
            print('Cluster id = %s' % clusid)

            # Update sam_projects table with information about this job submission.

            submit_time = datetime.datetime.strftime(datetime.datetime.now(), 
                                                     '%Y-%m-%d %H:%M:%S')
            c = self.conn.cursor()
            q = '''UPDATE sam_projects
                   SET name=?,cluster_id=?,submit_time=?,status=?
                   WHERE id=?;'''
            c.execute(q, (sub.prjname, clusid, submit_time, 1, sub.sam_project_id))

            # Done updating database in this function.

            self.conn.commit()
            self.total_sam_projects_started += 1

        else:

            # Batch job submission failed.

            print('Batch job submission failed.')
            print('Submit command: %s' % sub.command)
            print('\nJobsub output:')
            print(jobout)
            print('\nJobsub error output:')
            print(joberr)

            # Stop sam project.

            if sub.prj_started:
                print('Stopping sam project %s' % sub.prjname)
                try:
                    self.samweb.stopProject(sub.prjname)
                except:
                    pass

        # Delete temporary files.

        for tmpdir in sub.tmpdirs:
            if larbatch_posix.isdir(tmpdir):
                larbatch_posix.rmtree(tmpdir)

        # Done.

        return


    # Function to do a full or partial flush of submit queue.
    # Upon return this function guarantees that the submit queue will
    # have at most the number of processes specified as the argument.
    # To do a full flush, call with argument zero.

    def flush_submit_queue(self, maxproc):

        # Quit if the submit queue is already below the maximum.

        if len(self.submit_queue) <= maxproc:
            return

        if maxproc == 0:
            print('\nDoing a full flush of submit queue.')
        else:
            print('\nDoing a partial flush of submit queue to a maximum of %d processes.' % maxproc)

        while len(self.submit_queue) > maxproc:

            print('There are currently %d processes in submit queue.' % len(self.submit_queue))

            # Loop over processes and remove any that are finished or have exceeded the timeout.

            now = time.time()
            for sub in self.submit_queue:

                # Kill process if it has exceeded the timeout.

                if now - sub.start_time >= self.submit_queue_timeout:
                    print('\nKilling submit process for sam project %s' % sub.prjname)
                    sub.jobinfo.terminate()
                    sub.jobinfo.wait()

                # Check whether this process has finished.

                if sub.jobinfo.poll() != None:
                    print('\nSubmit process for project %s finished.' % sub.prjname)
                    self.postsubmit(sub)
                    self.submit_queue.remove(sub)
                    break

            # Rest a bit if queue is still full.

            if len(self.submit_queue) > maxproc:
                time.sleep(2)

        # Done.

        print('\nDone flushing submit queue.')
        print('Submit queue has %d entries.' % len(self.submit_queue))
        return


    # Function to start sam project and submit batch jobs.

    def submit(self, sam_project_id):

        # Throttle submit rate.
        # If this is the first submission, set the submit start time.

        if self.submit_num_submit == 0:
            self.submit_start_time = time.time()

        # Get the time since the first submit.

        delta_t = time.time() - self.submit_start_time

        # Increment the submit count.

        self.submit_num_submit += 1

        # Calculate the delay time to keep the submit rate under the maximum.

        submit_rate  = 0.
        if delta_t > 0.:
            submit_rate = (self.submit_num_submit - 1) / delta_t
        delta_tmin = self.submit_num_submit / self.submit_max_rate
        wait_t = delta_tmin - delta_t

        # Print summary

        print('Submit rate summary.')
        print('Submission number = %d' % self.submit_num_submit)
        print('Time since first submit = %10.2f' % delta_t)
        print('Average submit rate = %10.2f' % submit_rate)
        print('Wait time = %10.2f' % wait_t)

        # Do actual waiting.

        if wait_t > 0.:
            time.sleep(wait_t)

        # Periodically reset.

        if delta_t > 300.:
            self.submit_num_submit = 0
            
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
        if row == None:
            print('No files associated with this project.')
            q = 'DELETE FROM sam_projects WHERE id=?'
            c.execute(q, (sam_project_id,))
            self.conn.commit()
            self.total_sam_projects_deleted += 1
            return
        unmerged_file = row[0]
        self.conn.commit()

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
        if 'data_stream' in md:
            data_stream = md['data_stream']
        else:
            data_stream = ''

        # Generate a fcl file customized for this merged file.

        if file_type != 'root':
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
            if data_stream != '':
                fcl.write('    streamName:  "%s"\n' % data_stream)
            fcl.write('    compressionLevel: 3\n')
            fcl.write('  }\n')
            fcl.write('}\n')
            fcl.close()


        # Generate project name and stash the name in the database.

        prjname = self.samweb.makeProjectName(defname)
        print('Submitting batch job for project %s' % prjname)

        # Start project now.

        if num_jobs > 1:
            print('Starting sam project %s' % prjname)
            try:
                self.samweb.startProject(prjname,
                                         defname=defname, 
                                         station=project_utilities.get_experiment(),
                                         group=project_utilities.get_experiment(),
                                         user=project_utilities.get_user())
            except:
                pass
        else:
            print('Project will be started by batch job.')

        # Temporary directory where we will copy the batch script.

        tmpdir = tempfile.mkdtemp()

        # Temporary directory where we will assemble other files for batch worker.

        tmpworkdir = tempfile.mkdtemp()

        # Copy fcl file to work directory.

        if file_type != 'root':
            workfcl = os.path.join(tmpworkdir, os.path.basename(self.fclpath))
            if os.path.abspath(self.fclpath) != os.path.abspath(workfcl):
                print('Copying fcl from %s to %s' % (self.fclpath, workfcl))
                larbatch_posix.copy(self.fclpath, workfcl)
                os.remove(self.fclpath)

        # Copy and rename batch script to work directory.

        workname = 'merge-%s-%s-%s.sh' % (ubstage, ubproject, self.probj.release_tag)
        workscript = os.path.join(tmpdir, workname)
        if self.stobj.script != workscript:
            larbatch_posix.copy(self.stobj.script, workscript)

        # Copy worker initialization script to work directory.

        #if self.stobj.init_script != '':
        #    if not larbatch_posix.exists(self.stobj.init_script):
        #        raise RuntimeError, 'Worker initialization script %s does not exist.\n' % \
        #            self.stobj.init_script
        #    work_init_script = os.path.join(tmpworkdir, os.path.basename(self.stobj.init_script))
        #    if self.stobj.init_script != work_init_script:
        #        larbatch_posix.copy(self.stobj.init_script, work_init_script)

        # Copy worker initialization source script to work directory.

        #if self.stobj.init_source != '':
        #    if not larbatch_posix.exists(self.stobj.init_source):
        #        raise RuntimeError, 'Worker initialization source script %s does not exist.\n' % \
        #            self.stobj.init_source
        #    work_init_source = os.path.join(tmpworkdir, os.path.basename(self.stobj.init_source))
        #    if self.stobj.init_source != work_init_source:
        #        larbatch_posix.copy(self.stobj.init_source, work_init_source)

        # Copy worker end-of-job script to work directory.

        #if self.stobj.end_script != '':
        #    if not larbatch_posix.exists(self.stobj.end_script):
        #        raise RuntimeError, 'Worker end-of-job script %s does not exist.\n' % \
        #            self.stobj.end_script
        #    work_end_script = os.path.join(tmpworkdir, os.path.basename(self.stobj.end_script))
        #    if self.stobj.end_script != work_end_script:
        #        larbatch_posix.copy(self.stobj.end_script, work_end_script)

        # Copy helper scripts to work directory.

        helpers = ('root_metadata.py',
                   'merge_json.py',
                   'merge_metadata.py',
                   'validate_in_job.py',
                   'mkdir.py',
                   'emptydir.py')

        for helper in helpers:

            # Find helper script in execution path.

            jobinfo = subprocess.Popen(['which', helper],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            jobout, joberr = jobinfo.communicate()
            jobout = convert_str(jobout)
            joberr = convert_str(joberr)
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
            jobinfo.stdin.write(convert_bytes('import %s\nprint(%s.__file__)\n' % (helper_module, helper_module)))
            jobout, joberr = jobinfo.communicate()
            jobout = convert_str(jobout)
            joberr = convert_str(joberr)
            rc = jobinfo.poll()
            helper_path = jobout.splitlines()[-1].strip()
            if rc == 0:
                #print('helper_path = %s' % helper_path)
                work_helper = os.path.join(tmpworkdir, os.path.basename(helper_path))
                if helper_path != work_helper:
                    larbatch_posix.copy(helper_path, work_helper)
            else:
                print('Helper python module %s not found.' % helper_module)

        # Make a tarball out of all of the files in tmpworkdir in stage.workdir
        # Use a tarball name that is unique per invocation of this script.

        global worktarname
        if worktarname == None:
            worktarname = uuid.uuid4()
        tmptar = '%s/work%s.tar' % (tmpworkdir, worktarname)
        print('Work tarball = %s' % tmptar)
        jobinfo = subprocess.Popen(['tar','-cf', tmptar, '-C', tmpworkdir,
                                    '--mtime=2018-01-01',
                                    '--exclude=work.tar', '.'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        jobout, joberr = jobinfo.communicate()
        jobout = convert_str(jobout)
        joberr = convert_str(joberr)
        rc = jobinfo.poll()
        if rc != 0:
            raise RuntimeError('Failed to create work tarball in %s' % tmpworkdir)

        # Make sure outdir and logdir exist.

        if not larbatch_posix.isdir(self.stobj.outdir):
            larbatch_posix.makedirs(self.stobj.outdir)
        if self.stobj.logdir != self.stobj.outdir and not larbatch_posix.isdir(self.stobj.logdir):
            larbatch_posix.makedirs(self.stobj.logdir)

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

            # Get container image.

            img = '/cvmfs/singularity.opensciencegrid.org/fermilab/fnal-wn-%s:latest' % self.probj.os.lower()
            command.append('--singularity-image=%s' % img)
        if self.stobj.jobsub != '':
            for word in self.stobj.jobsub.split():
                command.append(word)
        opt = project_utilities.default_jobsub_submit_options()
        if opt != '':
            for word in opt.split():
                command.append(word)

        # Copy tarball containing fcl file and helpers.

        if check_jobsub_lite():
            #command.append('--use-pnfs-dropbox')
            #command.append('--skip-check=rcds')
            pass
        #command.extend(['-f', 'dropbox://%s' % tmptar])
        command.extend(['--tar-file-name', 'dropbox://%s' % tmptar])

        # Batch script.

        workurl = "file://%s" % workscript
        command.append(workurl)

        # Add batch script options.

        command.extend([' --group', project_utilities.get_experiment()])
        if file_type != 'root':
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
        #if self.stobj.init_script != '':
        #    command.extend([' --init-script', os.path.basename(self.stobj.init_script)])
        #if self.stobj.init_source != '':
        #    command.extend([' --init-source', os.path.basename(self.stobj.init_source)])
        #if self.stobj.end_script != '':
        #    command.extend([' --end-script', os.path.basename(self.stobj.end_script)])
        command.extend([' --init', project_utilities.get_setup_script_path()])
        if self.stobj.validate_on_worker == 1:
            print('Validation will be done on the worker node %d' % self.stobj.validate_on_worker)
            command.extend([' --validate'])
            command.extend([' --declare'])
        if self.stobj.copy_to_fts == 1:
            command.extend([' --copy'])
        command.extend(['--sam_station', project_utilities.get_experiment()])
        command.extend(['--sam_group', project_utilities.get_experiment()])
        command.extend(['--sam_defname', defname])
        command.extend(['--sam_project', prjname])
        command.extend(['--dirsize', '100'])
        command.extend(['--dirlevels', '2'])
        if num_jobs == 1:
            command.append('--sam_start')

        # Make sure there is room in the submit queue.

        self.flush_submit_queue(self.submit_queue_max - 1)

        # Dump poms environment.

        #print('POMS environment:')
        #for v in os.environ:
        #    if v.find('POMS') >= 0:
        #        print('%s = %s' % (v, os.environ[v]))

        # Maybe remove POMS and JOBSUB_EXTRA from environment.

        pomsenv = {}
        if random.random() * self.submit_queue_max >= 1.:
            for v in os.environ:
                if v.find('POMS') >= 0 or v.find('JOBSUB_EXTRA') >= 0:
                    pomsenv[v] = os.environ[v]
            for v in pomsenv:
                del os.environ[v]

        # Invoke the job submission command and add to submit queue.

        print('Invoke jobsub_submit')
        jobinfo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sub = SubmitStruct(time.time(),              # Start time (now).
                           jobinfo,                  # Popen object.
                           [tmpdir, tmpworkdir],     # Temporary files.
                           sam_project_id,           # Database sam project id.
                           prjname,                  # Sam project name.
                           num_jobs>1,               # Sam project started?
                           command)                  # Command (jobsub_submit, etc.).
        self.submit_queue.add(sub)
        print('Submit queue now has %d entries.' % len(self.submit_queue))

        # Restore POMS environment

        for v in pomsenv:
            os.environ[v] = pomsenv[v]

        # Done.

        return


    # Flush delete process queue, leaving queue empty.

    def flush_delete_process_queue(self):

        if len(self.delete_process_queue) > 0:

            # Delete all sam process ids in delete queue.

            print('Flushing delete process queue.')
            print('Delete process queue has %d members.' % len(self.delete_process_queue))

            c = self.conn.cursor()
            placeholders = ('?,'*len(self.delete_process_queue))[:-1]
            q = 'UPDATE unmerged_files SET sam_process_id=? WHERE sam_process_id IN (%s);' % placeholders
            c.execute(q, [0] + self.delete_process_queue)

            q = 'DELETE FROM sam_processes WHERE id IN (%s)' % placeholders
            c.execute(q, self.delete_process_queue)

            self.conn.commit()

            # Clear delete queue.

            self.delete_process_queue = []
            print('Done flushing delete process queue.')

        # Done

        return


    # Deferred delete process id.

    def delete_process(self, sam_process_id):
        self.delete_process_queue.append(sam_process_id)
        if len(self.delete_process_queue) >= self.delete_process_queue_max:
            self.flush_delete_process_queue()
        return


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
            self.conn.commit()
            for row in rows:
                merge_id = row[0]
                sam_process_id = row[1]
                merged_file = row[2]

                print('\nStatus=%d, file name %s' % (status, merged_file))

                if status == 3 or status == 4:

                    # Finished.

                    # Finished.
                    # Delete this process.

                    # First validate locations of any unmerged files associated with this process.

                    q = 'SELECT name, id FROM unmerged_files WHERE sam_process_id=?'
                    c.execute(q, (merge_id,))
                    rows = c.fetchall()
                    if len(rows) > 0:
                        print('Checking locations of remaining unmerged files.')
                        for row in rows:
                            f = row[0]
                            id = row[1]
                            self.check_location(f, True)

                            # Forget about this file.
                            # This will force a recalculation of the merge group when (if)
                            # this file is rediscovered via a sam query.

                            print('Forgetting about %s' % f)
                            self.delete_unmerged_file(f)
                        #self.flush_delete_unmerged_queue()

                    # Add process to delete queue.

                    print('Adding process to delete queue.')
                    print('Delete process queue now has %d members.' % len(self.delete_process_queue))
                    self.delete_process(merge_id)

                if status == 2:

                    # Located.
                    # Do cleanup for this merged file.

                    print('Doing cleanup for merged file %s' % merged_file)

                    # First query unmerged files corresponsing to this merged file.

                    unmerged_files = []
                    q = 'SELECT name FROM unmerged_files WHERE sam_process_id=?'
                    c.execute(q, (merge_id,))
                    rows = c.fetchall()
                    self.conn.commit()
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
                        self.modifyFileMetadata(f, mdmod)

                        # Delete disk locations for unmerged file.

                        self.delete_disk_locations(f)

                        # Delete unmerged file from database..

                        print('Deleting file from merge database: %s' % f)
                        self.delete_unmerged_file(f)

                    # Done looping over unmerged files.

                    #self.flush_metadata()
                    #self.flush_delete_unmerged_queue()

                    # End of loop over unmerged files.
                    # Cleaning done.
                    # Update status of sam process to 3

                    print('Cleaning finished.')
                    q = '''UPDATE sam_processes SET status=? WHERE id=?;'''
                    c.execute(q, (3, merge_id))
                    self.conn.commit()
  
                if status == 1:

                    # Declared.
                    # Check whether this file has a location.

                    on_disk, on_tape = self.check_location(merged_file, False)

                    if on_tape:

                        print('File located.')
                        q = 'UPDATE sam_processes SET status=? WHERE id=?;'
                        c.execute(q, (2, merge_id))
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
                        dtsec = dt.total_seconds()
                        print('File age = %d seconds.' % dtsec)
                        if dtsec > 24*3600:

                            # File too old, set error status.

                            print('File is too old.  Set error status.')
                            q = '''UPDATE sam_processes SET status=? WHERE id=?;'''
                            c.execute(q, (4, merge_id))
                            self.conn.commit()

                            # Also declare file bad in sam

                            mdmod = {'content_status': 'bad'}
                            print('Setting file bad status in sam.')
                            self.modifyFileMetadata(merged_file, mdmod)
                            #self.flush_metadata()

                if status == 0:

                    # Not declared (shouldn't happen).

                    pass

            # Done looping over sam processes.

            # Flush queues.

            self.flush_delete_unmerged_queue()
            self.flush_delete_process_queue()
            self.flush_metadata()

        # Done looping over statuses.

        return


    # Flush delete merge group queue, leaving queue empty.

    def flush_delete_merge_group_queue(self):

        if len(self.delete_merge_group_queue) > 0:

            # Delete all merge group ids in delete queue.

            print('Flushing delete merge group queue.')
            print('Delete merge group queue has %d members.' % len(self.delete_merge_group_queue))

            c = self.conn.cursor()
            placeholders = ('?,'*len(self.delete_merge_group_queue))[:-1]
            q = 'DELETE FROM merge_groups WHERE id IN (%s)' % placeholders
            c.execute(q, self.delete_merge_group_queue)

            self.conn.commit()

            # Clear delete queue.

            self.delete_merge_group_queue = []
            print('Done flushing delete merge group queue.')

        # Done

        return


    # Deferred delete merge group.

    def delete_merge_group(self, group_id):
        self.delete_merge_group_queue.append(group_id)
        if len(self.delete_merge_group_queue) >= self.delete_merge_group_queue_max:
            self.flush_delete_merge_group_queue()
        return


    # Function to remove unused merged groups from database.

    def clean_merge_groups(self):

        print('\nCleaning merge groups.')

        # Loop over empty merge groups.

        c = self.conn.cursor()
        q = 'SELECT id FROM merge_groups WHERE id NOT IN (SELECT DISTINCT group_id FROM unmerged_files) ORDER BY id;'
        c.execute(q)
        rows = c.fetchall()
        for row in rows:
            group_id = row[0]

            # Double check that no files belong to this merge group.

            q = 'SELECT COUNT(*) FROM unmerged_files WHERE group_id=?;'
            c.execute(q, (group_id,))
            row = c.fetchone()
            n = row[0]
            if n == 0:

                # Add merge group to delete queue.

                print('Adding merge group %d to delete queue' % group_id)
                print('Delete merge group now has %d members.' % len(self.delete_merge_group_queue))
                self.delete_merge_group(group_id)

        # Final flush of merge group delete queue.

        self.flush_delete_merge_group_queue()

        # Done.

        return


    # Function to remove unused run groups from database.

    def clean_run_groups(self):

        print('\nCleaning run groups.')

        # Loop over empty merge groups.

        c = self.conn.cursor()
        q = 'SELECT DISTINCT run_group_id FROM run_groups WHERE -run_group_id NOT IN (SELECT DISTINCT run FROM merge_groups);'
        c.execute(q)
        rows = c.fetchall()
        for row in rows:
            run_group_id = row[0]

            # Double check that no merge groups belong to this run group id.

            q = '''SELECT COUNT(*) FROM merge_groups, run_groups
                   WHERE run_groups.run_group_id=?
                   AND merge_groups.run = -run_groups.run_group_id;'''
            c.execute(q, (run_group_id,))
            row = c.fetchone()
            n = row[0]
            if n == 0:
                print('Deleting run group id %d' % run_group_id)
                q = 'DELETE FROM run_groups WHERE run_group_id=?;'
                c.execute(q, (run_group_id,))

        self.conn.commit()

        # Done.

        return


# Check whether we are using jobsub_lite.
# Return true if yes.
# Result is cached.

def check_jobsub_lite():

    global using_jobsub_lite

    # Check cached result.

    if using_jobsub_lite == None:
        using_jobsub_lite = False

        # Check jobsub_submit version.

        jobinfo = subprocess.Popen(['jobsub_submit', '--version'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        jobout, joberr = jobinfo.communicate()
        jobout = convert_str(jobout)
        joberr = convert_str(joberr)
        rc = jobinfo.poll()
        if rc == 0:
            print(jobout.rstrip())
            if jobout.find('jobsub_lite') >= 0:
                using_jobsub_lite = True

    # Done.

    return using_jobsub_lite


# Get parent process id of the specified process id.
# This function works by reading information from the /proc filesystem.
# Return 0 in case of any kind of difficulty.

def get_ppid(pid):

    result = 0

    statfname = '/proc/%d/status' % pid
    statf = open(statfname)
    for line in statf.readlines():
        if line.startswith('PPid:'):
            words = line.split()
            if len(words) >= 2 and words[1].isdigit():
                result = int(words[1])

    # Done.

    return result


# Check whether a similar process is already running.
# Return true if yes.

def check_running(argv):

    result = 0

    # Find all ancestor processes, which we will ignore.

    ignore_pids = set()
    pid = os.getpid()
    while pid > 1:
        ignore_pids.add(pid)
        pid = get_ppid(pid)

    # Look over pids in /proc.

    for pid in os.listdir('/proc'):
        if pid.isdigit() and int(pid) not in ignore_pids:
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

    # Sleep a random number of seconds.

    sleep_sec = int(30*random.random())
    time.sleep(sleep_sec)

    # Parse arguments.

    xmlfile = ''
    projectname = ''
    stagename = ''
    database = 'merge.db'
    defname = ''
    logdir = ''
    max_size = 2500000000
    min_size = 1000000000
    max_count = 0
    max_age = 3*24*3600
    max_projects = 500
    max_groups = 100
    query_limit = 1000
    file_limit = 10000
    group_runs = 0
    do_phase1 = False
    do_phase2 = False
    do_phase3 = False
    nobatch = False

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
        elif args[0] == '--logdir' and len(args) > 1:
            logdir = args[1]
            del args[0:2]
        elif args[0] == '--max_size' and len(args) > 1:
            max_size = int(args[1])
            del args[0:2]
        elif args[0] == '--min_size' and len(args) > 1:
            min_size = int(args[1])
            del args[0:2]
        elif args[0] == '--max_count' and len(args) > 1:
            max_count = int(args[1])
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
        elif args[0] == '--file_limit' and len(args) > 1:
            file_limit = int(args[1])
            del args[0:2]
        elif args[0] == '--group_runs' and len(args) > 1:
            group_runs = int(args[1])
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
        elif args[0] == '--nobatch':
            nobatch = True
            del args[0]
        else:
            print('Unknown option %s' % args[0])
            return 1

    # Check whether another process is already running.

    if check_running(argv):
        print('Quitting because similar process is already running.')
        sys.exit(0)

    # Check if we want to generate log files.

    if logdir != '':

        # Try to make logdir if it doesn't exist.

        if not os.path.exists(logdir):
            os.makedirs(logdir)

        # Make sure log directory exists.
            
        if os.path.exists(logdir):

            # Generate unique names for stdout and stderr log files using current time
            # according to the pattern merge_YYYYmmDD_HHMM.out/.err

            now = datetime.datetime.now()
            merge_name = 'merge_%s' % datetime.datetime.strftime(now, '%Y%m%d_%H%M')
            merge_name = merge_name + '_%s' % uuid.uuid4()
            outpath = '%s/%s.out' % (logdir, merge_name)
            errpath = '%s/%s.err' % (logdir, merge_name)

            # Override sys.stdout and sys.stderr

            sys.stdout = open(outpath, 'w', buffering=1)    # Line buffered
            sys.stderr = open(errpath, 'w', buffering=1)    # Line buffered

            # Dump the environment in a file in the logdir.

            f = open(os.path.join(logdir, 'env_%s.txt' % merge_name), 'w')
            for v in os.environ:
                f.write('%s=%s\n' % (v, os.environ[v]))
            f.close()

            # Dump bearer token information.

            f = open(os.path.join(logdir, 'decodetoken_%s.txt' % merge_name), 'w')
            out = subprocess.check_output(['htdecodetoken', '-H'])
            f.write(convert_str(out))
            f.close()

        else:

            # If log directory doesn't exist, write output to stdout and stderr.

            print('Log directory does not exist.')
            logdir = ''

    # If no phase option, do all three phases.

    if not do_phase1 and not do_phase2 and not do_phase3:
        do_phase1 = True
        do_phase2 = True
        do_phase3 = True

    # Create and populate run groups (do this once for the lifetime of the merge database).

    # Create merge engine.

    engine = MergeEngine(xmlfile, projectname, stagename, defname,
                         database, max_size, min_size, max_count, max_age,
                         max_projects, max_groups, query_limit, file_limit,
                         group_runs, nobatch)
    if do_phase1:
        engine.update_unmerged_files()
    if do_phase2:
        engine.update_sam_projects()
        engine.update_sam_project_status()
    if do_phase3:
        engine.update_sam_process_status()
        engine.clean_merge_groups()
        engine.clean_run_groups()

    # Done.

    print('\nStatistics:')
    print('Unmerged files added:      %d' % engine.total_unmerged_files_added)
    print('Unmerged files deleted:    %d' % engine.total_unmerged_files_deleted)
    print('SAM projects added:        %d' % engine.total_sam_projects_added)
    print('SAM projects submitted:    %d' % engine.total_sam_projects_started)
    print('SAM projects ended:        %d' % engine.total_sam_projects_ended)
    print('SAM projects no processes: %d' % engine.total_sam_projects_noprocs)
    print('SAM projects killed:       %d' % engine.total_sam_projects_killed)
    print('SAM projects deleted:      %d' % engine.total_sam_projects_deleted)
    print('SAM processes discovered:  %d' % engine.total_sam_processes)
    print('SAM processes succeeded:   %d' % engine.total_sam_processes_succeeded)
    print('SAM processes failed:      %d' % engine.total_sam_processes_failed)
    print('\nFinished.')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
