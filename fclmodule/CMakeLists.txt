# fix required for c7 (clang 7.0.0)
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
cet_add_compiler_flags(CXX -Wno-register )
endif()

include_directories( $ENV{PYTHON_INCLUDE} )

find_library(PYTHON NAMES python2.7 PATHS $ENV{PYTHON_LIB})

set( CMAKE_SHARED_LIBRARY_PREFIX "" )
art_make( LIBRARY_NAME fclmodule 
	  LIB_LIBRARIES ${FHICLCPP}
	  		cetlib
			cetlib_except
	  		${PYTHON} )

install_source()
