#!/bin/bash
#pick flux files from fluxdir, ifdh cp them to the current folder, untar them, move the files to the appropriate names

set -x #turn echo on
fluxdir=/pnfs/uboone/persistent/users/mibass/corsika/sqShowers



#list of file lables, manually defined for now
fnums=("001002" "003004" "005006" "007008" "009010" "011012" "013014" "015016" "017018" "019020" "021022" "023024" "025026" "027028" "029030" "031032" "033034" "035036" "037038" "039040" "041042" "043044" "045046" "047048" "049050" "051052" "053054" "055056" "057058" "059060" "061062" "063064" "065066" "067068" "069070" "071072" "073074" "075076" "077078" "079080" "081082" "083084" "085086" "087088" "089090" "091092" "093094" "095096" "097098" "099100")


# Seed random generator, use process for repeatability otherwise time
# Note: PROCESS is set if we are running on a grid node
if [ -z "$PROCESS" ]; then
  RANDOM=$$$(date +%s);
else
  RANDOM=${PROCESS};
fi
  

selfnum=${fnums[$RANDOM % ${#fnums[@]} ]}
f1=$fluxdir/p_showers_$selfnum.tgz
f2=$fluxdir/He_showers_$selfnum.tgz
f3=$fluxdir/N_showers_$selfnum.tgz
f4=$fluxdir/Mg_showers_$selfnum.tgz
f5=$fluxdir/Fe_showers_$selfnum.tgz


echo Picking files $f1 $f2 $f3 $f4 $f5
ifdh cp -D $f1 $f2 $f3 $f4 $f5 ./

for f in $f1 $f2 $f3 $f4 $f5
do
  fname=$(basename "$f")
  tar xzf $fname
  mv ${fname/.tgz/}.db ${fname/_$selfnum.tgz/}.db
done
