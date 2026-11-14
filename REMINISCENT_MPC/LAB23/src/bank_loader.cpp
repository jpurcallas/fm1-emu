#include "bank_loader.hpp"
#include <fstream>
#include <sstream>
#include <cstdlib>
namespace rem {
bool preloadAllBanks(Engine &engine,const std::string& base,std::string &err,int &sampleCount){
 std::ifstream f(base+"/bank.tsv");if(!f){err="bank.tsv missing";return false;}
 std::string line;sampleCount=0; bool sawFlac=false; bool didgeA=false;
 while(std::getline(f,line)){
  std::istringstream is(line);int src=-1,note=0;std::string rel,tag;float cents=0.f;
  if(!(is>>src>>note>>rel>>tag>>cents))continue;
  if(src<0||src>=28||src==8)continue; // duduk excluded (catalog source 8)
  const bool flac=rel.size()>=5 && rel.compare(rel.size()-5,5,".flac")==0;
  sawFlac=sawFlac||flac;
  if(src==10 && tag=="B" && flac){err="Didgeridoo B estaba excluido del banco FLAC aprobado";return false;}
  rem::Bank &bank=(src==10 && tag=="B")?engine.didgeridooB:engine.sourceBanks[src];
  if(flac ? !bank.loadFlac(base+"/"+rel,note,err) : !bank.loadWav(base+"/"+rel,note,err))return false;
  bank.layers.back().tuneCents=cents;
  if(src==10 && tag=="A")didgeA=true;
  sampleCount++;
 }
 const int expected=sawFlac?253:254;
 if(sampleCount!=expected){err="expected "+std::to_string(expected)+" sample anchors, loaded "+std::to_string(sampleCount);return false;}
 if(sawFlac && !didgeA){err="Falta didgeridoo A aprobado";return false;}
 return true;
}
}