include_directories( $ENV{PYTHON_INCLUDE} )

find_library(PYTHON NAMES python2.7 PATHS $ENV{PYTHON_LIB})

set( CMAKE_SHARED_LIBRARY_PREFIX "" )
art_make( LIBRARY_NAME fclmodule 
	  LIB_LIBRARIES ${FHICLCPP}
	  		cetlib
	  		${PYTHON} )

install_source()
