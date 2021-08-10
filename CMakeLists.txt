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


cmake_minimum_required(VERSION 3.19 FATAL_ERROR)

project(ubutil LANGUAGES CXX)

# cetbuildtools contains our cmake modules
find_package(cetbuildtools REQUIRED)

list(APPEND CMAKE_MODULE_PATH $ENV{ART_DIR}/Modules)

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
find_ups_product( fhiclcpp )
find_ups_product( cetlib )
find_ups_product( cetlib_except )



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

# FCL module
add_subdirectory(fclmodule)

# Root batch framework.
add_subdirectory(root_batch)

# Root analysis modules.
add_subdirectory(root_analyze)

# packaging utility
include(UseCPack)

