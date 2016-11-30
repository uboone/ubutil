//
// Name: key_params
//
// Purpose: Stand alone executable to parse fcl job files and dump some
//          important fcl parameters.  Emphasis is on fcl parameters, including
//          service parameters that must match between simulation and
//          reconstruction.
//
// Usage:
//
// key_params [-h] [-p <fcl-path>] <fcl-file>
//
// Options:
//
// -h - Print help message.
// -p - Fcl path (colon-separated list of directories, default $FHICL_FILE_PATH).
//
// Arguments:
//
// <fcl-file> - Fcl job file to analyze.
//
// Created: H. Greenlee 21-Nov-2016

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include "fhiclcpp/ParameterSet.h"
#include "fhiclcpp/make_ParameterSet.h"

// Function to print help message.

void help()
{
  std::cout << "\nUsage: key_params [-h] <fcl-file>\n"
	    << "\n"
	    << "Options:\n"
	    << "\n"
	    << "-h - Print help message.\n"
	    << "-p - Fcl path (colon-separated list of directories, default $FHICL_FILE_PATH).\n"
	    << "\n"
	    << "Arguments:\n"
	    << "\n"
	    << "<fcl-file> - Fcl job file to analyze." << std::endl;
}

// Function to recursively analyze parameter set.

void analyze(const fhicl::ParameterSet& pset, const std::string& head)
{
  // Get trigger paths and end paths, if applicable.

  if(head == "physics") {
    std::vector<std::string> groups;
    groups.push_back("trigger_paths");
    groups.push_back("end_paths");

    // Print paths.

    for(auto const & group : groups) {
      std::vector<std::string> paths = pset.get<std::vector<std::string> >(group);
      std::cout << "physics." << group << ": [ ";
      std::string sep;
      for(auto const & path : paths) {
	std::cout << sep << '"' << path << '"';
	sep = ", ";
      }
      std::cout << "]" << std::endl;

      // Print modules in each path.

      for(auto const& path : paths) {
	std::vector<std::string> modules = pset.get<std::vector<std::string> >(path);
	std::cout << "physics." << path << ": [ ";
	sep.clear();
	for(auto const & module : modules) {
	  std::cout << sep << '"' << module << '"';
	  sep = ", ";
	}
	std::cout << "]" << std::endl;
      }
    }
  }

  // Loop over keys.

  std::vector<std::string> keys = pset.get_names();
  for(auto const& key : keys) {
    if(pset.is_key_to_table(key)) {

      // Print services.

      if(head == "services")
	std::cout << "\nservices." << key << ":" << std::endl;

      // Keys of tables handled here by recursively calling this function.

      fhicl::ParameterSet ps;
      ps = pset.get<fhicl::ParameterSet>(key);
      std::string new_head = (head.empty() ? key : head + std::string(".") + key);
      analyze(ps, new_head);
    }
    else {

      // Leaf keys handled here (including sequences).
      // Only certain keys with known c++ types are extracted.

      std::string prefix = (head.empty() ? key : head + std::string(".") + key) + std::string(": ");

      // Type bool.

      if(key == "StretchFullResponse" ||
	 key == "TruncateTicks" ||
	 key == "ProcessNoise" ||
	 key == "InheritClockConfig" ||
	 key == "EnableSimSpatialSCE" ||
	 key == "EnableSimEfieldSCE" ||
	 key == "EnableCorrSCE")
	std::cout << prefix << (pset.get<bool>(key) ? "true" : "false") << std::endl;

      // Type string.

      if(key == "LibraryFile" ||
	 key == "service_provider" ||
	 key.find("BeamGateModule") < std::string::npos)
	std::cout << prefix << '"' << pset.get<std::string>(key) << '"' << std::endl;

      // Type int.

      if(key == "NConfigs" ||
	 key == "WindowSize" ||
	 key == "TriggerOffsetTPC" ||
	 key == "NumberTimeSamples" ||
	 key == "ReadOutWindowSize" ||
	 key == "NumTicksToDropFront" ||
	 key == "MaxMultiHit" ||
	 key == "GenNoise" ||
	 key == "TDist" ||
	 key == "T0" ||
	 key == "SigmaT")
	try {
	  std::cout << prefix << pset.get<int>(key) << std::endl;
	}
	catch(...) {}

      // Type double.

      if(key == "Temperature" ||
	 key == "Electronlifetime" ||
	 key == "BNBFireTime" ||
	 key == "GlobalTimeOffset" ||
	 key == "RandomTimeOffset" ||
	 key == "G4RefTime" ||
	 key == "SampleTime" ||
	 key == "TimeOffset")
	std::cout << prefix << pset.get<double>(key) << std::endl;

      // Type vector<bool>.

      if(key == "TransformViewVec" ||
	 key == "ZigZagCorrectVec") {
	std::vector<bool> values = pset.get<std::vector<bool> >(key);
	std::cout << prefix << "[ ";
	std::string sep;
	for(auto value : values) {
	  std::cout << sep << (value ? "true" : "false");
	  sep = ", ";
	}
	std::cout << "]" << std::endl;
      }

      // Type vector<string>.

      if(key == "FilterFuncVec" ||
	 key == "swtrg_algonames" ||
	 key == "swtrg_algotype" ||
	 (head.find("OpMapTimeRanges") < std::string::npos &&
	  key.find("FEMOpMap") < std::string::npos)) {
	std::vector<std::string> values = pset.get<std::vector<std::string> >(key);
	std::cout << prefix << "[ ";
	std::string sep;
	for(auto value : values) {
	  std::cout << sep << '"' << value << '"';
	  sep = ", ";
	}
	std::cout << "]" << std::endl;
      }

      // Type vector<int>.

      if(key == "Mask" ||
	 key == "T0" ||
	 key == "SigmaT" ||
	 (head.find("OpMapRunRanges") < std::string::npos &&
	  key.find("FEMOpMap") < std::string::npos)) {
	try {
	  std::vector<int> values = pset.get<std::vector<int> >(key);
	  std::cout << prefix << "[ ";
	  std::string sep;
	  for(auto value : values) {
	    std::cout << sep << value;
	    sep = ", ";
	  }
	  std::cout << "]" << std::endl;
	}
	catch(...) {}
      }

      // Type vector<double>.

      if(key == "Efield" ||
	 key == "FilterWidthCorrectionFactor" ||
	 key == "MinSig" ||
	 key == "BNBTrigger" ||
	 key == "ExtTrigger" ||
	 key == "UserBNBTime") {
	std::vector<double> values = pset.get<std::vector<double> >(key);
	std::cout << prefix << "[ ";
	std::string sep;
	for(auto value : values) {
	  std::cout << sep << value;
	  sep = ", ";
	}
	std::cout << "]" << std::endl;
      }

      // Type vector<vector<double>>.

      if(key == "ShapeTimeConst" ||
	 key == "ASICGainInMVPerFC" ||
	 key == "FilterParamsVec") {
	std::vector<std::vector<double> > outer_values = 
	  pset.get<std::vector<std::vector<double> > >(key);
	std::cout << prefix << "[ ";
	std::string outer_sep;
	for(auto const & inner_values : outer_values) {
	  std::cout << outer_sep;
	  std::string inner_sep("[ ");
	  for(auto value : inner_values) {
	    std::cout << inner_sep << value;
	    inner_sep = ", ";
	  }
	  std::cout << "]";
	  outer_sep = ", ";
	}
	std::cout << "]" << std::endl;
      }
    }
  }
}

