#! /bin/bash

#--------------------------------------------------------------------------
#
# Name: clean_repo_history.sh
#
# Purpose: Clean up history of refactored uboonecode repositories.
#
# Usage:
#
# clean_repo_history.sh [-h|--help] [--repo <repo>]
#
# Options:
#
# -h|--help     - Print help
# --repo <repo> - Specify repository (by default do all repos in $MRB_SOURCE).
#
#--------------------------------------------------------------------------

# Help function.

function dohelp {
  echo "Usage: clean_repo_history.sh [-h|--help]"
}

# Parse command line.

repos=''

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      dohelp
      exit
      ;;

    # Specify repository.
    --repo )
      if [ $# -gt 1 ]; then
        repos=$2
        shift
      fi
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

if [ x$repos = x ]; then
  while read dir
  do
    d=`dirname $dir`
    dd=`basename $d`
    if [ $dd != uboonecode.orig -a $dd != uboonecode ]; then
      repos="$dd $repos"
    fi
  done < <( ls -d $MRB_SOURCE/*/.git )
fi

# Loop over repos.

for repo in $repos
do
  echo "Cleaning $repo"

  # Make a list of subdirectories in the original repo that contain data products.

  proddirs=''
  if [ $repo = ubobj ]; then
    proddirs="OpticalDetectorAna RawData CRT MuCS DataOverlay UBFlashFinder UBXSec"
  fi

  # Make a list of subdirectories in the original repo that are candidates for deletion.

  noproddirs=''
  while read d
  do
    dir1=`echo $d | sed "s;$MRB_SOURCE/uboonecode.orig/uboone/;;"`
    dir2=`echo $dir1/ | cut -d/ -f1`
    if [ x$dir2 != x ]; then
      if echo $proddirs | grep -vq $dir2; then
        if echo $noproddirs | grep -vq $dir2; then
          noproddirs="$noproddirs $dir2"
        fi
      fi
    fi
  done < <(find $MRB_SOURCE/uboonecode.orig/uboone \( -name .git -prune -o -true \) -type d )

  # Loop over no-product directories and see if the corrsponding directory exists in the
  # refactored repo.

  deldirs=''
  for dir in $noproddirs
  do
    n=`find $MRB_SOURCE/$repo \( -name .git -prune -o -true \) -type d -name $dir | wc -l`
    if [ $n -eq 0 ]; then
      deldirs="$deldirs uboone/$dir"
    fi
  done

  # If this repo doesn't have a fcl directory, remove fcl history.

  if [ ! -d $MRB_SOURCE/$repo/fcl ]; then
    deldirs="$deldirs fcl"
  fi

  # Delete some legacy directories.

  if [ $repo != ublite ]; then
    deldirs="$deldirs Algorithms DataTypes HitCosmicTag Modules Utils Base arxiv job UBXSec README.md DoxyFile .gitmodules .travis.yml generateDocumentationAndDeploy.sh MyPandoraHelper.h MyPandoraHelper.cxx"
  fi

  if [ $repo != uboonecode ]; then
    deldirs="$deldirs test/ci test/CRTMerge test/CRTSwizzle test/DataProduction test/EventGenerator test/Geometry test/OverlayProduction test/Production test/SpaceCharge test/SparseRawDigits test/RecoObjects test/Swizzle"
  fi

  if [ $repo != ubobj ]; then
    deldirs="$deldirs ubooneobj"
  fi

  # Filter out deleted directories.

  cd $MRB_SOURCE/$repo
  pwd
  rm -rf .git-rewrite
  git filter-branch -f --prune-empty --index-filter "git rm -rf --cached --ignore-unmatch $deldirs" HEAD | grep -v '^rm'
  #git filter-branch -f --prune-empty --tree-filter "rm -rf $deldirs" HEAD
  rm -rf .git/refs/original
  git reflog expire --expire=now --all
  git gc --aggressive --prune=now

  # Create new branches develop and master.

  git checkout -b master
  git checkout -b develop

done
