// UI41: real host callback must receive Q-Link proxy automation
// when a page's target parameter changes through touch/Data Wheel.
#include "mpc_vst2_abi.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <vector>
using Entry=AEffect* (*)(audioMasterCallback);
static std::vector<int> notifications;
static VstIntPtr host(AEffect*, VstInt32 opcode,VstInt32 index,VstIntPtr,void*,float){
 if(opcode==audioMasterAutomate)notifications.push_back(index);
 return opcode==audioMasterVersion?2400:0;
}
static bool has(int index){return std::find(notifications.begin(),notifications.end(),index)!=notifications.end();}
int main(int argc,char** argv){
 if(argc!=2)return 2;
 void* h=dlopen(argv[1],RTLD_NOW);
 if(!h){std::fprintf(stderr,"dlopen: %s\n",dlerror());return 2;}
 auto entry=(Entry)dlsym(h,"VSTPluginMain");
 if(!entry)return 2;
 AEffect* fx=entry(host);
 if(!fx||fx->numParams<130){std::fprintf(stderr,"unexpected UI39+ parameter count\n");return 1;}
 fx->dispatcher(fx,effOpen,0,0,nullptr,0);
 int n=0;
 for(int page: {5,6,8}){
  const int targetStart=(page==5?38:page==6?42:44);
  fx->setParameter(fx,112,float(page)/10.f);
  for(int k=0;k<4;++k){
   const int target=(page==6 && k==1)?107:(page==6&&k==2)?108:(page==6&&k==3)?43:targetStart+k;
   // Exceed the current default so this is an actual edit rather than no-op.
   const float before=fx->getParameter(fx,target);
   const float next=before>.5f?.13f:.87f;
   notifications.clear();
   fx->setParameter(fx,target,next);
   if(!has(113+k)){std::fprintf(stderr,"NO proxy automation: page %d Q%d target %d\n",page,k+1,target);++n;}
   const float proxy=fx->getParameter(fx,113+k);
   if(std::fabs(proxy-next)>0.02f){std::fprintf(stderr,"PROXY STALE page %d Q%d: %.2f wanted %.2f\n",page,k+1,proxy,next);++n;}
  }
 }
 fx->dispatcher(fx,effClose,0,0,nullptr,0);
 dlclose(h);
 if(n)return 1;
 std::puts("PASS: host receives Q-Link proxy notification for 12 direct touch/Data Wheel edits");
}
