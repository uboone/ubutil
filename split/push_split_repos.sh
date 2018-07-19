#! /bin/bash

#--------------------------------------------------------------------------
#
# Name: push_split_repos.sh
#
# Purpose: Wipe and push and tag split uboonecode repositories.
#
# Usage:
#
# push_split_repos.sh [-h|--help]
#
# Options:
#
# -h|--help     - Print help
#
#--------------------------------------------------------------------------

# Help function.

function dohelp {
  echo "Usage: push_split_repos.sh [-h|--help]"
}

# Parse command line.

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      dohelp
      exit
      ;;

    # Other (error).
    * )
      echo "Unknown option $1."
      dohelp
      exit 1
      ;;

  esac
  shift
done

# Make variables to hold refactored repo structure.

declare -a repos       # List of refactored repositories.

# Define repos.

repos[0]="ubobj"
repos[1]="ubcore"
repos[2]="ubraw"
repos[3]="ubevt"
repos[4]="ubsim"
repos[5]="ubreco"
repos[6]="ubana"
repos[7]="ublite"
repos[8]="ubcrt"
repos[9]="ubcv"

# Make sure $MRB_SOURCE is defined, and go there.

if [ x$MRB_SOURCE = x ]; then
  echo "Environment variable MRB_SOURCE is not defined."
  exit 1
fi

if [ ! -d $MRB_SOURCE ]; then
  echo "Directory $MRB_SOURCE does not exist."
  exit 1
fi

# Loop over repositories.

for i in ${!repos[@]}; do
  repo=${repos[$i]}
  echo "Processing ${repo}"
  cd $MRB_SOURCE/$repo

  # Get tag.

  v=`grep ^parent ups/product_deps | awk '{print $3}'`
  echo "Version $v"

  if git checkout master; then
    echo "git checkout master successful."
  else
    git checkout -b master
    echo "Created branch master."
  fi
  git push --delete origin master |& grep -v warn
  git push -u origin master
  git tag -a -m$v $v -f
  git push origin $v -f
  if git checkout develop; then
    echo "git checkout develop successful."
  else
    git checkout -b develop
    echo "Created branch develop."
  fi
  git push --delete origin develop |& grep -v warn
  git push -u origin develop
done
