#!/bin/bash
declare -a list_test=(`ls $UBOONECODE_DIR/job/`)

arraylength=${#list_test[@]}

curdir=`pwd`

echo "Checking a total of ${arraylength} files... "

for (( i=1; i<${arraylength}+1; i++ ));
do
    echo "File ${i} : " ${list_test[$i-1]}
    test=`fhicl-dump ${list_test[$i-1]}`
    cmd="source /cvmfs/uboone.opensciencegrid.org/products/setup_uboone.sh >& /dev/null; cd $curdir; setup uboonecode ${UBOONECODE_VERSION} -qe17:prof >& /dev/null; fhicl-dump ${list_test[$i-1]}"
    fix=`ssh -f $(hostname) "${cmd}"`
    out=`diff -u <(echo "${test}") <(echo "${fix}")`    
    
    if [[ $out = *[!\ ]* ]]; then       
	printf "${list_test[$i-1]} changed :\n ${out} \n " &>> changed.txt
    fi
done

echo "Difference can be found in changed.txt"    

