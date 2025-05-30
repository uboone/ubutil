# Source this file to set the basic configuration needed by LArSoft 
# and for the uBooNE-specific software that interfaces to LArSoft.

FERMIOSG_COMMON_DIR="/cvmfs/fermilab.opensciencegrid.org"
FERMIOSG_LARSOFT_DIR="/cvmfs/larsoft.opensciencegrid.org"
FERMIOSG_UBOONE_DIR="/cvmfs/uboone.opensciencegrid.org"
UBOONE_BLUEARC_DATA="/exp/uboone/data"

# Make sure locale is reasonable.

if [ x$LC_ALL = x ]; then
  echo "Setting LC_ALL=C"
  export LC_ALL=C
fi

# Make sure jobsub_lite environment is initialized.
# This normally happens by sourcing the system /etc/bashrc

if [ -d /opt/jobsub_lite ]; then
  if ! echo $PATH | grep -q jobsub_lite; then

    # Don't let jobsub initialization override the value of $JOBSUB_AUTH_METHODS, if set.

    save_auth=$JOBSUB_AUTH_METHODS
    source /etc/bashrc
    if [ x$save_auth != x ]; then
      export JOBSUB_AUTH_METHODS=$save_auth
    fi
    unset save_auth
  fi
fi

# Do SL7 and AL9 specific initializations

eval `grep PRETTY_NAME /etc/os-release`   # Define $PRETTY_NAME
echo $PRETTY_NAME
if echo $PRETTY_NAME | grep -q "Scientific Linux"; then

  # Do SL7-specific initializations (ups).

  for dir in $FERMIOSG_LARSOFT_DIR/products
  do
    if [[ -f $dir/setup ]]; then
      echo "Setting up larsoft UPS area... ${dir}"
      source $dir/setup
      break
    fi
  done

  # Set up ups for uBooNE

  for dir in $FERMIOSG_UBOONE_DIR/products
  do
    if [[ -f $dir/setup ]]; then
      echo "Setting up uboone UPS area... ${dir}"
      source $dir/setup
      break
    fi
  done

  # Add fermilab common products to $PRODUCTS.

  for dir in $FERMIOSG_COMMON_DIR/products/common/db
  do
    if [[ -d $dir ]]; then
      echo "Setting up fermilab common UPS area... $dir"
      export PRODUCTS=`dropit -p $PRODUCTS $dir`:$dir
      break
    fi
  done

  # Set up the basic ups tools.

  setup mrb
  setup gh
  setup ubtools

  # End if SL7-specific section.

else

  # Do AL9-specific initializations.
  # Initialize spack.
  # Temporarily initialize the larsoft spack instance as the head instance.
  # This will get updated to the uboonecode spack instance when a uboonecode instance exists.

  #source /cvmfs/larsoft.opensciencegrid.org/spack-packages/setup-env.sh

  # Initialize ups-for-AL9 for use with certain null-flavored ups products.

  source /cvmfs/fermilab.opensciencegrid.org/products/common/etc/setup
  source /cvmfs/uboone.opensciencegrid.org/products/setup
  source /cvmfs/larsoft.opensciencegrid.org/products/setup

fi

# Add current working directory (".") to FW_SEARCH_PATH
#
if [[ -n "${FW_SEARCH_PATH}" ]]; then
  FW_SEARCH_PATH=`echo $FW_SEARCH_PATH | tr : '\n' | grep -v '\.' | head -c -1 | tr '\n' :`
  export FW_SEARCH_PATH=.:${FW_SEARCH_PATH}
else
  export FW_SEARCH_PATH=.
fi

# Add uBooNE data path to FW_SEARCH_PATH
#
if [[ -d "${UBOONE_BLUEARC_DATA}" ]]; then

    if [[ -n "${FW_SEARCH_PATH}" ]]; then
      FW_SEARCH_PATH=`echo $FW_SEARCH_PATH | tr : '\n' | grep -v $UBOONE_BLUEARC_DATA | head -c -1 | tr '\n' :`
      export FW_SEARCH_PATH=${UBOONE_BLUEARC_DATA}:${FW_SEARCH_PATH}
    else
      export FW_SEARCH_PATH=${UBOONE_BLUEARC_DATA}
    fi

fi

# Add cvmfs bin directory to execute path.
#
if [[ -d "${FERMIOSG_UBOONE_DIR}/bin" ]]; then

    PATH=`echo $PATH | tr : '\n' | grep -v ${FERMIOSG_UBOONE_DIR}/bin | head -c -1 | tr '\n' :`
    export PATH=${PATH}:${FERMIOSG_UBOONE_DIR}/bin

fi

# Define the value of MRB_PROJECT. This can be used
# to drive other set-ups. 
# We need to set this to 'larsoft' for now.

export MRB_PROJECT=larsoft

# Define environment variables that store the standard experiment name.

export JOBSUB_GROUP=uboone
export EXPERIMENT=uboone     # Used by ifdhc
export SAM_EXPERIMENT=uboone

# Define samweb server environment variable.

export IFDH_BASE_URI="https://samuboone.fnal.gov:8483/sam/uboone/api"

# For Art workbook

#export ART_WORKBOOK_OUTPUT_BASE=/exp/uboone/data/users
#export ART_WORKBOOK_WORKING_BASE=/exp/uboone/app/users
#export ART_WORKBOOK_QUAL="s2:e5:nu"
