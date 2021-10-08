FILE(GLOB xml_files *.xml)
install(FILES ${xml_files} DESTINATION xml/v1_00_02)
install_source( EXTRAS ${xml_files} )
