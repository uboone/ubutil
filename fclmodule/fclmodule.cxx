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
#include <iomanip>
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

  if(lcatom == std::string("true") || lcatom == std::string("\"true\"")) {
    pyval = Py_True;
    Py_INCREF(pyval);
  }
  else if(lcatom == std::string("false") || lcatom == std::string("\"false\"")) {
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

static std::string format(PyObject* obj, unsigned int pos, unsigned int indent, unsigned int maxlen)
//
// Purpose: Convert a python object to a prettified string.  The resulting string
//          is suppsed to be valid python code.
//
// Arguments: obj    - Object to be formatted.
//            pos    - Current character position (number of characters printed
//                     since the last newline).
//            indent - Indentation level (spaces) for multiline formatting.
//            maxlen - Maximum line length before breaking.
//
// Returns: c++ string.
//
// Usage:
//
// This function is designed to call itself recursively in order to descend
// into structured objects like dictionaries and sequences.
//
// Dictionaries and sequences may be printed in either single-line or multiline
// format, depending on the complexity of the contained objects, and the indent
// and maxlen parameters.
//
{
  // Result string stream.

  std::ostringstream ss;

  if(PyString_Check(obj)) {

    // String objects, add single quotes, but don't do any other formatting.

    ss << "'" << PyString_AsString(obj) << "'";
  }

  else if(PyDict_Check(obj)) {

    // Always print dictionary objects in multiline format, one key per line.

    // Get list of keys.  Keys are assumed to be strings.

    PyObject* keys = PyDict_Keys(obj);

    // Make a first pass over the list of keys to determine the maximum length key.

    int n = PyList_Size(keys);
    int keymaxlen = 0;
    for(int i=0; i<n; ++i) {
      PyObject* key = PyList_GetItem(keys, i);
      int keylen = PyString_Size(key);
      if(keylen > keymaxlen)
	keymaxlen = keylen;
    }

    // Second pass, loop over keys and values and convert them to strings.

    char sep = '{';
    for(int i=0; i<n; ++i) {
      PyObject* key = PyList_GetItem(keys, i);
      PyObject* value = PyDict_GetItem(obj, key);
      const char* ks = PyString_AsString(key);
      std::string ksquote = std::string("'") + std::string(ks) + std::string("'");
      ss << sep << '\n'
	 << std::setw(indent+2) << ""
	 << std::setw(keymaxlen+2) << std::left << ksquote << " : "
	 << format(value, indent + keymaxlen + 7, indent+2, maxlen);
      sep = ',';
    }
    if(n == 0)
      ss << "{}";
    else
      ss << '\n' << std::setw(indent+1) << std::right << '}';

    Py_DECREF(keys);

  }

  else if(PyList_Check(obj) || PyTuple_Check(obj)) {

    // Sequence printing handled here.
    // Break lines only when position exceeds maxlen.

    char open_seq = 0;
    char close_seq = 0;
    int n = 0;
    if(PyList_Check(obj)) {
      open_seq = '[';
      close_seq = ']';
      n = PyList_Size(obj);
    }
    else {
      open_seq = '(';
      close_seq = ')';
      n = PyTuple_Size(obj);
    } 

    // Loop over elements of this sequence.

    std::string sep(1, open_seq);
    unsigned int break_indent = pos+1;
    for(int i=0; i<n; ++i) {
      ss << sep;
      pos += sep.size();
      PyObject* ele = PySequence_GetItem(obj, i);

      // Get the formatted string representation of this object.

      std::string f = format(ele, pos, break_indent, maxlen);

      // Get the number of characters before the first newline.

      std::string::size_type fs = f.size();
      std::string::size_type n1 = std::min(f.find('\n'), fs);

      // Decide if we want to break the line before printing this element.
      // Never break at the first element of a sequence.
      // Force a break (except at first element) if this is a structured element.
      // If we do break here, reformat this element with the updated position.

      bool force_break = PyList_Check(ele) || PyTuple_Check(ele) || PyDict_Check(ele);
      if(i > 0 && (force_break || pos + n1 > maxlen)) {
	ss << '\n' << std::setw(break_indent) << "";
	pos = break_indent;
	f = format(ele, pos, break_indent, maxlen);
      }

      // Print this element

      ss << f;

      // Update the current character position, taking into account 
      // whether the string we just printed contains a newline.

      std::string::size_type n2 = f.find_last_of('\n');
      if(n2 >= fs)
	pos += fs;
      else
	pos = fs - n2 - 1;

      sep = std::string(", ");
      Py_DECREF(ele);
    }

    // Close sequence.

    if(n == 0)
      ss << open_seq;
    ss << close_seq;
  }

  else {

    // Last resort, use python's string representation.

    PyObject* pystr = PyObject_Str(obj);
    ss << PyString_AsString(pystr);
  }

  // Done.

  return ss.str();
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

static PyObject* pretty(PyObject* self, PyObject *args)
//
// Purpose: Public module function to convert a python fcl dictionary to a
//          prettified string.
//
// Arguments: self - Not used, because this is not a member function.
//            args - Argument tuple.  This function expects a single 
//                   python object of any type, but typically a dictionary.
//
// Returned value: A python string or none.
//
{
  // Result.

  PyObject* result = 0;

  // Extract argument.

  int n = PySequence_Length(args);
  if(n == 0) {

    // No arguments, return none.

    result = Py_None;
    Py_INCREF(result);
  }
  else {

    // Otherwise, extract the first element.

    PyObject* obj = PySequence_GetItem(args, 0);
    std::string s = format(obj, 0, 0, 80);
    result = PyString_FromString(s.c_str());
  }

  // Done.

  return result;
}

// Module method table.

static struct PyMethodDef fclmodule_methods[] = {
     {"make_pset", make_pset, METH_VARARGS},
     {"pretty", pretty, METH_VARARGS},
     {0, 0}
};

// Initialization function.

extern "C" {
  void initfcl()
  {
    Py_InitModule("fcl", fclmodule_methods);
  }
}
