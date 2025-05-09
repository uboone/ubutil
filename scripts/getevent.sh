#! /bin/bash
VER=""
Run=0
Event=0
FCL=swizzler_reco_anatree_art.fcl
LOCAL=
while [ $# -gt 0 ]; do
    case "$1" in

    # Interactive flag.
    -h|--help )
      echo getevent.sh --version v05_01_02 --run 4670 --event 662 [--fcl swizzle_software_trigger_streams.fcl --local local.tar]
      exit 0
      ;;

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

     # fcl file
     --fcl )
       if [ $# -gt 1 ]; then
	    FCL=$2
	    shift
	fi
	;;

     # local product tarball
     --local )
       if [ $# -gt 1 ]; then
	    LOCAL=$2
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
echo Event=$Event

#kx509
source /grid/fermiapp/products/uboone/setup_uboone.sh
setup uboonecode $VER -q e9:prof
if [ -n "$LOCAL" ]; then
    mkdir localProducts
    cp $LOCAL localProducts
    file=`basename $LOCAL`
    cd localProducts
    tar -xf $file
    cd -
    sed "s@setenv MRB_INSTALL.*@setenv MRB_INSTALL `pwd`/localProducts@" localProducts/setup | \
    sed "s@setenv MRB_TOP.*@setenv MRB_TOP `pwd`@" > localProducts/setup.local
    . localProducts/setup.local
    mrbslp
fi
ups active
rawfile=`samweb list-files "run_number=$Run and first_event<=$Event and last_event>=$Event and data_tier=raw and file_format=binaryraw-uncompressed"`
echo rawfile=$rawfile
ifdh cp `samweb get-file-access-url $rawfile` .
#echo $[ $Event%50-1 ]
nskip=$[ $Event%50-1 ]
if [ $nskip -eq -1 ]; then
    nskip=49
fi
ART_DEBUG_CONFIG=cfg.fcl lar -c $FCL $rawfile --nskip $nskip -n 1
echo "lar -c $FCL $rawfile --nskip $nskip -n 1 >& lar.out"
lar -c $FCL $rawfile --nskip $nskip -n 1 >& lar.out
rm -f $rawfile
rm -rf localProducts
