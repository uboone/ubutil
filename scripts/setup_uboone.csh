# Source this file to set the basic configuration needed by LArSoft 
# and for the uBooNE-specific software that interfaces to LArSoft.

set FERMIAPP_LARSOFT_DIR = "/grid/fermiapp/products/larsoft/"
set FERMIOSG_LARSOFT_DIR = "/cvmfs/fermilab.opensciencegrid.org/products/larsoft/"
set OASIS_LARSOFT_DIR = "/cvmfs/oasis.opensciencegrid.org/fermilab/products/larsoft/"

set FERMIAPP_UBOONE_DIR = "/grid/fermiapp/products/uboone/"
set FERMIOSG_UBOONE_DIR = "/cvmfs/uboone.opensciencegrid.org/products/"
set OASIS_UBOONE_DIR = "/cvmfs/oasis.opensciencegrid.org/microboone/products/"

set UBOONE_BLUEARC_DATA = "/uboone/data/"

# Set up ups for LArSoft
# Sourcing this setup will add larsoft and common to $PRODUCTS

foreach dir ( $FERMIAPP_LARSOFT_DIR $FERMIOSG_LARSOFT_DIR $OASIS_LARSOFT_DIR )
  if ( -f $dir/setup ) then
    echo "Setting up larsoft UPS area... ${dir}"
    set prod_db = $dir
    source $dir/setup
    set common = `dirname $dir`/common/db
    if ( -d $common ) then
      setenv PRODUCTS `dropit -p $PRODUCTS common/db`:`dirname $dir`/common/db
    endif
    break
  endif
end

# Set up ups for uBooNE

foreach dir ( $FERMIAPP_UBOONE_DIR $FERMIOSG_UBOONE_DIR $OASIS_UBOONE_DIR )
  if ( -f $dir/setup ) then
    echo "Setting up uboone UPS area... ${dir}"
    set prod_db = $dir
    source $dir/setup
    break
  endif
end

# Add uBooNE path to FW_SEARCH_PATH
#
if ( -d "${UBOONE_BLUEARC_DATA}" ) then
    if ( $?FW_SEARCH_PATH ) then
	setenv FW_SEARCH_PATH ${UBOONE_BLUEARC_DATA}:${FW_SEARCH_PATH}
    else
	setenv FW_SEARCH_PATH ${UBOONE_BLUEARC_DATA}
    endif
endif

# Set up the basic tools that will be needed
#
if ( `uname` != Darwin ) then

  # Work around git table file bugs.

  setenv PATH `dropit git`
  setenv LD_LIBRARY_PATH `dropit -p $LD_LIBRARY_PATH git`
  setup git
endif
setup gitflow
setup mrb

# Define the value of MRB_PROJECT. This can be used
# to drive other set-ups.
# We need to set this to 'larsoft' for now.
#
setenv MRB_PROJECT larsoft

# Define environment variables that store the standard experiment name.

setenv JOBSUB_GROUP uboone
setenv EXPERIMENT uboone
setenv SAM_EXPERIMENT uboone
