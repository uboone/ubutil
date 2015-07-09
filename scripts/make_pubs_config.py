#! /usr/bin/env python
######################################################################
#
# Name: make_pubs_config.py
#
# Purpose: Generate a pubs project configuration for a give mc xml file.
#          Pubs configuration is written to standard output.
#
# Created: 27-May-2015  Herbert Greenlee
#
# Usage:
#
# make_pubs_config.py <options> <xml-files> > <config-file>
#
# Options:
#
# -h|--help           - Print help.
# -m|--email <email>  - Specify contact e-mail address (default <username>@fnal.gov).
# --command <command> - Specify command (default "python dstream_prod/production.py")
# --server <node>     - Specify server node (default current node).
# --runtable <run-table> - Specify run table (default "mcrun").
# --first_run <first-run> - Specify first run (default 1).
# --first_subrun <first-subrun> - Specify first subrun (default 1).
# --last_run <last-run> - Specify the last run (default same as first run).
# --last_subrun <last-subrun> - Specify the last subrun (default same as number of 
#                               jobs in first stage of project).
# --nruns <nruns>     - Maximum number of files to process per invocation of
#                       production command (pubs parameter NRUNS).  Default 10.
#
######################################################################

import sys, os, getpass, socket
from xml.dom.minidom import parse
import project


# Print help.

def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:21] == 'make_pubs_config.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print line[2:],
            else:
                print


# Main program.

def main(argv):

    # Parse arguments.

    xmlfiles = []
    contact = ''
    command = 'python dstream_prod/production.py'
    server = ''
    runtablearg = ''
    first_run_arg = 1
    first_subrun_arg = 1
    last_run_arg = -1
    last_subrun_arg = -1
    nruns_arg = -1

    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help' :
            help()
            return 0
        elif args[0] == '--xml' and len(args) > 1:
            xmlfile = args[1]
            del args[0:2]
        elif (args[0] == '-m' or args[0] == '--email') and len(args) > 1:
            contact = args[1]
            del args[0:2]
        elif args[0] == '--server' and len(args) > 1:
            server = args[1]
            del args[0:2]
        elif args[0] == '--runtable' and len(args) > 1:
            runtablearg = args[1]
            del args[0:2]
        elif args[0] == '--first_run' and len(args) > 1:
            first_run_arg = int(args[1])
            del args[0:2]
        elif args[0] == '--first_subrun' and len(args) > 1:
            first_subrun_arg = int(args[1])
            del args[0:2]
        elif args[0] == '--last_run' and len(args) > 1:
            last_run_arg = int(args[1])
            del args[0:2]
        elif args[0] == '--last_subrun' and len(args) > 1:
            last_subrun_arg = int(args[1])
            del args[0:2]
        elif args[0] == '--nruns' and len(args) > 1:
            nruns_arg = int(args[1])
            del args[0:2]
        elif args[0][0] == '-':
            print 'Unknown option %s' % args[0]
            return 1
        else:
            xmlfiles.append(args[0])
            del args[0]

    # Make sure xmlfile was specified.

    if len(xmlfiles) == 0:
        print 'No xml files specified.  Type "make_pubs_config.py -h" for help.'
        return 1

    # Loop over xml files.

    for xmlfile in xmlfiles:

        # Convert xml file to absolute path.

        xmlpath = os.path.abspath(xmlfile)

        # Parse xml (returns xml document).

        xml = open(xmlpath)
        doc = parse(xml)

        # Extract root element.

        root = doc.documentElement

        # Find projectd in the root element.

        projects = project.find_projects(root)
        first_project = projects[0]
        first_stage = first_project.stages[0]

        # Set some additional defaults.

        runtable = runtablearg
        if contact == '':
            contact = '%s@fnal.gov' % getpass.getuser()
        if server == '':
            server = socket.gethostname()
        if runtable == '':
            runtable = 'mcrun'

        first_run = first_run_arg
        last_run = last_run_arg
        if last_run < 0:
            last_run = first_run

        first_subrun = first_subrun_arg
        last_subrun = last_subrun_arg
        if last_subrun < 0:
            last_subrun = first_stage.num_jobs

        nruns = nruns_arg
        if nruns < 0:
            nruns = 10
        if nruns > first_stage.num_jobs:
            nruns = first_stage.num_jobs

        # Extract stage names and status codes.

        status = 0
        status_codes = ''
        stage_names = ''
        for prj in projects:
            for stage in prj.stages:
                if status_codes == '':
                    status_codes = '%d' % status
                else:
                    status_codes = '%s:%d' % (status_codes, status)
                status += 10
                if stage_names == '':
                    stage_names = stage.name
                else:
                    stage_names = '%s:%s' % (stage_names, stage.name)

        # Extract pubs project name.  This is the same as the name of the 
        # first project in the xml file, except postgres doesn't allow
        # periods (.) or hyphens (-) in table names, so we replace both
        # with underscores (_).

        pubs_project_name = first_project.name.replace('.', '_')
        pubs_project_name = pubs_project_name.replace('-', '_')

        # Generate configuration.

        print 'PROJECT_BEGIN'
        print 'NAME      %s' % pubs_project_name
        print 'COMMAND   %s %s' % (command, pubs_project_name)
        print 'CONTACT   %s' % contact
        print 'SLEEP     30'
        print 'PERIOD    120'
        print 'SERVER    %s' % server
        print 'RUNTABLE  %s' % runtable
        print 'RUN       %d' % first_run
        print 'SUBRUN    %d' % first_subrun
        print 'ENABLE    True'
        print 'RESOURCE XMLFILE => %s' % xmlpath
        print 'RESOURCE NRESUBMISSION => 2'
        print 'RESOURCE EXPERTS => %s' % contact
        print 'RESOURCE STAGE_STATUS => %s' % status_codes
        print 'RESOURCE STAGE_NAME => %s' % stage_names
        print 'RESOURCE NRUNS => %d' % nruns
        print 'RESOURCE MAX_RUN => %d' % last_run
        print 'RESOURCE MAX_SUBRUN => %d' % last_subrun
        print 'PROJECT_END'
        print


# Invoke main program.

if __name__ == '__main__':
    sys.exit(main(sys.argv))
