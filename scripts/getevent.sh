#!/bin/bash
VER=""
Run=0
Event=0

while [ $# -gt 0 ]; do
    case "$1" in

      # version.
      --version )
	if [ $# -gt 1 ]; then
	    VER=$2
	    shift
	fi
	;;      
	
      # run
      --run )
	if [ $# -gt 1 ]; then
	    Run=$2
	    shift
	fi
	;;

     # event
     --event )
       if [ $# -gt 1 ]; then
	    Event=$2
	    shift
	fi
	;;

    # Other.
    * )
      echo "Unknown option $1"
      exit 1
  esac
  shift
done

echo VER=$VER
echo Run=$Run
echo SubRun=$SubRun
echo Event=$Event

#kx509
source /grid/fermiapp/products/uboone/setup_uboone.sh
setup uboonecode $VER -q e9:prof
rawfile=`samweb list-files "run_number=$Run and first_event<=$Event and last_event>=$Event and data_tier=raw and file_format=binaryraw-uncompressed"`
echo rawfile=$rawfile
ifdh cp `samweb get-file-access-url $rawfile` .
#echo $[ $Event%50-1 ]
nskip=$[ $Event%50-1 ]
if [ $nskip -eq -1 ]; then
    nskip=49
fi
lar -c swizzler_reco_anatree_art.fcl $rawfile --nskip $nskip -n 1 >& lar.out
rm -f $rawfile
