#include "lab19_pcm_bank.hpp"
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <vector>
namespace rem {
bool loadPcmBank(const std::string& base,const std::string& manifest,int oldSourceA,int oldSourceB,Bank& a,Bank& b,std::string& err,int& na,int& nb){
 std::ifstream f(manifest);if(!f){err="Manifest bank.tsv no encontrado";return false;}
 std::string ln;na=0;nb=0;
 while(std::getline(f,ln)){
  std::istringstream is(ln);int source=0,root=60;std::string path,tag;
  if(!(is>>source>>root>>path>>tag))continue;float tuning=0.f;is>>tuning;
  if(source==8)continue; // Duduk retired; no fallback allowed.
  if(source==oldSourceA && !(source==10 && tag=="B")) {
   if(!a.loadWav(base+"/"+path,root,err))return false;a.layers.back().tuneCents=tuning;na++;
  }
  if(source==oldSourceB && !(source==10 && tag=="A")) {
   if(!b.loadWav(base+"/"+path,root,err))return false;b.layers.back().tuneCents=tuning;nb++;
  }
 }
 if(na==0||nb==0){err="Una fuente acústica seleccionada está vacía";return false;}
 return true;
}
}