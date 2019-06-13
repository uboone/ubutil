# ======================================================================
#  larsoft main build file
#
#  cd .../path/to/build/directory
#  source .../path/to/larsoft/ups/setup_for_development <-d|-p>
#  cmake [-DCMAKE_INSTALL_PREFIX=/install/path]
#        -DCMAKE_BUILD_TYPE=$CETPKG_TYPE
#        $CETPKG_SOURCE
#  make
#  make test
#  make install
#  make package (builds distribution tarfile)
# ======================================================================


# use cmake 2.8 or later
cmake_minimum_required (VERSION 2.8)

project(ubutil)

# cetbuildtools contains our cmake modules
SET ( CETBUILDTOOLS_VERSION $ENV{CETBUILDTOOLS_VERSION} )
IF (NOT CETBUILDTOOLS_VERSION)
    MESSAGE (FATAL_ERROR "ERROR: setup cetbuildtools to get the cmake modules")
ENDIF()

set(CMAKE_MODULE_PATH $ENV{CETBUILDTOOLS_DIR}/Modules
		      ${CMAKE_MODULE_PATH})

include(CetCMakeEnv)
cet_cmake_env()

set_install_root()

# -Wno-register is not recognized by e15
if( ${qualifier} STREQUAL "e17" )
cet_set_compiler_flags(DIAGS CAUTIOUS
  WERROR
  NO_UNDEFINED
  EXTRA_FLAGS -pedantic -Wno-error=register -Wno-register
)
else()
cet_set_compiler_flags(DIAGS CAUTIOUS
  WERROR
  NO_UNDEFINED
  EXTRA_FLAGS -pedantic
)
endif()


cet_report_compiler_flags()

# these are minimum required versions, not the actual product versions
find_ups_product( art )
find_ups_product( cetbuildtools )



# macros for dictionary and simple_plugin
include(ArtMake)
include(BuildPlugins)

# ADD SOURCE CODE SUBDIRECTORIES HERE

# subdirectory for test code
add_subdirectory(test)

# ups - table and config files
add_subdirectory(ups)

# XML project files.
add_subdirectory(xml)

# Scripts and utilities.
add_subdirectory(scripts)

# Python modules.
add_subdirectory(python)

# Validation scripts
add_subdirectory(validation)

# Tools (programs)
add_subdirectory(tools)

## fclmodule is available from fhiclcpp
## We remove it from here since the copy in fhiclcpp 
## already knows how to find either python 2 or python 3 properly.
# FCL module
##add_subdirectory(fclmodule)

# Root batch framework.
add_subdirectory(root_batch)

# Root analysis modules.
add_subdirectory(root_analyze)

# packaging utility
include(UseCPack)

