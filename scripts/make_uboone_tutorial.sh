#! /bin/bash
#----------------------------------------------------------------------
#
# Name: make_uboont_tutorial.sh
#
# Purpose:
#       Setup a tutorial enviorment for uboone grid running and analysis
#       This script is intended to be added to and modify as time goes on
#       
#       
# Usage:
#
#      Just run it! No options at the moment. 
#
#----------------------------------------------------------------------

# Parse arguments.

rs=$UBOONECODE_VERSION
rr1=$UBOONECODE_VERSION
rr2=$UBOONECODE_VERSION
userdir=$USER
userbase=$userdir
ls=''
lr1=''
lr2=''
tag="tutorial"

# Get qualifier.

qual=e14

# Loop over existing generator fcl files.

 fcl="$UBOONECODE_DIR/source/fcl/gen/single/prod_muminus_0-2.0GeV_isotropic_uboone.fcl" 
 echo $fcl
 newprj=`basename $fcl .fcl`
 xml=${newprj}.xml
 
if [ -z "$UBOONECODE_VERSION" ]; then
   echo "ERROR: You must setup uboonecode first!"
   exit 1
fi    

cp /uboone/data/users/uboonepro/tutorial/Makefile . 

 # Make xml file.

 echo "Making ${xml}"

 # Generator

 genfcl=`basename $fcl`

 # G4

 g4fcl=standard_g4_nospacecharge_uboone.fcl

 # Detsim (optical + tpc).

 detsimfcl=standard_detsim_uboone.fcl

 # Reco 1

 reco1fcl=reco_uboone_mcc8_driver_stage1.fcl

 # Reco 2

 reco2fcl=reco_uboone_mcc8_driver_stage2.fcl

 # Merge/Analysis

 mergefcl=standard_ana_uboone.fcl

 # Set number of gen/g4 events per job.

 nevjob=50
 nevgjob=$nevjob

 # Set number of events.
 nev=50


 # Calculate the number of worker jobs.

 njob1=$(( $nev / $nevgjob ))	      
 njob2=$njob1   

  
resource=DEDICATED,OPPORTUNISTIC  

cat <<EOF > $xml
<?xml version="1.0"?>

<!-- Production Project -->

<!DOCTYPE project [
<!ENTITY relsim "$rs">
<!ENTITY relreco1 "$rr1">
<!ENTITY relreco2 "$rr2">
<!ENTITY file_type "mc">
<!ENTITY run_type "physics">
<!ENTITY name "$newprj">
<!ENTITY tag "tutorial">
]>

<job>

<project name="&name;">

  <!-- Project size -->
  <numevents>$nev</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Batch resources -->
  <resource>$resource</resource>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&relsim;</tag>
    <qual>${qual}:prof</qual>
  </larsoft>

  <!-- Validate on worker -->
  <check>0</check>

  <!-- Project stages -->

  <stage name="gen">
    <fcl>$genfcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relsim;/gen/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userbase}/&tag;/&relsim;/gen/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userbase}/work/&tag;/&relsim;/gen/&name;</workdir>
    <output>${newprj}_\${PROCESS}_%tc_gen.root</output>
    <numjobs>$njob1</numjobs>
    <datatier>generated</datatier>
    <defname>&name;_&tag;_gen</defname>
  </stage>

  <stage name="g4">
    <fcl>$g4fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relsim;/g4/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userbase}/&tag;/&relsim;/g4/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userbase}/work/&tag;/&relsim;/g4/&name;</workdir>
    <numjobs>$njob1</numjobs>
    <datatier>simulated</datatier>
    <defname>&name;_&tag;_g4</defname>
  </stage>

  <stage name="detsim">
    <fcl>$detsimfcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relsim;/detsim/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userbase}/&tag;/&relsim;/detsim/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userbase}/work/&tag;/&relsim;/detsim/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>detector-simulated</datatier>
    <memory>4000</memory>
    <defname>&name;_&tag;_detsim</defname>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

<project name="&name;_reco1">

  <!-- Project size -->
  <numevents>$nev</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&relreco1;</tag>
    <qual>${qual}:prof</qual>
  </larsoft>

  <!-- Project stages -->

  <!-- Validate on worker -->
    <check>0</check>

  <stage name="reco1">
    <fcl>$reco1fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco1;/reco1/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userbase}/&tag;/&relreco1;/reco1/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userbase}/work/&tag;/&relreco1;/reco1/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>reconstructed-2d</datatier>
    <memory>4000</memory>
    <defname>&name;_&tag;_reco1</defname>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

