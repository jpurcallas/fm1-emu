// REminiSCENT LAB24: four real DSP paths + WHITE/PINK choice.
// Build host: c++ -std=c++17 -O2 -Isrc -o test_dsp_lab24
//   tests/test_dsp_lab24.cpp src/engine.cpp src/bank_loader.cpp
//   src/lab19_pcm_bank.cpp
// Run: ./test_dsp_lab24 Content
// Tests original LAB19 PCM from private storage, not redistributed in git.
#include "../src/engine.hpp"
#include "../src/bank_loader.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>
using namespace rem;
static constexpr int frames=8192;
static std::vector<Stereo> renderNote(Engine &e,int midi,bool osc){
 e.allSoundOff();
 e.params.oscOn=osc;e.params.acousticA=!osc;e.params.acousticB=false;
 e.params.masterBlend=osc?1.f:0.f;
 e.params.masterPresence=64.f/127.f;
 e.params.masterLevel=.5f;
 e.params.attack=.001f;e.params.decay=.02f;e.params.sustain=1.f;
 e.params.release=.08f;
 e.params.grainMix=0;e.params.resoMix=0;
 e.params.sendOn.fill(false);e.params.modOn.fill(false);e.params.env2On=false;
 e.noteOn(midi,1.f);
 std::vector<Stereo> out(frames);
 for(int i=0;i<frames;i+=128)e.render(out.data()+i,128);
 return out;
}
static double diff(const std::vector<Stereo>& a,const std::vector<Stereo>& b){
 double sum=0;
 for(size_t i=0;i<a.size();i++){
  const double l=a[i].l-b[i].l,r=a[i].r-b[i].r;
  sum+=l*l+r*r;
 }return std::sqrt(sum/(2*a.size()));
}
static double stereo(const std::vector<Stereo>& a){
 double s=0;
 for(auto x:a){const double d=x.l-x.r;s+=d*d;}
 return std::sqrt(s/a.size());
}
static bool finite(const std::vector<Stereo>& a){
 for(auto x:a)if(!std::isfinite(x.l)||!std::isfinite(x.r))return false;
 return true;
}
int main(int argc,char **argv){
 if(argc!=2){std::fputs("usage: test_dsp_lab24 Content\n",stderr);return 2;}
 auto e=std::make_unique<Engine>(44100);std::string err;int count=0;
 if(!preloadAllBanks(*e,argv[1],err,count)||count!=254){
  std::printf("ERROR PCM bank: %s; count %d\n",err.c_str(),count);return 1;
 }
 bool ok=true;
 e->params.sourceA=0;e->params.levelA=1.f;
 e->params.acousticNoiseLevel=0.f;
 auto base=renderNote(*e,60,false);
 e->params.acousticNoiseLevel=.7f;e->params.acousticNoiseType=0;
 auto white=renderNote(*e,60,false);
 e->params.acousticNoiseType=1;
 auto pink=renderNote(*e,60,false);
 const double nw=diff(white,base),np=diff(pink,base),wp=diff(white,pink);
 std::printf("ACOUSTIC WHITE/PINK: white=%.6f pink=%.6f distinct=%.6f\n",nw,np,wp);
 ok=ok&&nw>1e-3&&np>1e-3&&wp>1e-3;
 e->params.acousticNoiseLevel=0.f;
 e->params.oscC99Mode=true;e->params.waveform=Wave::Saw;
 e->params.oscLevel=.7f;e->params.oscSpread=64.f/127.f;
 auto center=renderNote(*e,60,true);
 e->params.oscSpread=1.f;auto expanded=renderNote(*e,60,true);
 e->params.oscSpread=0.f;auto reversed=renderNote(*e,60,true);
 std::printf("OSC SPREAD: mono=%.9f wide=%.6f reverse=%.6f\n",
             stereo(center),stereo(expanded),stereo(reversed));
 ok=ok&&stereo(center)<1e-8&&stereo(expanded)>1e-3&&stereo(reversed)>1e-3;
 e->params.oscSpread=64.f/127.f;
 e->params.lowPassOn=true;e->params.lowPassMix=1.f;
 e->params.lowPassCutoff=1500.f;
 e->params.lowPassEnv=56.f/127.f;e->params.lowPassTrack=64.f/127.f;
 auto filterBase=renderNote(*e,72,true);
 e->params.lowPassEnv=.9f;auto env=renderNote(*e,72,true);
 e->params.lowPassEnv=56.f/127.f;e->params.lowPassTrack=.95f;
 auto track=renderNote(*e,72,true);
 std::printf("FILTER ENV/KEY: envDifference=%.6f trackDifference=%.6f\n",
             diff(filterBase,env),diff(filterBase,track));
 ok=ok&&diff(filterBase,env)>1e-3&&diff(filterBase,track)>1e-3;
 for(const auto& a:{base,white,pink,center,expanded,reversed,filterBase,env,track})
  ok=ok&&finite(a);
 std::puts(ok?"PASS LAB24: WHITE/PINK, SPREAD, FILTER ENV, KEY TRACK":
              "FAIL LAB24 DSP");
 return ok?0:1;
}
