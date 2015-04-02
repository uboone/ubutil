#!/bin/sh
#######################################################
# This script is not for general users; 
# if used will result in authentication errors;
# This is mainly used for official validation 
# process, meant to be run from the uboonepro account!
# This script generates all the requisite root files
# and .gif files and stores them in the right places
# for access by the html scripts for the webpage.
#######################################################
# USAGE: sh runVal.sh larsoft_version 
# Example: sh runVal.sh v04_03_00
#######################################################

if [ $1 = "" ] 
then
   echo "Please specify a larsoft version and rerun...exiting!"	
   exit 0   
fi

echo "Running Momresolution.py ...."
python Momresolution.py --dataset singlemu --input /uboone/data/uboonepro/validation/singlemu/$1/singlemu_isotropic_anahist.root --dir /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/
echo "Running hit.py ...."
python hit.py --dataset singlemu --input /uboone/data/uboonepro/validation/singlemu/$1/singlemu_isotropic_anahist.root --dir /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/
echo "Running flash.py ...."
python flash.py --dataset singlemu --input /uboone/data/uboonepro/validation/singlemu/$1/singlemu_isotropic_anahist.root --dir /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/
echo "Running trackingeff.py ...."
python trackingeff.py --dataset singlemu --input /uboone/data/uboonepro/validation/singlemu/$1/singlemu_isotropic_anahist.root --dir /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/
echo "Running pid.py ...."
python pid.py --dataset singlemu --input /uboone/data/uboonepro/validation/singlemu/$1/singlemu_isotropic_anahist.root --dir /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/
echo "Running calorimetry.py ...."
python calorimetry.py --dataset singlemu --input /uboone/data/uboonepro/validation/singlemu/$1/singlemu_isotropic_anahist.root --dir /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/

python makeplots.py --hit --input /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/hit.root --dir /afs/fnal.gov/files/expwww/microboone/html/css/validation/singlemu/$1 
python makeplots.py --flash --input /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/flash.root --dir /afs/fnal.gov/files/expwww/microboone/html/css/validation/singlemu/$1 
python makeplots.py --pid --input /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/pid.root --dir /afs/fnal.gov/files/expwww/microboone/html/css/validation/singlemu/$1 
python makeplots.py --tracking --input /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/tracking.root --dir /afs/fnal.gov/files/expwww/microboone/html/css/validation/singlemu/$1 
python makeplots.py --momresol --input /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/momresol.root --dir /afs/fnal.gov/files/expwww/microboone/html/css/validation/singlemu/$1 
python makeplots.py --calorimetry --input /uboone/data/uboonepro/validation/singlemu/$1/rootfiles/calorimetry.root --dir /afs/fnal.gov/files/expwww/microboone/html/css/validation/singlemu/$1