<project name="&name;_reco2">

  <!-- Project size -->
  <numevents>$nev</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&relreco2;</tag>
    <qual>${qual}:prof</qual>
  </larsoft>

  <!-- Project stages -->

  <!-- Validate on worker -->
    <check>0</check>

  <stage name="reco2">
    <fcl>$reco2fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco2;/reco2/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userbase}/&tag;/&relreco2;/reco2/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userbase}/work/&tag;/&relreco2;/reco2/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>reconstructed-3d</datatier>
    <memory>4000</memory>
    <defname>&name;_&tag;_reco2</defname>
  </stage>

  <stage name="mergeana">
    <fcl>$mergefcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco2;/mergeana/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userbase}/&tag;/&relreco2;/mergeana/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userbase}/work/&tag;/&relreco2;/mergeana/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>reconstructed</datatier>
    <anadatatier>root-tuple</anadatatier>
    <defname>&name;_&tag;</defname>
    <anadefname>&name;_&tag;_ana</anadefname>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

</job>
EOF

xml=prod_reco_data.xml

cat <<EOF > $xml
<?xml version="1.0"?>

<!-- Production Project -->

<!DOCTYPE project [
<!ENTITY release "$rs">
<!ENTITY file_type "data">
<!ENTITY run_type "physics">
<!ENTITY name "prod_reco_data">
<!ENTITY tag "tutorial">
]>

<job>

<project name="&name;">

  <!-- Project size -->
  <numevents>1000000</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>

  <!-- Project Version -->
  <version>&tag;_&release;</version>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&release;</tag>
    <qual>e14:prof</qual>
  </larsoft>

  <!-- Validate on worker -->
  <check>0</check>

  <!-- Project stages -->

  <stage name="reco1">
    <inputdef>prod_extbnb_swizzle_inclusive_tutorial</inputdef>
    <fcl>reco_uboone_data_Feb2016_gaussfilter_driver_stage1.fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/reco1/&release;/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/reco1/&release;/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userdir}/work/&tag;/reco1/&release;/&name;</workdir>
    <numjobs>33</numjobs>
    <datatier>reconstructed-2d</datatier>
    <memory>4000</memory>
    <maxfilesperjob>1</maxfilesperjob>
    <jobsub>--expected-lifetime=long</jobsub>
    <jobsub_start>--expected-lifetime=short</jobsub_start>
  </stage>

  <stage name="reco2">
    <fcl>reco_uboone_data_Feb2016_driver_stage2.fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/reco2/&release;/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/reco2/&release;/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userdir}/work/&tag;/reco2/&release;/&name;</workdir>
    <numjobs>33</numjobs>
    <datatier>reconstructed</datatier>
    <memory>4000</memory>
    <maxfilesperjob>1</maxfilesperjob>
    <jobsub>--expected-lifetime=long</jobsub>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

</job>

EOF

xml=prodgenie_bnb_nu_cosmic_uboone_tutorial.xml

cat <<EOF > $xml
<?xml version="1.0"?>

<!-- Production Project -->

<!DOCTYPE project [
<!ENTITY relsim "$rs">
<!ENTITY relreco1 "$rr1">
<!ENTITY relreco2 "$rr2">
<!ENTITY file_type "mc">
<!ENTITY run_type "physics">
<!ENTITY name "prodgenie_bnb_nu_cosmic_uboone">
<!ENTITY tag "tutorial">
]>

<job>

<project name="&name;">

  <!-- Project size -->
  <numevents>10000</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>
  
  <!-- Project Version -->
  <version>&tag;_$rs</version>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&relsim;</tag>
    <qual>e14:prof</qual>
  </larsoft>
  
  <check>1</check>

  <!-- Project stages -->

  <stage name="sim">
    <fcl>prodgenie_bnb_nu_cosmic_uboone.fcl</fcl>
    <fcl>$g4fcl</fcl>
    <fcl>$detsimfcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relsim;/sim/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relsim;/sim/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userdir}/work/&tag;/&relsim;/sim/&name;</workdir>
    <output>prodgenie_bnb_nu_cosmic_uboone_${PROCESS}_%tc_gen.root</output>
    <numjobs>200</numjobs>
    <datatier>detector-simulated</datatier>
    <memory>4000</memory>
    <jobsub>--expected-lifetime=24h</jobsub>
  </stage>  
  
  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