// Main program.

int main(int argc, char** argv)
{
  // Parse arguments.

  std::string fcl;                          // Fcl file.
  std::string pathvar("FHICL_FILE_PATH");   // Fcl path environment variable.

  for(int i=1; i<argc; ++i) {

    std::string arg(argv[i]);

    // Parse options.

    // Help option.

    if(arg == "-h") {
      help();
      return 0;
    }

    // Path option.

    if(arg == "-p") {
      if(i<argc-1 && *argv[i+1] != '-') {
	std::ostringstream fclpath;        // Fcl path (name=value).
	fclpath << pathvar << "=" << std::string(argv[i+1]);
	char* p = strdup(fclpath.str().c_str());
	putenv(p);
	++i;
      }
      else {
	std::cout << "Option -p requires an argument." << std::endl;
	return 1;
      }
    }

    // Other options are not allowed.

    else if(arg[0] == '-') {
      std::cout << "Option " << arg << " not recognized." << std::endl;
      help();
      return 1;
    }

    // Extract fcl file name.

    else if(fcl.empty())
      fcl = arg;

    // Too many arguments.

    else {
      std::cout << "Too many arguments." << std::endl;
      help();
      return 1;
    }
  }

  // Done parsing arguments.
  // First do some sanity checks.

  if(fcl.empty()) {
    std::cout << "No fcl file specified." << std::endl;
    help();
    return 1;
  }

  fhicl::ParameterSet pset;
  cet::filepath_lookup maker(pathvar);
  fhicl::make_ParameterSet(fcl, maker, pset);

  // Analyze parameter set.

  std::string head;
  analyze(pset, head);

  // Done.
    
  return 0;
}
