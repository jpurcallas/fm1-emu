// Native host regression using generated synthetic PCM only; no private assets.
#include "engine.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>
int main(int argc,char**argv){
 if(argc!=7){std::cerr<<"expected flac expected-raw channels rate bits frames root\n";return 2;}
 const std::string flac=argv[1],expected=argv[2];
 const int channels=std::stoi(argv[3]),rate=std::stoi(argv[4]),bits=std::stoi(argv[5]),frames=std::stoi(argv[6]);
 std::ifstream f(expected,std::ios::binary);if(!f)return 3;
 const std::vector<uint8_t> ref((std::istreambuf_iterator<char>(f)),{});
 rem::Bank bank;std::string error;
 if(!bank.loadFlac(flac,60,error)){std::cerr<<error<<"\n";return 4;}
 if(bank.layers.size()!=1)return 5;
 const rem::Sample &s=bank.layers.front();
 if(s.channels!=channels||s.rate!=rate||s.bits!=bits||s.frames!=size_t(frames)||s.wavFormat!=1||s.root!=60){
  std::cerr<<"format mismatch\n";return 6;
 }
 if(s.pcm!=ref){auto it=std::mismatch(s.pcm.begin(),s.pcm.end(),ref.begin(),ref.end());
  std::cerr<<"LOSSLESS MISMATCH raw PCM bytes="<<s.pcm.size()<<" expected="<<ref.size()<<"\n";return 7;
 }
 std::cout<<"PASS "<<flac<<" PCM bytes="<<ref.size()<<" frames="<<frames<<" bits="<<bits<<"\n";
 return 0;
}
