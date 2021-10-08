FILE(GLOB xml_files *.xml)
install(FILES ${xml_files} DESTINATION xml/mcc6.0)
install_source( EXTRAS ${xml_files} )
