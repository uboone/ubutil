# modernize finding python
find_package(Python COMPONENTS Interpreter Development)

cet_make_library(
  LIBRARY_NAME fcl
  SOURCE fclmodule.cxx
  LIBRARIES
  fhiclcpp::fhiclcpp
  Python::Python
)
set_target_properties(fcl PROPERTIES PREFIX "" SUFFIX ".so")

install_source()
