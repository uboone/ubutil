# Source this file to set the basic configuration needed by LArSoft 
# and for the uBooNE-specific software that interfaces to LArSoft.

# Set up ups for LArSoft
# Sourcing this setup will add /grid/fermiapp/products/larsoft and
# /grid/fermiapp/products/common to $PRODUCTS
#


set OASIS_LARSOFT_DIR = /cvmfs/oasis.opensciencegrid.org/fermilab/products/larsoft/
set FERMIAPP_LARSOFT_DIR = /grid/fermiapp/products/larsoft/
set OASIS_UBOONE_DIR = /cvmfs/oasis.opensciencegrid.org/microboone/products/
set FERMIAPP_UBOONE_DIR = /grid/fermiapp/products/uboone/
set FERMIAPP_COMMON_DIR = /grid/fermiapp/products/
set UBOONE_BLUEARC_DATA = /uboone/data

if ( -d "${FERMIAPP_LARSOFT_DIR}" ) then
    echo "Setting up the Grid Fermiapp larsoft UPS area...${FERMIAPP_LARSOFT_DIR}"
    source ${FERMIAPP_LARSOFT_DIR}/setups
    setenv PRODUCTS ${PRODUCTS}:/grid/fermiapp/products/common/db
else if ( -d "${OASIS_LARSOFT_DIR}" ) then
    echo "Setting up the OASIS Fermilab UPS area...${OASIS_LARSOFT_DIR}"
    source ${OASIS_LARSOFT_DIR}/setups
    setenv PRODUCTS ${PRODUCTS}:/grid/fermiapp/products/common/db
endif

if ( -d "${FERMIAPP_UBOONE_DIR}" ) then
    echo "Setting up the Grid Fermiapp uboone UPS area...${FERMIAPP_UBOONE_DIR}"
    source ${FERMIAPP_UBOONE_DIR}/setups
else if ( -d "${OASIS_UBOONE_DIR}" ) then
    echo "Setting up the OASIS uboone UPS area...${OASIS_UBOONE_DIR}"
    source ${OASIS_UBOONE_DIR}/setups
endif

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
