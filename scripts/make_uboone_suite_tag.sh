#! /bin/bash
#------------------------------------------------------------------
#
# Name: make_uboone_suite_tag.sh
#
# Purpose: Make UBOONE_SUITE suite tag.
#
# Usage:
#
# make_uboone_suite_tag.sh [options] [<tag>]
#
# Options:
#
# -h|--help            - Print help message.
# -b|--branch <branch> - Make suite tag on head of this branch.
#                        If missing, use current revision.
# -f|--force           - Force flag.
# -n|--dryrun          - Don't make tags.  Just print messages.
# -p|--push            - Push tags to origin (default: no).
#
# Arguments:
#
# <tag> - Tag (optional).  If missing use uboonecode version.
#
# Usage notes:
#
# 1.  All suite packages that are supposed to be tagged should be
#     checked out in directory $MRB_SOURCE.
#
# 2.  The created suite tag will have the form UBOONE_SUITE_<tag>,
#     where <tag> is the tag specified on the command line, or
#     the uboonecode version.
#
# 3.  Obtain a valid kerberos ticket before invoking this script.
#
#------------------------------------------------------------------

# Help function.

function dohelp {
  sed -n '/^# make_uboone_suite_tag.sh/,/^# Usage notes/p' $0 | cut -c3- | head -n-2
}

# Parse arguments.

branch=''
force=''
tag=''
dryrun=0
push=0

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      dohelp
      exit
      ;;

    # Branch
    -b|--branch )
      if [ $# -gt 1 ]; then
        branch=$2
        shift
      fi

      ;;

    # Force
    -f|--force )
      force='-f'
      ;;

    # Dry run
    -n|--dryryn )
      dryrun=1
      ;;

    # Push
    -p|--push )
      push=1
      ;;

    # Other
    * )
      if [ x$tag = x ]; then
        tag=$1
      else
        echo "Too many arguments."
        dohelp
        exit 1
      fi
      ;;

  esac
  shift

done

# Make sure $MRB_SOURCE is defined and exists.

if [ x$MRB_SOURCE = x ]; then
  echo "MRB_SOURCE is not defined."
  exit 1
fi

if [ ! -d $MRB_SOURCE ]; then
  echo "$MRB_SOURCE does not exist."
  exit 1
fi

# If tag wasn't specified, get uboonecode version.

if [ x$tag = x ]; then
  if [ -f $MRB_SOURCE/uboonecode/ups/product_deps ]; then
    tag=`awk '/parent.*uboonecode/{print $3}' $MRB_SOURCE/uboonecode/ups/product_deps`
  else
    echo "No uboonecode product_deps found in $MRB_SOURCE"
    exit 1
  fi
fi
if [ x$tag = x ]; then
  echo "Problem getting uboonecode version from product_deps."
  exit 1
fi

t="UBOONE_SUITE_$tag"
if [ x$branch = x ]; then
  echo "Will make suite tag $t on current revision."
else
  echo "Will make suite tag $t on branch $branch."
fi

# Loop over git repositories in $MRB_SOURCE

for gitdir in $MRB_SOURCE/*/.git
do
  repodir=`dirname $gitdir`
  repo=`basename $repodir`
  if [[ $repo =~ ^ub ]]; then
    echo "Tagging $repo"
    cd $repodir
    if [ x$branch != x ]; then
      echo "Checking out branch $branch"
      git checkout $branch
    fi
    if [ $dryrun -eq 0 ]; then
      git tag -a -m"Uboone suite $v" $force $t
    fi
    if [ $push -ne 0 ]; then
      git push origin --tags $force
    fi
  else
    echo "Ignoring $repo"
  fi
done
