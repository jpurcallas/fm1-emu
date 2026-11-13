#pragma once
#include "engine.hpp"
#include <string>
namespace rem {bool loadPcmBank(const std::string& base,const std::string& manifest,int oldSourceA,int oldSourceB,Bank& a,Bank& b,std::string& err,int& na,int& nb);}