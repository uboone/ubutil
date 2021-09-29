# All of the .py files in this directory are python modules.
# Install without execute permission.

FILE(GLOB python_modules *.py)

install(FILES ${python_modules} DESTINATION python)
