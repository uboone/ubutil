#!/bin/bash

if [ x$FHICL_FILE_PATH = x ]; then
  echo "***************************************"
  echo "Variable FHICL_FILE_PATH not found."
  echo "You porbably haven't set up larsoft yet,"
  echo "Try 'setup uboonecode vXX_XX_XX -q e10:prof"
  echo "OR 'mrbsetenv'"
  echo "***************************************"
  exit 1

fi

FHICL_SEARCH_FILE=$1

if [ x$FHICL_SEARCH_FILE = x ]; then
  echo "***************************************"
  echo "USAGE: find_fhicl <fhicl file name>."
  echo "Note that \$FHICL_FILE_PATH must be defined."
  echo "Try 'setup uboonecode vXX_XX_XX -q e10:prof"
  echo "OR 'mrbsetenv' if it isn't"
  echo "***************************************"
  exit 1


fi

SEARCH_PATHS=(`awk '{split($0,array,":"); for (a in array)  printf "%s ", array[a]; printf "\n";}' <<< $FHICL_FILE_PATH`)
CHECKED_WORKING_DIR=0
for elt in ${SEARCH_PATHS[*]};
do
  
  #skipc local dirs autmoatically added to the path but do not exist
 #echo $CHECKED_WORKING_DIR
 if [ ! -d "$elt" ]; then
   continue
 fi
 
 # also, check the current working dir (".") only once. For whatever reason, it gets added to $FHICL_SEARCH_FILE a bunch... 
 
 #echo $elt 
 FOUND_FHICL=`find $elt -name $FHICL_SEARCH_FILE`
 
 if [ -n "$FOUND_FHICL" ]; then
   echo "*******************"
   echo "Found fhicl file(s):"
    
   awk -F:" " '{printf "%s \n", $1}' <<< $FOUND_FHICL
 fi
    
done
