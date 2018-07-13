#! /bin/bash

#--------------------------------------------------------------------------
#
# Name: split_uboonecode2.sh
#
# Purpose: Split/refactor uboonecode repository.
#
# Usage:
#
# split_uboonecode2.sh [-h|--help]
#
# Options:
#
# -h|--help            - Print help
#
# This script performs the following tasks.
#
# 1.  Clone and rename the uboonecode repository.
#
# 2.  Delete content contained in other split repositories (basically
#     everything in subdirectories "uboone" and "ubooneobj").
#
# 3.  Generate new product_deps and CMakeLists.txt files.
#
#
#--------------------------------------------------------------------------

# Help function.

function dohelp {
  echo "Usage: split_uboonecode2.sh [-h|--help]"
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

# Set dependencies.

cmake_deps="art larcore lardata larevt larsim larreco gsl"
ups_deps="larsoft ubcv ubcrt ublite ubutil uboonedata genie_xsec"

# Make sure $MRB_SOURCE is defined, and go there.

if [ x$MRB_SOURCE = x ]; then
  echo "Environment variable MRB_SOURCE is not defined."
  exit 1
fi

if [ ! -d $MRB_SOURCE ]; then
  echo "Directory $MRB_SOURCE does not exist."
  exit 1
fi

cd $MRB_SOURCE

# Set the name of the new repository.

repo=uboonecode

# Delete existing repo directory, if any.

if [ -d $repo ]; then
  rm -rf $repo
fi
if [ -d $repo ]; then
  echo "Directory $repo not deleted."
  exit 1
fi

# Check out the unrefactored branch of uboonecode

cd $MRB_SOURCE/uboonecode.orig
git checkout $ubr

# Extract the uboonecode and larsoft version and qualifiers.

uboonecode_version=`grep 'parent.*uboonecode' ups/product_deps | awk '{print $3}'`
uboonecode_qual=`grep defaultqual ups/product_deps | awk '{print $2}'`
cet_version=`grep cetbuildtools ups/product_deps | grep -v qualifier | awk '{print $2}'`
cd $MRB_SOURCE

# Clone uboonecode into new repo.

repodir=$MRB_SOURCE/$repo
git clone file://$MRB_SOURCE/uboonecode.orig/.git $repodir
cd $repodir

# Directories that we want to delete.

deldirs="uboone ubooneobj"

# Now scrub the repo.

git checkout $ubr
#git filter-branch -f --prune-empty --index-filter "git rm -rf --cached --ignore-unmatch $deldirs" HEAD | grep -i rewrite
#rm -rf .git/refs/original
#rm -rf .git-rewrite
git rm -rf $deldirs

# Don't follow upstream any more.

  # Reset origin.

  git branch --unset-upstream $ubr
  git remote remove origin
  git remote add origin ssh://p-uboonecode@cdcvs.fnal.gov/cvs/projects/uboonecode
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
find_ups_product( ubevt )
find_ups_product( larcorealg )
find_ups_product( larcoreobj )
find_ups_product( lardataobj )
EOF
for dep in ${cmake_deps}
do
  echo "find_ups_product( $dep v1_00_00 )" >> CMakeLists.txt
done
cat <<EOF >> CMakeLists.txt
find_ups_product( cetbuildtools v3_10_00 )
find_ups_boost( v1_53_0 )
find_ups_product( canvas )

cet_find_library( GSLCBLAS NAMES gslcblas PATHS ENV GSL_LIB NO_DEFAULT_PATH )

# macros for dictionary and simple_plugin
include(ArtDictionary)
include(ArtMake)
include(BuildPlugins)

# ADD SOURCE CODE SUBDIRECTORIES HERE
add_subdirectory(fcl)
add_subdirectory(test)
add_subdirectory(tools)
add_subdirectory(releaseDB)

# ups - table and config files
add_subdirectory(ups)

# packaging utility
include(UseCPack)
EOF

git add CMakeLists.txt

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
fwdir   product_dir scripts

# table fragment to set FW_SEARCH_PATH
table_fragment_begin
pathPrepend(FHICL_FILE_PATH, .:./job)
table_fragment_end

# With "product  version" table below, we now define depdendencies

# Add the dependent product and version

product                 version
EOF
for dep in ${ups_deps}; do
  if [ -d $MRB_SOURCE/$dep ]; then
    v=`grep '^parent' $MRB_SOURCE/$dep/ups/product_deps | awk '{print $3}'`
  elif [ $dep = uboonedata ]; then
    v=v01_18_10
  else
    v=`ups depend uboonecode $uboonecode_version -q ${uboonecode_qual}:prof | sed -n "s;^[ |_]*\(${dep} "'[_0-9a-z]*\).*$;\1;p' | awk '{print $2}'`
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
for dep in ${ups_deps}; do
  printf "%-15s" $dep >> ups/product_deps
done
echo >> ups/product_deps
for qual in c2:debug c2:opt c2:prof c2:prof:fg e15:debug e15:opt e15:prof e15:prof:fg; do
  printf "%-15s" $qual >> ups/product_deps
  for dep in ${ups_deps}; do
    thisqual=`echo $qual | cut -d: -f-2`
    fgqual=`echo $qual | cut -d: -f3`
    if [ $dep = genie_xsec ]; then
      if [ x$fgqual = xfg ]; then
        thisqual=LocalFGNievesQEAndMEC
      else
        thisqual=DefaultPlusMECWithNC
      fi
    fi
    if [ $dep = uboonedata ]; then
      thisqual='-nq-'
    fi
    extra_quals=''
    printf "%-15s" ${thisqual} >> ups/product_deps
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
    sed 's;uboone/MicroBooNEPandora;ubana/MicroBooNEPandora;' $f > ${f}.temp
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
    sed 's;uboone/LLBasicTool;ubana/LLBasicTool;' $f > ${f}.temp
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

  # Done updating.
    
  cd $repodir
  git commit -a -m "Import from uboonecode."

# Done updating.
    
cd $repodir
git commit -a -m "Import from uboonecode."

# Create a new branch post_split

git checkout -b split_test

# Update the master CMakeLists.txt

cd $MRB_SOURCE
mv uboonecode.orig .uboonecode.orig
mrb uc
mv .uboonecode.orig uboonecode.orig
