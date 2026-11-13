#include "bank_loader.hpp"
#include <fstream>
#include <sstream>
#include <cstdlib>
namespace rem {
bool preloadAllBanks(Engine &engine,const std::string& base,std::string &err,int &sampleCount){
 std::ifstream f(base+"/bank.tsv");if(!f){err="bank.tsv missing";return false;}
 std::string line;sampleCount=0;
 while(std::getline(f,line)){
  std::istringstream is(line);int src=-1,note=0;std::string rel,tag;float cents=0.f;
  if(!(is>>src>>note>>rel>>tag>>cents))continue;
  if(src<0||src>=28||src==8)continue; // duduk excluded (catalog source 8)
  rem::Bank &bank=(src==10 && tag=="B")?engine.didgeridooB:engine.sourceBanks[src];
  if(!bank.loadWav(base+"/"+rel,note,err))return false;
  bank.layers.back().tuneCents=cents;sampleCount++;
 }
 if(sampleCount!=254){err="expected 254 sample anchors, loaded "+std::to_string(sampleCount);return false;}
 return true;
}
}