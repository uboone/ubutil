# We distinguish executable and non-executable .py files.
# The former are installed with execute permission in bin area (which is on python path).
# The latter are installed without execute permission in python area.

# Executable python files.

LIST(APPEND exes calorimetry.py makeplots.py )

# Non-executable python modules that we want to be on PYTHONPATH.

LIST(APPEND nonexes validation_utilities.py )

message(STATUS "Executable python modules ${exes}")
message(STATUS "Non-executable python modules ${nonexes}")

install(FILES ${nonexes} DESTINATION ${product}/${version}/python)
install_scripts(LIST ${exes})
