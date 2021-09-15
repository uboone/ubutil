# All of the .py files in this directory are python modules.
# We distinguish executable and non-executable .py files.
# The former are installed with execute permission.
# The latter are installed without execute permission.

# Executable python files.

LIST(APPEND exes lar.py )

# Non-executable python files.

LIST(APPEND nonexes root_analyze.py cint_analyze.py )

message(STATUS "Executable python modules ${exes}")
message(STATUS "Non-executable python modules ${nonexes}")

install(FILES ${nonexes} DESTINATION python)
install_scripts(LIST ${exes})