<project name="&name;_reco">

  <!-- Project size -->
  <numevents>50</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Project Version -->
  <version>&tag;_$rr1</version>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&relreco1;</tag>
    <qual>e14:prof</qual>
  </larsoft>

  <check>1</check>

  <!-- Project stages -->

  <stage name="reco">
    <fcl>$reco1fcl</fcl>
    <fcl>$reco2fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco1;/reco/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco1;/reco/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userdir}/work/&tag;/&relreco1;/reco/&name;</workdir>
    <numjobs>200</numjobs>
    <datatier>reconstructed</datatier>
    <maxfilesperjob>1</maxfilesperjob>
    <inputdef>prodgenie_bnb_nu_cosmic_uboone_mcc8_detsim</inputdef>
    <memory>4000</memory>
    <jobsub>--expected-lifetime=24h</jobsub>
    <jobsub_start>--expected-lifetime=short</jobsub_start>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

<project name="&name;_reco2">

  <!-- Project size -->
  <numevents>50</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Project Version -->
  <version>&tag;_$rr2</version>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&relreco2;</tag>
    <qual>e14:prof</qual>
  </larsoft>

  <check>0</check>
  <copy>0</copy>

  <!-- Project stages -->

  <stage name="mergeana">
    <fcl>standard_ana_uboone.fcl</fcl>
    <outdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco2;/mergeana/&name;</outdir>
    <logdir>/pnfs/uboone/scratch/users/${userdir}/&tag;/&relreco2;/mergeana/&name;</logdir>
    <workdir>/pnfs/uboone/scratch/users/${userdir}/work/&tag;/&relreco2;/mergeana/&name;</workdir>
    <numjobs>200</numjobs>
    <datatier>reconstructed</datatier>
    <anadatatier>root-tuple</anadatatier>
    <anadefname>&name;_&tag;_ana</anadefname>
    <memory>2000</memory>
    <jobsub> --subgroup=prod </jobsub>
    <jobsub_start> --subgroup=prod --expected-lifetime=short</jobsub_start>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

</job>

EOF

cat << EOF > demo_ReadEvent.cc

/*************************************************************
 * 
 * demo_ReadEvent program
 * 
 * This is a simple demonstration of reading a LArSoft file 
 * and printing out the run and event numbers. You can also
 * put the event numbers into a histogram!
 *
 * Wesley Ketchum (wketchum@fnal.gov), Aug28, 2016
 * 
 *************************************************************/


//some standard C++ includes
#include <iostream>
#include <stdlib.h>
#include <string>
#include <vector>

//some ROOT includes
#include "TInterpreter.h"
#include "TROOT.h"
#include "TH1F.h"
#include "TFile.h"

//"art" includes (canvas, and gallery)
#include "canvas/Utilities/InputTag.h"
#include "gallery/Event.h"
#include "gallery/ValidHandle.h"
#include "canvas/Persistency/Common/FindMany.h"
#include "canvas/Persistency/Common/FindOne.h"

#include "lardataobj/RecoBase/Track.h"

//convenient for us! let's not bother with art and std namespaces!
using namespace art;
using namespace std;

int main(){
  
  //Let's make a histogram to store event numbers.
  //I ran this before, so I know my event range. You can adjust this for your file!

  //note, because I'm in my standalone code now, I'm not going to make this a pointer
  //so I can have nice clean memory
  TH1F h_events("h_events","Event Numbers;event;N_{events} / bin",50,0,50); 
  
  //We specify our files in a list of file names!
  //Note: multiple files allowed. Just separate by comma.
  //  vector<string> filenames { "MyInputFile_1.root" };
  vector<string> filenames { "path_to_your_file" }; //Change this to the full path of your muon reco2 file
  
  InputTag track_tag { "pandoraCosmic" };

  //ok, now for the event loop! Here's how it works.
  //
  //gallery has these built-in iterator things.
  //
  //You declare an event with a list of file names. Then, you
  //move to the next event by using the "next()" function.
  //Do that until you are "atEnd()".
  //
  //In a for loop, that looks like this:

  for (gallery::Event ev(filenames) ; !ev.atEnd(); ev.next()) {

    //to get run and event info, you use this "eventAuxillary()" object.
    cout << "Processing "
	 << "Run " << ev.eventAuxiliary().run() << ", "
	 << "Event " << ev.eventAuxiliary().event() << endl;

    // Track Handle Information in the loop.
    auto const& track_handle = ev.getValidHandle<vector<recob::Track>>(track_tag);
    auto const& track_vec(*track_handle);	 

    //ok, then we can fill our histogram!
    h_events.Fill(ev.eventAuxiliary().event());
    
    for (size_t i_t = 0, size_track = track_handle->size(); i_t != size_track; ++i_t) {
       double track_length = track_vec.at(i_t).Length();
       cout << track_length << endl;
    }

  } //end loop over events!


  //and ... write to file!
  TFile f_output("demo_ReadEvent_output.root","RECREATE");
  h_events.Write();
  f_output.Close();
  
}

EOF
