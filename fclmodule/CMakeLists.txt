# fix required for c7 and e19 with python 2
# also fine with c2 and e17
cet_add_compiler_flags(CXX -Wno-register )

find_package(PythonInterp REQUIRED)
find_package(PythonLibs REQUIRED)

include_directories(${PYTHON_INCLUDE_DIRS})

art_make( LIBRARY_NAME fcl
	  LIB_LIBRARIES fhiclcpp
	  		cetlib
			cetlib_except
			${PYTHON_LIBRARIES} )
set_target_properties(fcl PROPERTIES PREFIX "" SUFFIX ".so")

install_source()
