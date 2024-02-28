# Source this file to set the basic configuration needed by LArSoft 
# and for the uBooNE-specific software that interfaces to LArSoft.

FERMIOSG_COMMON_DIR="/cvmfs/fermilab.opensciencegrid.org/products/common/db"

FERMIOSG_LARSOFT_DIR="/cvmfs/larsoft.opensciencegrid.org/products/"

FERMIOSG_UBOONE_DIR="/cvmfs/uboone.opensciencegrid.org/products/"

UBOONE_BLUEARC_DATA="/exp/uboone/data/"

# Make sure locale is reasonable.

if [ x$LC_ALL = x ]; then
  echo "Setting LC_ALL=C"
  export LC_ALL=C
fi

# Sourcing this setup will add larsoft to $PRODUCTS

for dir in $FERMIOSG_LARSOFT_DIR
do
  if [[ -f $dir/setup ]]; then
    echo "Setting up larsoft UPS area... ${dir}"
    source $dir/setup
    break
  fi
done

# Set up ups for uBooNE

for dir in $FERMIOSG_UBOONE_DIR
do
  if [[ -f $dir/setup ]]; then
    echo "Setting up uboone UPS area... ${dir}"
    source $dir/setup
    break
  fi
done

# Add fermilab common products to $PRODUCTS.

for dir in $FERMIOSG_COMMON_DIR
do
  if [[ -d $dir ]]; then
    echo "Setting up fermilab common UPS area... $dir"
    export PRODUCTS=`dropit -p $PRODUCTS $dir`:$dir
    break
  fi
done

# Add current working directory (".") to FW_SEARCH_PATH
#
if [[ -n "${FW_SEARCH_PATH}" ]]; then
  FW_SEARCH_PATH=`dropit -e -p $FW_SEARCH_PATH .`
  export FW_SEARCH_PATH=.:${FW_SEARCH_PATH}
else
  export FW_SEARCH_PATH=.
fi

# Add uBooNE data path to FW_SEARCH_PATH
#
if [[ -d "${UBOONE_BLUEARC_DATA}" ]]; then

    if [[ -n "${FW_SEARCH_PATH}" ]]; then
      FW_SEARCH_PATH=`dropit -e -p $FW_SEARCH_PATH ${UBOONE_BLUEARC_DATA}`
      export FW_SEARCH_PATH=${UBOONE_BLUEARC_DATA}:${FW_SEARCH_PATH}
    else
      export FW_SEARCH_PATH=${UBOONE_BLUEARC_DATA}
    fi

fi

# Set up the basic tools that will be needed
#
if [ `uname` != Darwin ]; then

  # Work around git table file bugs.

  export PATH=`dropit git`
  if [ x$LD_LIBRARY_PATH != x ]; then
    export LD_LIBRARY_PATH=`dropit -p $LD_LIBRARY_PATH git`
  fi
  setup git
fi
setup gitflow
setup mrb v4_04_06
setup ubtools

# Define the value of MRB_PROJECT. This can be used
# to drive other set-ups. 
# We need to set this to 'larsoft' for now.

export MRB_PROJECT=larsoft

# Define environment variables that store the standard experiment name.

export JOBSUB_GROUP=uboone
export EXPERIMENT=uboone     # Used by ifdhc
export SAM_EXPERIMENT=uboone

# For Art workbook

#export ART_WORKBOOK_OUTPUT_BASE=/exp/uboone/data/users
#export ART_WORKBOOK_WORKING_BASE=/exp/uboone/app/users
#export ART_WORKBOOK_QUAL="s2:e5:nu"