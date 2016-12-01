#! /bin/bash
#--------------------------------------------------------------------
#
# Name: fclpath.sh
#
# Purpose: Print fcl path corresponding to a particular release of uboonecode.
#
# Usage: fclpath.sh <version>
#
# Options:
#
# -h|--help - Print help.
# -q <qual> - Ups qualifiers.
#
# Arguments:
#
# <version> - Uboonecode version.
#
#--------------------------------------------------------------------

# Clean environment.

[ "$HOME" != "" ] && exec -c $0 $@

# When we get to here, the environment has been cleaned.
# Do some basic initialization.

source /etc/bashrc
source /grid/fermiapp/products/uboone/setup_uboone.sh > /dev/null 2> /dev/null

# Help function.

function dohelp {
  echo "Usage: fclpath.sh [-h|--help] [-q <qual>] <version>"
  exit
}

# Parse arguments.

qual=''
version=''

while [ $# -gt 0 ]; do
  case "$1" in

  # Help.

  -h|--help )
    dohelp
    exit
    ;;

  -q )
    if [ $# -gt 1 ]; then
      qual=$2
      shift
    fi
    ;;

  * )
    if [ x$version = x ]; then
      version=$1
    else
      echo "Too many arguments."
      dohelp
      exit 1
    fi
  esac
  shift
done

# Check arguments.

if [ x$version = x ]; then
  echo "No version specified."
  dohelp
  exit 1
fi

if [ x$qual = x ]; then
  echo "No qualifier specified."
  dohelp
  exit 1
fi

setup uboonecode -q $qual $version
echo $FHICL_FILE_PATH | sed 's;\.[^:]*:;;g'
