//----------------------------------------------------------------------
//
// Name: fclmodule.cxx
//
// Purpose: A python extension module that wraps the c++ fcl
//          api.  The main purpose of this module is to provide the
//          capability to read and parse a fcl file and return the
//          resulting parameter set in the form of a python dictionary.
//
//          This module compiles to a shared library (fclmodule.so).  
//          When this shared library is on the python path, it can be
//          imported as a python module (import fcl).
//
// Created: 4-Apr-2017  H. Greenlee
//
// FCL module interface.
//
// Module members.
//
// 1.  Function make_pset(fclfile)
//
// The argument is the name of a fcl file (can be anywhere on $FHICL_FILE_PATH).
// The function reads the fcl file and returns the expanded parameter set
// in the form of a python dictionary.
//
// Example:
//
// #! /usr/bin/env python
// import fcl
// pset = fcl.make_pset('myfile.fcl')
//
//
//----------------------------------------------------------------------

#include "Python.h"
#include <iostream>
#include <sstream>
#include "cetlib/search_path.h"
#include "fhiclcpp/ParameterSet.h"
#include "fhiclcpp/ParameterSetRegistry.h"
#include "fhiclcpp/make_ParameterSet.h"

// Forward declarations.

PyObject* convert_any(const boost::any& any);

PyObject* convert_atom(const std::string& atom)
//
// Purpose: Convert a string representing an atomic value to a python object.
//          The type of the returned object is one of: bool, int, float, or 
//          string.  The type is chosen based on the string content.  In
//          principle, fhicl also support type complex.  We don't handle 
//          complex in this function (complex atomic values will be returned
//          as strings).
//
// Arguments: atom - A string reprsenting an atomic value.
//
// Return value: Python object pointer.
//
{
  // Return value.

  PyObject* pyval = 0;

  // Get lower case version of argument string.

  std::string lcatom(atom);
  std::transform(lcatom.begin(), lcatom.end(), lcatom.begin(),
		 [](unsigned char c){return std::tolower(c);});

  // Check for boolean.

  if(lcatom == std::string("true")) {
    pyval = Py_True;
    Py_INCREF(pyval);
  }
  else if(lcatom == std::string("false")) {
    pyval = Py_False;
    Py_INCREF(pyval);
  }

  // Check for quoted string.

  size_t n = atom.size();
  if(pyval == 0 && n >= 2 && atom[0] == '"' && atom[n-1] == '"') {
    std::string s = atom.substr(1, n-2);
    pyval = PyString_FromString(s.c_str());
  }  

  // Check for int.

  if(pyval == 0) {
    std::istringstream iss(atom);
    long i;
    iss >> std::noskipws >> i;
    if(iss.eof() and !iss.fail())
      pyval = PyInt_FromLong(i);
  }

  // Check for float.

 if(pyval == 0) {
    std::istringstream iss(atom);
    double x;
    iss >> std::noskipws >> x;
    if(iss.eof() and !iss.fail())
      pyval = PyFloat_FromDouble(x);
  }
  
  // Last resort store a copy of the original string (unquoted string).

  if(pyval == 0)
    pyval = PyString_FromString(atom.c_str());

  // Done.

  return pyval;
}

PyObject* convert_pset(const fhicl::ParameterSet& pset)
//
// Purpose: Convert a parameter set to a python dictionary.
//
// Arguments: pset - Parameter set.
//
// Return value: Python dictionary pointer.
//
{
  // Make an empty python dictionary that will be our result.

  PyObject* pydict = PyDict_New();

  // Pry open the parameter set.

  const std::map<std::string, boost::any>& anymap = 
    reinterpret_cast<const std::map<std::string, boost::any>&>(pset);

  // Loop over items in parameter set.

  for(const auto& entry : anymap) {
    const std::string& key = entry.first;
    const boost::any& any = entry.second;
    PyObject* pyval = convert_any(any);

    // Done converting key.

    if(pyval != 0) {

      // Conversion was successful.  Insert value into dictionary.

      PyDict_SetItemString(pydict, key.c_str(), pyval);
      Py_DECREF(pyval);
    }
    else {

      // Abort.

      Py_DECREF(pydict);
      pydict = 0;
      break;
    }
  }

  // Done.

  return pydict;
}

PyObject* convert_seq(const std::vector<boost::any>& seq)
//
// Purpose: Convert a sequence to a python list.
//
// Arguments: seq - Sequence.
//
// Return value: Python list pointer.
//
{
  // Make a python list that will be our return value.

  PyObject* pylist = PyList_New(seq.size());
  for(unsigned int i=0; i<seq.size(); ++i) {

    // Convert element.

    PyObject* pyele = convert_any(seq[i]);
    if(pyele != 0) {

      // Element conversion was successful.  Insert element into list.

      PyList_SetItem(pylist, i, pyele);
    }
    else {

      // Abort.

      Py_DECREF(pylist);
      pylist = 0;
    }
  }

  // Done.

  return pylist;
}

PyObject* convert_any(const boost::any& any)
//
// Purpose: Convert a boost::any to a python object.
//
// Arguments: any - Boost::any object.
//
// Return value: Python object pointer.
//
{
  // Return value.

  PyObject* pyval = 0;

  if(any.type() == typeid(std::string)) {

    // Atomic types.

    const std::string& atom = boost::any_cast<const std::string&>(any);
    pyval = convert_atom(atom);
  }
  else if(any.type() == typeid(std::vector<boost::any>)) {

    // Sequences.

    const std::vector<boost::any>& anyvec = boost::any_cast<const std::vector<boost::any>&>(any);
    pyval = convert_seq(anyvec);
  }
  else if(any.type() == typeid(fhicl::ParameterSetID)) {

    // Parameter sets.

    const fhicl::ParameterSetID& id = boost::any_cast<const fhicl::ParameterSetID&>(any);
    const fhicl::ParameterSet& pset = fhicl::ParameterSetRegistry::get(id);
    pyval = convert_pset(pset);
  }
  else {

    // Unknown type.
    // Shouldn't happen.

    std::string msg = std::string("Failed to convert object of type ") + any.type().name();
    PyErr_SetString(PyExc_ValueError, msg.c_str());
  }

  // Done.

  return pyval;
}

static PyObject* make_pset(PyObject* self, PyObject *args)
//
// Purpose: Public module function to read fcl file and return a python dictionary.
//
// Arguments: self - Not used, because this is not a member function.
//            args - Argument tuple.  A single string representing the
//                   name of a fcl file.
// Returned value: A python dictionary.
//
{
  // Extract argument as string.

  const char* fclname;
  if(!PyArg_ParseTuple(args, "s", &fclname))
    return 0;
  std::string fclstr(fclname);

  // Make parameter set.

  PyObject* result = 0;
  fhicl::ParameterSet pset;
  std::string pathvar("FHICL_FILE_PATH");
  cet::filepath_lookup maker(pathvar);
  try {
    fhicl::make_ParameterSet(fclstr, maker, pset);
    result = convert_pset(pset);
  }
  catch(cet::exception& e) {
    PyErr_SetString(PyExc_IOError, e.what());
    result = 0;
  }

  // Done.

  return result;
}

// Module method table.

static struct PyMethodDef fclmodule_methods[] = {
     {"make_pset", make_pset, METH_VARARGS},
     {0, 0}
};

// Initialization function.

extern "C" {
  void initfcl()
  {
    Py_InitModule("fcl", fclmodule_methods);
  }
}
