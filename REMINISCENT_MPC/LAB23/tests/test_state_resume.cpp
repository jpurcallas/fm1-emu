// LAB24 regression: project-state restore must not overwrite read-only preview
// channels during silent rendering, but must resume them at the next MIDI note.
// Native host only; this does not certify physical MPC skin rendering.
// Build: c++ -std=c++17 -O2 -I<SDK>/framework -o test_state_resume tests/test_state_resume.cpp -ldl
// Run: ./test_state_resume build/native/reminiscent-lab24-state-fixed.so
#include "mpc_vst2_abi.h"
#include <dlfcn.h>
#include <cstdio>
#include <vector>
using Entry=AEffect*(*)(audioMasterCallback);
static VstIntPtr cb(AEffect*,VstInt32 op,VstInt32,VstIntPtr,void*,float){
 return op==audioMasterVersion?2400:0;
}
static std::vector<unsigned char> save(AEffect* e){
 void* v=nullptr;
 VstIntPtr n=e->dispatcher(e,effGetChunk,0,0,&v,0);
 return n>0?std::vector<unsigned char>((unsigned char*)v,(unsigned char*)v+n):std::vector<unsigned char>();
}
int main(int argc,char** argv){
 if(argc!=2)return 2;
 void* h=dlopen(argv[1],RTLD_NOW);
 if(!h){std::printf("FAIL %s\n",dlerror());return 2;}
 auto factory=(Entry)dlsym(h,"VSTPluginMain");
 if(!factory)return 2;
 auto e=factory(cb);
 e->dispatcher(e,effOpen,0,0,nullptr,0);
 e->dispatcher(e,effSetSampleRate,0,0,nullptr,44100.f);
 e->dispatcher(e,effSetBlockSize,0,128,nullptr,0);
 e->dispatcher(e,effMainsChanged,0,1,nullptr,0);
 for(int i=118;i<=123;i++)e->setParameter(e,i,float((i*19)%97)/96.f);
 const auto before=save(e);
 for(int i=118;i<=123;i++)e->setParameter(e,i,float((i*29)%99)/98.f);
 e->dispatcher(e,effSetChunk,0,before.size(),(void*)before.data(),0);
 float l[128]={},r[128]={};float* outs[2]={l,r};
 for(int n=0;n<20;n++)e->processReplacing(e,nullptr,outs,128);
 const auto silence=save(e);
 const bool preserved=!before.empty()&&before==silence;
 VstMidiEvent note{};
 note.type=kVstMidiType;note.byteSize=sizeof(note);
 note.midiData[0]=char(0x90);note.midiData[1]=60;note.midiData[2]=110;
 VstEvents ev{};ev.numEvents=1;ev.events[0]=reinterpret_cast<VstEvent*>(&note);
 e->dispatcher(e,effProcessEvents,0,0,&ev,0);
 for(int n=0;n<20;n++)e->processReplacing(e,nullptr,outs,128);
 const auto live=save(e);
 const bool resumed=(live!=silence)&&(e->getParameter(e,122)>0.99f);
 std::printf("%s save-load-save byte-exact during silent render (%zu bytes)\n",
             preserved?"PASS":"FAIL",before.size());
 std::printf("%s visuals resumed on next note; Solaris stayed DONE\n",
             resumed?"PASS":"FAIL");
 e->dispatcher(e,effClose,0,0,nullptr,0);dlclose(h);
 return (preserved&&resumed)?0:1;
}
