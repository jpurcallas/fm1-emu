// LAB23 source-bank acceptance test; no third-party WAV redistribution.
// Build: c++ -std=c++17 -O2 -o test_all_acoustic_27 tests/test_all_acoustic_27.cpp \
//        src/engine.cpp src/bank_loader.cpp src/lab19_pcm_bank.cpp
// Run: ./test_all_acoustic_27 Content
#include "../src/engine.hpp"
#include "../src/bank_loader.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>
int main(int argc,char** argv){
 if(argc!=2){std::fprintf(stderr,"usage: test_all_acoustic_27 <Content>\n");return 2;}
 auto e=std::make_unique<rem::Engine>(44100);std::string err;int loaded=0;
 if(!rem::preloadAllBanks(*e,argv[1],err,loaded)||loaded!=254){
  std::fprintf(stderr,"FAIL: PCM bank: %s; loaded %d\n",err.c_str(),loaded);return 1;
 }
 e->params.oscOn=false;e->params.acousticA=true;e->params.acousticB=false;
 e->params.masterBlend=0.f;e->params.masterLevel=1.f;e->params.masterPresence=64.f/127.f;
 e->params.acousticBlend=0.f;e->params.attack=.001f;e->params.decay=.12f;
 e->params.sustain=1.f;e->params.release=.12f;e->params.grainMix=0.f;e->params.resoMix=0.f;
 std::vector<rem::Stereo> audio(128);
 int passes=0,failures=0,aboveUnity=0;
 for(int source=0;source<28;source++){
  if(source==8)continue; // Duduk excluded; no substitution.
  const auto& bank=e->sourceBanks[source];
  if(bank.layers.empty()){std::printf("FAIL source %02d missing\n",source);failures++;continue;}
  e->allSoundOff();e->params.sourceA=source;
  const int note=bank.layers[bank.layers.size()/2].root;
  e->noteOn(note,1.f);
  double sum=0;float peak=0;int samples=0;
  for(int block=0;block<120;block++){
   e->render(audio.data(),128);
   for(auto sample:audio){
    if(!std::isfinite(sample.l)||!std::isfinite(sample.r)){
     std::printf("FAIL source %02d non-finite output\n",source);return 1;
    }
    peak=std::max(peak,std::max(std::fabs(sample.l),std::fabs(sample.r)));
    sum+=double(sample.l)*sample.l+double(sample.r)*sample.r;samples+=2;
   }
  }
  const double rms=std::sqrt(sum/samples);
  const bool audible=peak>=1e-5f&&rms>=1e-6;
  aboveUnity+=(peak>1.f);
  if(audible)passes++;else failures++;
  std::printf("%s source %02d layers=%zu root=%d peak=%.6f rms=%.6f\n",
              audible?"PASS":"FAIL",source,bank.layers.size(),note,peak,rms);
 }
 // Original alternate didgeridoo B is separate from the main 27 catalog sources.
 const auto& b=e->didgeridooB;
 if(b.layers.empty()){std::puts("FAIL didgeridoo B empty");failures++;}
 else{
  e->allSoundOff();e->params.acousticA=false;e->params.acousticB=true;e->params.sourceB=10;
  e->noteOn(b.layers.front().root,1.f);
  float peak=0;
  for(int block=0;block<120;block++){
   e->render(audio.data(),128);
   for(auto sample:audio)peak=std::max(peak,std::max(std::fabs(sample.l),std::fabs(sample.r)));
  }
  if(peak>=1e-5f)std::printf("PASS didgeridoo B peak=%.6f\n",peak);
  else{std::puts("FAIL didgeridoo B silent");failures++;}
 }
 std::printf("RESULT %d/27 acoustic sources; %d PCM anchors; fail=%d; raw full-level >1.0 sources=%d\n",
             passes,loaded,failures,aboveUnity);
 // Raw maximum-level peaks are diagnostic only, not an approved limiter change.
 return passes==27&&failures==0?0:1;
}
