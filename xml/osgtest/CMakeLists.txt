FILE(GLOB xml_files *.xml)
install(FILES ${xml_files} DESTINATION xml/osgtest)
install_source( EXTRAS ${xml_files} )
