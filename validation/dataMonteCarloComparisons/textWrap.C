// This function wraps text (so we can output multi-line .comment files for the CI dashboard)
void textWrap(std::string &in, std::ostream& out, size_t width) {

  std::string tmp;
  char cur = '\0';
  char last = '\0';
  size_t i = 0;

  for (size_t idx_in_str=0; idx_in_str < in.size(); idx_in_str++) {
    cur = in.at(idx_in_str);
    if (idx_in_str == in.size()-1){ // Add last word to the file
      out << tmp << cur << '\n';
    }
    if (++i == width) { // If you get to the character limit for a line, add it to the file
      if (isspace(tmp.at(0))){ // Remove leading spaces
        //tmp = tmp.substr(1,tmp.size()-1);
        tmp.erase(tmp.begin());
      }
      out << '\n' << tmp;           
      i = tmp.length();
      tmp.clear();
    }
    else if (isspace(cur) && !isspace(last)) { // This is the end of a word. Add it to the file
      out << tmp;
      tmp.clear();
    }
    tmp += cur;
    last = cur;
  }
}
