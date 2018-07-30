#! /bin/bash

#--------------------------------------------------------------------------
#
# Name: split_uboonecode.sh
#
# Purpose: Split/refactor uboonecode repository.
#
# Usage:
#
# split_uboonecode.sh [-h|--help]
#
# Options:
#
# -h|--help     - Print help
#
# This script performs the following tasks.
#
# 1.  Split the uboonecode git repository by cloning, renaming and pruning
#     unneeded content from the cloned repositories content.
#
# 2.  Do various automatic updates to include files, CMakeLists.txt, and
#     product_deps files.
#
#--------------------------------------------------------------------------

# Help function.

function dohelp {
  echo "Usage: split_uboonecode.sh [-h|--help]"
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

# Branch containing unrefactored uboonecode content.

ubr=feature/greenlee_split

# Make variables to hold refactored repo structure.

declare -a repos       # List of refactored repositories.
declare -a paths       # Corresponding paths within uboonecode (space-separated list).
declare -a cmake_deps  # Dependencies for cmake (space-separated list).
declare -a ups_deps    # Dependencies ups/product_deps (space-separated list).

# Fill dependency tree.

repos[0]="ubobj"
cmake_deps[0]="artdaq_core"
ups_deps[0]="lardataobj larcorealg artdaq_core"

repos[1]="ubcore"
cmake_deps[1]="ubobj lardata art"
ups_deps[1]="ubobj lardata"

repos[2]="ubraw"
cmake_deps[2]="ubcore ifdh_art larevt lardata uboonedaq_datatypes art"
ups_deps[2]="ubcore larevt uboonedaq_datatypes"

repos[3]="ubevt"
cmake_deps[3]="ubcore ifdh_art larevt gsl art"
ups_deps[3]="ubcore larevt"

repos[4]="ubsim"
cmake_deps[4]="ubevt larsim art"
ups_deps[4]="ubevt larsim"

repos[5]="ubreco"
cmake_deps[5]="ubsim larreco swtrigger art"
ups_deps[5]="ubsim larreco swtrigger"

repos[6]="ubana"
cmake_deps[6]="ubreco ubraw larana larpandora art"
ups_deps[6]="ubreco ubraw larana larpandora"

repos[7]="ublite"
cmake_deps[7]="ubana larana larpandora larlite art"
ups_deps[7]="ubana larpandora larlite"

repos[8]="ubcrt"
cmake_deps[8]="ubobj lardata artdaq_core ifdh_art gallery art"
ups_deps[8]="ubobj lardata gallery"

repos[9]="ubcv"
cmake_deps[9]="ubevt larevt larcv art"
ups_deps[9]="ubevt larcv larlite"

#repos[10]="ubxsec"
#cmake_deps[10]="ublite larana larpandora larlite"
#ups_deps[10]="ublite larpandora larlite"


# Make sure $MRB_SOURCE is defined, and go there.

if [ x$MRB_SOURCE = x ]; then
  echo "Environment variable MRB_SOURCE is not defined."
  exit 1
fi

if [ ! -d $MRB_SOURCE ]; then
  echo "Directory $MRB_SOURCE does not exist."
  exit 1
fi

# Delete all directories in $MRB_SOURCE except uboonecode.

find $MRB_SOURCE -maxdepth 1 -type d \! -name srcs \! -name uboonecode.orig \! -name ubutil -print | while read dir
do
  echo "Deleting $dir"
  rm -rf $dir
  if [ -d $dir ]; then
    echo "Directory $dir not deleted."
    exit 1
  fi
done

# Delete all installed products.

rm -rf $MRB_INSTALL/ub*

# Check out the unrefactored branch of uboonecode

cd $MRB_SOURCE/uboonecode.orig
git checkout $ubr

# Extract the uboonecode and larsoft version and qualifiers.

uboonecode_version=`grep 'parent.*uboonecode' ups/product_deps | awk '{print $3}'`
uboonecode_qual=`grep defaultqual ups/product_deps | awk '{print $2}'`
cet_version=`grep cetbuildtools ups/product_deps | grep -v qualifier | awk '{print $2}'`
cd $MRB_SOURCE

# Loop over directories in uboonecode repository that we might want to migrate 
# to a different repository.

rm -rf /tmp/dirs.txt
find $MRB_SOURCE/uboonecode.orig -maxdepth 2 -type d \( -name .git -prune -o -name tools -prune -o -name test -prune -o -name fcl -prune -o -true \) \! -name ups \! -name .git \! -name releaseDB \! -name fcl \! -name test \! -name uboonecode.orig \! -name tools \! -name uboone -print -name ubooneobj -prune > /tmp/dirs.txt
for dir in `cat /tmp/dirs.txt`
do
  dirname=`basename $dir`
  dirdir=`dirname $dir`
  dirbase=`basename $dirdir`
  dirpath=$dirname
  if [ $dirbase != uboonecode.orig ]; then
    dirpath=$dirbase/$dirname
  fi
  echo "Directory path ${dirpath}."

  # Figure out which repo we want to migrate this directory to.

  repo=''
  if [ $dirname = ubooneobj ]; then
    repo=ubobj
  elif [ $dirname = BeamAna ]; then
    repo=ubraw
  elif [ $dirname = BeamDAQ ]; then
    repo=ubraw
  elif [ $dirname = BeamData ]; then
    repo=ubraw
  elif [ $dirname = RawData ]; then
    repo=ubraw
  elif [ $dirname = CRT ]; then
    repo=ubcrt
  elif [ $dirname = CalData ]; then
    repo=ubevt
  elif [ $dirname = Calibrations ]; then
    repo=ubana
  elif [ $dirname = CosmicTagging ]; then
    repo=ubana
  elif [ $dirname = DQMTools ]; then
    repo=ubcore
  elif [ $dirname = DataOverlay ]; then
    repo=ubevt
  elif [ $dirname = DataScanner ]; then
    repo=none
  elif [ $dirname = Database ]; then
    repo=ubevt
  elif [ $dirname = DetSim ]; then
    repo=ubsim
  elif [ $dirname = EventGenerator ]; then
    repo=ubcore
  elif [ $dirname = EventWeight ]; then
    repo=ubsim
  elif [ $dirname = FakeNEWS ]; then
    repo=none
  elif [ $dirname = Geometry ]; then
    repo=ubcore
  elif [ $dirname = LArCVImageMaker ]; then
    repo=ubcv
  elif [ $dirname = LArG4 ]; then
    repo=ubsim
  elif [ $dirname = LLApp ]; then
    repo=ubana
  elif [ $dirname = LLBasicTool ]; then
    repo=ubcore
  elif [ $dirname = LLSelectionTool ]; then
    repo=ubana
  elif [ $dirname = LiteMaker ]; then
    repo=ublite
  elif [ $dirname = MichelReco ]; then
    repo=ubreco
  elif [ $dirname = MicroBooNEPandora ]; then
    repo=ubreco
  elif [ $dirname = MicroBooNEWireCell ]; then
    repo=ubana
  elif [ $dirname = MuCS ]; then
    repo=ubreco
  elif [ $dirname = OpticalDetectorAna ]; then
    repo=ubana
  elif [ $dirname = OpticalDetectorSim ]; then
    repo=ubsim
  elif [ $dirname = PatternFilter ]; then
    repo=ubana
  elif [ $dirname = PhotonPropagation ]; then
    repo=ubsim
  elif [ $dirname = RecoDemo ]; then
    repo=none
  elif [ $dirname = SNStreamSim ]; then
    repo=ubsim
  elif [ $dirname = Simulation ]; then
    repo=ubsim
  elif [ $dirname = SpaceCharge ]; then
    repo=ubevt
  elif [ $dirname = SpaceChargeServices ]; then
    repo=ubevt
  elif [ $dirname = T0Reco ]; then
    repo=ubreco
  elif [ $dirname = TPCNeutrinoIDFilter ]; then
    repo=ubana
  elif [ $dirname = ChargedTrackMultiplicity ]; then
    repo=ubana
  elif [ $dirname = LEEPhotonAnalysis ]; then
    repo=ubana
  elif [ $dirname = UBXSec ]; then
    repo=ubana
  elif [ $dirname = TriggerSim ]; then
    repo=ubcore
  elif [ $dirname = UBFlashFinder ]; then
    repo=ubreco
  elif [ $dirname = Utilities ]; then
    repo=ubevt
  elif [ $dirname = BurstNoiseMetrics ]; then
    repo=ubcore
  elif [ $dirname = DLFilters ]; then
    repo=ubcore
  elif [ $dirname = QuietEventFilter ]; then
    repo=ubcore
  elif [ $dirname = AnalysisTree ]; then
    repo=ubana
  else
    echo "Don't know what to do with $dirname."
    exit 1
  fi

  # Find index of this repo.

  found=0
  for i in ${!repos[@]}; do
    if [ ${repos[$i]} = $repo ]; then
      paths[$i]="${paths[$i]} $dirpath"
      found=1
    fi
  done

  if [ $found -eq 0 ]; then
    echo "No repository $repo"
  fi

done

echo "Paths:"
echo ${paths[*]}

# Loop over repositories.

for i in ${!repos[@]}; do
  repo=${repos[$i]}
  echo $repo
  pths=${paths[$i]}

  # Clone uboonecode into new repo.

  repodir=$MRB_SOURCE/$repo
  git clone file://$MRB_SOURCE/uboonecode.orig/.git $repodir
  cd $repodir

  # Loop over directories that are candidates for deletion.

  deldirs=''
  rm -f /tmp/dirs.txt
  find $repodir -maxdepth 2 -type d \( -name .git -prune -o -true \) \! -name .git \! -name ups \! -name uboone -print \( -name fcl -prune -o -name test -prune -o -name tools -prune -o -path \*/ubobj/ubooneobj -prune \) > /tmp/dirs.txt
  for dir in `cat /tmp/dirs.txt`
  do
    keep=0
    if [ $dir = $repodir ]; then
      keep=1
    fi
    for pth in $pths; do
      if [ $dir = $repodir/$pth ]; then
        keep=1
      fi
    done

    if [ $keep -eq 0 ]; then
      delpth=`echo $dir | sed "s;$repodir/;;"`
      deldirs="$deldirs $delpth"
    fi

  done

  # Now scrub the repo.

  git checkout $ubr
  #git filter-branch -f --prune-empty --index-filter "git rm -rf --cached --ignore-unmatch $deldirs" HEAD | grep -i rewrite
  #rm -rf .git/refs/original
  #rm -rf .git-rewrite
  git rm -rf $deldirs

  # Move subdirectories to where they are supposed to be.

  if [ ! -d $repo ]; then
    mkdir $repo
  fi

  for subdir in uboone/* ubooneobj/*
  do
    if [ -d $subdir ]; then
      subdirname=`basename $subdir`
      mv $subdir $repo
      git add $repo/$subdirname
    fi
  done

  git rm -rf uboone
  git rm -rf ubooneobj

  # Reset origin.

  git branch --unset-upstream $ubr
  git remote remove origin
  git remote add origin ssh://p-${repo}@cdcvs.fnal.gov/cvs/projects/$repo
  git fetch origin

  # Make a default top level CMakeLists.txt.

  cat <<EOF > CMakeLists.txt
# ======================================================================
#  larsoft main build file
#
#  cd .../path/to/build/directory
#  source .../path/to/larsoft/ups/setup_for_development <-d|-p>
#  cmake [-DCMAKE_INSTALL_PREFIX=/install/path]
#        -DCMAKE_BUILD_TYPE=\$CETPKG_TYPE
#        \$CETPKG_SOURCE
#  make
#  make test
#  make install
#  make package (builds distribution tarfile)
# ======================================================================

# use cmake 2.8 or later
cmake_minimum_required (VERSION 2.8)

project($repo)

# cetbuildtools contains our cmake modules
SET ( CETBUILDTOOLS_VERSION \$ENV{CETBUILDTOOLS_VERSION} )
IF (NOT CETBUILDTOOLS_VERSION)
    MESSAGE (FATAL_ERROR "ERROR: setup cetbuildtools to get the cmake modules")
ENDIF()


set(CMAKE_MODULE_PATH \$ENV{CANVAS_ROOT_IO_DIR}/Modules
		      \$ENV{CETBUILDTOOLS_DIR}/Modules
		      \${CMAKE_MODULE_PATH})

include(CetCMakeEnv)
cet_cmake_env()

cet_set_compiler_flags(DIAGS CAUTIOUS
  WERROR
  NO_UNDEFINED
  ALLOW_DEPRECATIONS
  EXTRA_FLAGS -pedantic -Wno-unused-local-typedefs
)

cet_report_compiler_flags()

# these are minimum required versions, not the actual product versions
find_ups_product( larcorealg )
find_ups_product( larcoreobj )
find_ups_product( lardataobj )
find_ups_product( cetbuildtools v3_10_00 )
find_ups_boost( v1_53_0 )
find_ups_product( canvas )
EOF
  for dep in ${cmake_deps[$i]}
  do
    echo "find_ups_product( $dep v1_00_00 )" >> CMakeLists.txt
  done

  if [ $repo = ubraw ]; then
    echo 'cet_find_library( UBDut NAMES ubdata_types PATHS $ENV{UBOONEDAQ_DATATYPES_LIB} )' >> CMakeLists.txt
  fi
  if [ $repo = ubevt ]; then
    echo 'cet_find_library( GSL NAMES gsl PATHS ENV GSL_LIB NO_DEFAULT_PATH )' >> CMakeLists.txt
  fi
  if [ $repo = ubreco ]; then
    echo 'find_library( SWTRIG_LIBBASE NAMES SWTriggerBase PATHS $ENV{SWTRIGGER_LIBDIR} )' >> CMakeLists.txt
    echo 'find_library( SWTRIG_LIBFEMU NAMES FEMBeamTrigger PATHS $ENV{SWTRIGGER_LIBDIR} )' >> CMakeLists.txt
  fi

  cat <<EOF >> CMakeLists.txt

# macros for dictionary and simple_plugin
include(ArtDictionary)
EOF
  if [ $repo = ubobj ]; then
    cat <<EOF >> CMakeLists.txt
include(CetMake)
EOF
  else
    cat <<EOF >> CMakeLists.txt
include(ArtMake)
include(BuildPlugins)
EOF
  fi
  cat <<EOF >> CMakeLists.txt

# ADD SOURCE CODE SUBDIRECTORIES HERE
add_subdirectory($repo)
EOF
  if [ $repo != ubobj ]; then
    cat <<EOF >> CMakeLists.txt

# Unit tests.
add_subdirectory(test)
EOF
  fi
  cat <<EOF >> CMakeLists.txt

# ups - table and config files
add_subdirectory(ups)

# packaging utility
include(UseCPack)
EOF

  git add CMakeLists.txt

  # Make a second level CMakeLists.txt

  if [ $repo != ubooonebj ]; then
    for subdir in $repo/* ;do
      subdirname=`basename $subdir`
      echo "add_subdirectory(${subdirname})" >> $repo/CMakeLists.txt
    done
  fi
  git add $repo/CMakeLists.txt

  # Generate a fresh product_deps

  cat <<EOF > ups/product_deps
# This @product_deps@ file defines dependencies for this package. 

# The *parent* line must the first non-commented line and defines this product and version
# The version must be of the form vxx_yy_zz (e.g. v01_02_03)
parent $repo $uboonecode_version

defaultqual $uboonecode_qual

# These optional lines define where headers, libraries, and executables go and should
# be used only if your product does not conform to the defaults.
# Format: directory_type directory_path directory_name
#   where directory_type is one of incdir, libdir, or bindir
#   where directory_path is one of product_dir, fq_dir and - 
# Defaults:
# incdir  product_dir  include
# fcldir  product_dir  fcl
# libdir  fq_dir       lib
# bindir  fq_dir       bin
#
fcldir  product_dir job
EOF
  if [ $repo = ubcore ]; then
    echo 'gdmldir product_dir gdml' >> ups/product_deps
  fi
  cat <<EOF >> ups/product_deps
fwdir   product_dir scripts

# table fragment to set FW_SEARCH_PATH
table_fragment_begin
EOF
  if [ $repo = ubana ]; then
    echo 'pathPrepend(FW_SEARCH_PATH, ${UBANA_DIR}/scripts)' >> ups/product_deps
  fi
  if [ $repo = ublite ]; then
    echo 'pathPrepend(FW_SEARCH_PATH, ${UBLITE_DIR}/scripts)' >> ups/product_deps
  fi
  if [ $repo = ubcore ]; then
    echo 'pathPrepend(FW_SEARCH_PATH, ${UBCORE_DIR}/gdml)' >> ups/product_deps
  fi
  cat <<EOF >> ups/product_deps
table_fragment_end

# With "product  version" table below, we now define depdendencies

# Add the dependent product and version

product                 version
EOF
  for dep in ${ups_deps[$i]}; do
    if [ -d $MRB_SOURCE/$dep ]; then
      v=`grep '^parent' $MRB_SOURCE/$dep/ups/product_deps | awk '{print $3}'`
    else
      v=`ups depend uboonecode $uboonecode_version -q ${uboonecode_qual}:prof | sed -n "s;^[ |_]*\(${dep} "'[_0-9a-z]*\).*$;\1;p' | awk '{print $2}' | sort -u`
    fi
    if [ x$v = x ]; then
      echo "No version for ${dep}."
      pwd
      exit
    fi
    printf "%-24s%s\n" $dep $v >> ups/product_deps
  done
  cat <<EOF >> ups/product_deps
cetbuildtools	        $cet_version	-	only_for_build
end_product_list

EOF

  printf "%-15s" qualifier >> ups/product_deps
  for dep in ${ups_deps[$i]}; do
    printf "%-15s" $dep >> ups/product_deps
  done
  echo >> ups/product_deps
  for qual in c2:debug c2:opt c2:prof e15:debug e15:opt e15:prof; do
    printf "%-15s" $qual >> ups/product_deps
    for dep in ${ups_deps[$i]}; do
      extra_quals=''
      if [ $dep = artdaq_core -o $dep = ifdh_art ]; then
        extra_quals=":s70"
      fi
      printf "%-15s" ${qual}${extra_quals} >> ups/product_deps
    done
    echo >> ups/product_deps
  done
  echo "end_qualifier_list" >> ups/product_deps

  cat <<EOF >> ups/product_deps

# Preserve tabs and formatting in emacs and vi / vim:

### Local Variables:
### tab-width: 8
### End:
EOF

  # Make a copy of test_fcl

  if [ $repo != ubobj ]; then
    cd $repodir
    mkdir -p test/test_fcl
    echo "add_subdirectory(test_fcl)" > test/CMakeLists.txt
    echo "cet_test( test_fcl_${repo}.sh PREBUILT )" > test/test_fcl/CMakeLists.txt
    sed "s/uboonecode/${repo}/" $MRB_SOURCE/uboonecode.orig/test/test_fcl/test_fcl_uboonecode.sh > test/test_fcl/test_fcl_${repo}.sh
    chmod +x test/test_fcl/test_fcl_${repo}.sh
    git add test
  fi

  # Fix classes_def.xml

  cd $repodir

  find . -type f -name classes_def.xml -exec grep -l 'include.*ubooneobj/Trigger' {} \; | while read f
  do
    sed 's;ubooneobj/Trigger;ubobj/Trigger;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  # Fix includes.

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/CRT' {} \; | while read f
  do
    sed 's;ubooneobj/CRT;ubobj/CRT;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/DataOverlay' {} \; | while read f
  do
    sed 's;ubooneobj/DataOverlay;ubobj/DataOverlay;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/MuCS' {} \; | while read f
  do
    sed 's;ubooneobj/MuCS;ubobj/MuCS;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/Optical' {} \; | while read f
  do
    sed 's;ubooneobj/Optical;ubobj/Optical;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/RawData' {} \; | while read f
  do
    sed 's;ubooneobj/RawData;ubobj/RawData;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/Trigger' {} \; | while read f
  do
    sed 's;ubooneobj/Trigger;ubobj/Trigger;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"ubooneobj/UBXSec' {} \; | while read f
  do
    sed 's;ubooneobj/UBXSec;ubobj/UBXSec;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/RawData' {} \; | while read f
  do
    sed 's;uboone/RawData;ubraw/RawData;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/TriggerSim' {} \; | while read f
  do
    sed 's;uboone/TriggerSim;ubcore/TriggerSim;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done
    
  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/Geometry' {} \; | while read f
  do
    sed 's;uboone/Geometry;ubcore/Geometry;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/DQMTools' {} \; | while read f
  do
    sed 's;uboone/DQMTools;ubcore/DQMTools;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/CalData' {} \; | while read f
  do
    sed 's;uboone/CalData;ubevt/CalData;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/Utilities' {} \; | while read f
  do
    sed 's;uboone/Utilities;ubevt/Utilities;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/DataOverlay' {} \; | while read f
  do
    sed 's;uboone/DataOverlay;ubevt/DataOverlay;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/Database' {} \; | while read f
  do
    sed 's;uboone/Database;ubevt/Database;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/SpaceCharge' {} \; | while read f
  do
    sed 's;uboone/SpaceCharge;ubevt/SpaceCharge;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/SpaceChargeServices' {} \; | while read f
  do
    sed 's;uboone/SpaceChargeServices;ubevt/SpaceChargeServices;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/EventWeight' {} \; | while read f
  do
    sed 's;uboone/EventWeight;ubsim/EventWeight;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/OpticalDetectorSim' {} \; | while read f
  do
    sed 's;uboone/OpticalDetectorSim;ubsim/OpticalDetectorSim;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/SNStreamSim' {} \; | while read f
  do
    sed 's;uboone/SNStreamSim;ubsim/SNStreamSim;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/DetSim' {} \; | while read f
  do
    sed 's;uboone/DetSim;ubsim/DetSim;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/LArG4' {} \; | while read f
  do
    sed 's;uboone/LArG4;ubsim/LArG4;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/PhotonPropagation' {} \; | while read f
  do
    sed 's;uboone/PhotonPropagation;ubsim/PhotonPropagation;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/Simulation' {} \; | while read f
  do
    sed 's;uboone/Simulation;ubsim/Simulation;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/MichelReco' {} \; | while read f
  do
    sed 's;uboone/MichelReco;ubreco/MichelReco;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/MuCS' {} \; | while read f
  do
    sed 's;uboone/MuCS;ubreco/MuCS;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/T0Reco' {} \; | while read f
  do
    sed 's;uboone/T0Reco;ubreco/T0Reco;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/UBFlashFinder' {} \; | while read f
  do
    sed 's;uboone/UBFlashFinder;ubreco/UBFlashFinder;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/AnalysisTree' {} \; | while read f
  do
    sed 's;uboone/AnalysisTree;ubana/AnalysisTree;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/ChargedTrackMultiplicity' {} \; | while read f
  do
    sed 's;uboone/ChargedTrackMultiplicity;ubana/ChargedTrackMultiplicity;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/Calibrations' {} \; | while read f
  do
    sed 's;uboone/Calibrations;ubana/Calibrations;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/CosmicTagging' {} \; | while read f
  do
    sed 's;uboone/CosmicTagging;ubana/CosmicTagging;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/LEEPhotonAnalysis' {} \; | while read f
  do
    sed 's;uboone/LEEPhotonAnalysis;ubana/LEEPhotonAnalysis;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/MicroBooNEPandora' {} \; | while read f
  do
    sed 's;uboone/MicroBooNEPandora;ubreco/MicroBooNEPandora;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/MicroBooNEWireCell' {} \; | while read f
  do
    sed 's;uboone/MicroBooNEWireCell;ubana/MicroBooNEWireCell;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/OpticalDetectorAna' {} \; | while read f
  do
    sed 's;uboone/OpticalDetectorAna;ubana/OpticalDetectorAna;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/PatternFilter' {} \; | while read f
  do
    sed 's;uboone/PatternFilter;ubana/PatternFilter;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^ *\#include.*"uboone/TPCNeutrinoIDFilter' {} \; | while read f
  do
    sed 's;uboone/TPCNeutrinoIDFilter;ubana/TPCNeutrinoIDFilter;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/UBXSec' {} \; | while read f
  do
    sed 's;uboone/UBXSec;ubana/UBXSec;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/LLBasicTool' {} \; | while read f
  do
    sed 's;uboone/LLBasicTool;ubcore/LLBasicTool;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/LLApp' {} \; | while read f
  do
    sed 's;uboone/LLApp;ubana/LLApp;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/LLSelectionTool' {} \; | while read f
  do
    sed 's;uboone/LLSelectionTool;ubana/LLSelectionTool;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/LiteMaker' {} \; | while read f
  do
    sed 's;uboone/LiteMaker;ublite/LiteMaker;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  find . -type f -name '*.[hc]*' -exec grep -l '^\#include.*"uboone/CRT' {} \; | while read f
  do
    sed 's;uboone/CRT;ubcrt/CRT;' $f > ${f}.temp
    mv -f ${f}.temp $f
  done

  # Fix CMakeLists.txt

  find . -type f -name CMakeLists.txt | while read f
  do
    sed 's;ubooneobj_CRT;ubobj_CRT;' $f | \
    sed 's;ubooneobj_DataOverlay;ubobj_DataOverlay;' | \
    sed 's;ubooneobj_MuCS;ubobj_MuCS;' | \
    sed 's;ubooneobj_Optical;ubobj_Optical;' | \
    sed 's;ubooneobj_RawData;ubobj_RawData;' | \
    sed 's;ubooneobj_Trigger;ubobj_Trigger;' | \
    sed 's;ubooneobj_UBXSec;ubobj_UBXSec;' | \
    sed 's;uboone_Geometry;ubcore_Geometry;' | \
    sed 's;uboone_DQMTools;ubcore_DQMTools;' | \
    sed 's;uboonecode_uboone_TriggerSim;ubcore_TriggerSim;' | \
    sed 's;uboonecode_uboone_FakeNEWS;ubcore_FakeNEWS;' | \
    sed 's;uboone_RawData;ubraw_RawData;' | \
    sed 's;uboone_CalData;ubevt_CalData;' | \
    sed 's;uboone_DataOverlay;ubevt_Overlay;' | \
    sed 's;uboone_Database;ubevt_Database;' | \
    sed 's;uboone_SpaceCharge;ubevt_SpaceCharge;' | \
    sed 's;uboone_SpaceChargeServices;ubevt_SpaceChargeServices;' | \
    sed 's;uboone_Utilities;ubevt_Utilities;' | \
    sed 's;uboone_SNStreamSim_Fmwk;ubsim_SNStreamSim_Fmwk;' | \
    sed 's;uboone_SNStreamSim_Algo;ubsim_SNStreamSim_Algo;' | \
    sed 's;uboone_EventWeight_Calculators;ubsim_EventWeight_Calculators;' | \
    sed 's;uboone_EventWeight_Calculators_BNBPrimaryHadron;ubsim_EventWeight_Calculators_BNBPrimaryHadron;' | \
    sed 's;uboone_MichelReco_Fmwk;ubreco_MichelReco_Fmwk;' | \
    sed 's;uboone_MichelReco_Algo;ubreco_MichelReco_Algo;' | \
    sed 's;uboone_LEEPreCutAlgo.so;ubana_LEEPreCutAlgo.so;' | \
    sed 's;uboone_OpticalDetectorAna;ubana_OpticalDetectorAna;' | \
    sed 's;uboone_AnalysisTree_MCTruth_MCTruthBase;ubana_AnalysisTree_MCTruth_MCTruthBase;' | \
    sed 's;uboone_AnalysisTree_AssociationsTruth_tool;ubana_AnalysisTree_AssociationsTruth_tool;' | \
    sed 's;uboone_AnalysisTree_BackTrackerTruth_tool;ubana_AnalysisTree_BackTrackerTruth_tool;' | \
    sed 's;uboone_AnalysisTree_;ubana_AnalysisTree_;' | \
    sed 's;uboone_PatternFilter_PMAlgs;ubana_PatternFilter_PMAlgs;' | \
    sed 's;uboonecode_uboone_Calibrations;ubana_Calibrations;' | \
    sed 's;uboonecode_uboone_BasicTool_GeoAlgo;ubana_BasicTool_GeoAlgo;' | \
    sed 's;uboonecode_uboone_SelectionTool_OpT0FinderBase;ubana_SelectionTool_OpT0FinderBase;' | \
    sed 's;uboonecode_uboone_SelectionTool_OpT0FinderAlgorithms;ubana_SelectionTool_OpT0FinderAlgorithms;' | \
    sed 's;uboonecode_uboone_CosmicTagging_CosmicTaggingAlgorithms;ubana_CosmicTagging_CosmicTaggingAlgorithms;' | \
    sed 's;uboone_LEEPhotonAnalysis;ubana_LEEPhotonAnalysis;' | \
    cat > ${f}.temp
    mv -f ${f}.temp $f      
  done

  # Fix fcls.

  if [ $repo = ubcrt ]; then
    find . -type f -name \*.fcl | while read fcl
    do
      sed 's;uboone/CRT;ubcrt/CRT;' $fcl > ${fcl}.temp
      mv -f ${fcl}.temp $fcl
      git add 
    done
  fi
  if [ $repo = ubana ]; then
    find . -type f -name \*.fcl | while read fcl
    do
      sed 's;uboone/AnalysisTree;ubana/AnalysisTree;' $fcl > ${fcl}.temp
      mv -f ${fcl}.temp $fcl
    done
  fi

  # Done updating.
    
  cd $repodir
  git commit -a -m "Import from uboonecode."

done

# Update the master CMakeLists.txt

cd $MRB_SOURCE
mv uboonecode.orig .uboonecode.orig
mrb uc
mv .uboonecode.orig uboonecode.orig
