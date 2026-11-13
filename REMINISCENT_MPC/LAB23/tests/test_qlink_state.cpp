// LAB23: regression for MPC Q-Link proxy routing and exact VST2 chunk persistence.
// Native test, not hardware MPC proof. SDK provides mpc_vst2_abi.h.
// Build: c++ -std=c++17 -O2 -I<SDK>/framework -o test_qlink_state tests/test_qlink_state.cpp -ldl
// Run:   ./test_qlink_state build/native/reminiscent-lab23.so
#include "mpc_vst2_abi.h"
#include <dlfcn.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
using Entry=AEffect*(*)(audioMasterCallback);
static VstIntPtr host(AEffect*,VstInt32 opcode,VstInt32,VstIntPtr,void*,float){
 return opcode==audioMasterVersion?2400:0;
}
static std::vector<uint8_t> chunk(AEffect* e){
 void* data=nullptr;
 VstIntPtr n=e->dispatcher(e,effGetChunk,0,0,&data,0);
 if(n<=0||!data)return {};
 const auto* b=static_cast<const uint8_t*>(data);
 return std::vector<uint8_t>(b,b+n);
}
int main(int argc,char** argv){
 if(argc!=2){std::fprintf(stderr,"usage: test_qlink_state <native-plugin.so>\n");return 2;}
 void* library=dlopen(argv[1],RTLD_NOW);
 if(!library){std::fprintf(stderr,"dlopen: %s\n",dlerror());return 2;}
 auto entry=reinterpret_cast<Entry>(dlsym(library,"VSTPluginMain"));
 if(!entry){std::fprintf(stderr,"missing VSTPluginMain\n");return 2;}
 AEffect* e=entry(host);
 if(!e||e->numParams!=118){std::fprintf(stderr,"unexpected parameter count\n");return 1;}
 e->dispatcher(e,effOpen,0,0,nullptr,0);
 // Exact host field indices from the approved LAB23 contract: Q1 in each page.
 const int q1targets[11]={19,23,20,29,33,38,42,52,44,80,64};
 int errors=0;
 for(int page=0;page<11;page++){
  e->setParameter(e,112,float(page)/10.f);
  const int target=q1targets[page];
  const float before=e->getParameter(e,target);
  const float wanted=before>.5f?0.f:1.f;
  e->setParameter(e,113,wanted);
  const float got=e->getParameter(e,target);
  const bool pass=std::fabs(got-wanted)<1e-6f;
  std::printf("%s page=%02d Q1 target=%03d expected=%.0f got=%.7f\n",
              pass?"PASS":"FAIL",page,target,wanted,got);
  errors+=!pass;
 }
 // Save normalised parameter values exactly, including 4 Q-Link proxies.
 for(int i=0;i<e->numParams;i++)e->setParameter(e,i,float((i*37)%103)/102.f);
 const auto before=chunk(e);
 for(int i=0;i<e->numParams;i++)e->setParameter(e,i,float((i*53)%89)/88.f);
 const auto ok=e->dispatcher(e,effSetChunk,0,static_cast<VstIntPtr>(before.size()),
                             const_cast<uint8_t*>(before.data()),0);
 const auto after=chunk(e);
 const bool same=!before.empty()&&before==after;
 std::printf("%s exact VST2 save-load-save (%zu bytes, dispatcher=%ld)\n",
             same?"PASS":"FAIL",before.size(),static_cast<long>(ok));
 errors+=!same;
 e->dispatcher(e,effClose,0,0,nullptr,0);
 dlclose(library);
 return errors?1:0;
}
