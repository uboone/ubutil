# fix required for c7 and e19 with python 2
# also fine with c2 and e17
cet_add_compiler_flags(CXX -Wno-register )

include_directories( $ENV{PYTHON_INCLUDE} )

#find_library(PYTHON NAMES python2.7 PATHS $ENV{PYTHON_LIB})
find_library(PYTHON NAMES python3.7 PATHS $ENV{PYTHON_LIB})

set( CMAKE_SHARED_LIBRARY_PREFIX "" )
art_make( LIBRARY_NAME fclmodule 
	  LIB_LIBRARIES ${FHICLCPP}
	  		cetlib
			cetlib_except
	  		${PYTHON} )

install_source()
