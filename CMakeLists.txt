# ======================================================================
#  ubutil main build file
#
#  cd .../path/to/build/directory
#  source .../path/to/lardataobj/ups/setup_for_development <-d|-p>
#  buildtool [-I /install/path] -bt[i] -jN
# ======================================================================

cmake_minimum_required(VERSION 3.20 FATAL_ERROR)

find_package(cetmodules REQUIRED)
project(ubutil VERSION 10.07.00 LANGUAGES CXX)

include(CetCMakeEnv)
cet_cmake_env()

cet_set_compiler_flags(DIAGS CAUTIOUS
  WERROR
  NO_UNDEFINED
  EXTRA_FLAGS -pedantic
)

cet_report_compiler_flags(REPORT_THRESHOLD VERBOSE)

find_package(art REQUIRED EXPORT )

# macros for dictionary and simple_plugin
include(ArtMake)
include(BuildPlugins)

# ADD SOURCE CODE SUBDIRECTORIES HERE

# subdirectory for test code
add_subdirectory(test)

# XML project files.
#add_subdirectory(xml)

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

cet_cmake_config()
