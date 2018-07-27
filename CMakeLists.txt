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

set(CMAKE_MODULE_PATH $ENV{CANVAS_DIR}/Modules
		      $ENV{CETBUILDTOOLS_DIR}/Modules
		      ${CMAKE_MODULE_PATH})

include(CetCMakeEnv)
cet_cmake_env()

set_install_root()

cet_set_compiler_flags(DIAGS CAUTIOUS
  WERROR
  NO_UNDEFINED
  EXTRA_FLAGS -pedantic
)

cet_report_compiler_flags()

# these are minimum required versions, not the actual product versions
find_ups_product( art )
find_ups_product( cetbuildtools )



# macros for dictionary and simple_plugin
include(ArtDictionary)
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

# FCL module
## skip fclmodule until it is updated for e17
if( ${qualifier} STREQUAL "e17" )
  message(STATUS "UBUTIL: skipping fclmodule for the e17 build")
else()
add_subdirectory(fclmodule)
endif()

# Root batch framework.
add_subdirectory(root_batch)

# Root analysis modules.
add_subdirectory(root_analyze)

# packaging utility
include(UseCPack)

