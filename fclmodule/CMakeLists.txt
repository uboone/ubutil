# fix required for c7 and e19 with python 2
# also fine with c2 and e17
cet_add_compiler_flags(CXX -Wno-register )

include_directories( $ENV{PYTHON_INCLUDE} )

SET ( PYTHON_VERSION $ENV{PYTHON_VERSION} )
if(PYTHON_VERSION MATCHES v3)
  find_library(PYTHON NAMES python3.8m PATHS $ENV{PYTHON_LIB})
else()
  find_library(PYTHON NAMES python2.7 PATHS $ENV{PYTHON_LIB})
endif()

set( CMAKE_SHARED_LIBRARY_PREFIX "" )
art_make( LIBRARY_NAME fcl
	  LIB_LIBRARIES ${FHICLCPP}
	  		cetlib
			cetlib_except
	  		${PYTHON} )

install_source()
