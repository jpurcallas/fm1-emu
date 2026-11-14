// REminiSCENT LAB20 — MPC SDK integration (STAGING)
// Based on approved Bridge16 DSP and LAB19 27-voice PCM bank; Mac/Linux host test first.
#include "mpc_plugin.h"
#include "engine.hpp"
#include "bank_loader.hpp"
#include "ui07_contract_generated.hpp"
#include <algorithm>
#include <atomic>
#include <array>
#include <cmath>
#include <cstring>
#include <memory>
#include <sstream>
#include <string>
#include <vector>
class REminiSCENTMPC : public mpc::Plugin {
 static constexpr int BLOCK=128;
 std::unique_ptr<rem::Engine> engine_;
 std::array<rem::Stereo,BLOCK> scratch_{};
 std::array<int,ui07::FIELDS.size()> hostIndices_{};
 // LAB21: 11 touch-tabs and dynamic 4-Q-Link proxy routing. The approved 105 DSP parameter indices NEVER change.
 int missingUi_[4]={-1,-1,-1,-1};
 int acousticNoiseType_=-1;
 int selectChar_=-1,selectSend_=-1,selectMod_=-1,tabPage_=-1;
 std::array<int,4> qLinkProxy_{{-1,-1,-1,-1}};
 int selectMemory_=-1;
 // Read-only MPC SDK display channels, appended after the existing 118 parameters.
 int visualLfo_[2]{-1,-1},visualMemory_=-1,visualPlayhead_=-1;
 int splashGroup_=-1,splashFrame_=-1;
 // UI34: HOST-only visual derived from real filter cutoff + ENV + KEY TRACK.
 int visualFilterEffectiveCutoff_=-1,visualFilterFrame_=-1,visualFilterGroup_=-1;
 uint64_t visualSamples_=0;
 uint64_t visualLastTick_=~uint64_t(0);
 int visualSampleRate_=44100;
 // Holds restored preview values until live MIDI restarts audio. Does not
 // freeze any DSP parameter, sound, Q-Link or musical state.
 std::atomic<bool> restoredPreviewHold_{false};
 std::atomic<bool> routing_{false};
 static bool isUiOnly(const char* id){return !strcmp(id,"params.acousticNoise") || !strcmp(id,"params.filterEnv") || !strcmp(id,"params.filterTrack") || !strcmp(id,"params.spread") || !strcmp(id,"selectedChar") || !strcmp(id,"selectedMemory") || !strcmp(id,"selectedMod") || !strcmp(id,"selectedSend");}
public:
 // SDK VST2 chunks serialize every host parameter, including read-only UI
 // telemetry. Mark the new format so a restored project can retain its exact
 // visual snapshot until there is genuine new audio to display.
 void saveExtraState(std::vector<uint8_t>& out) override {
  out.push_back('V');out.push_back('I');out.push_back('1');
 }
 void loadExtraState(const uint8_t* data,size_t size) override {
  if(size>=3&&data[0]=='V'&&data[1]=='I'&&data[2]=='1')
   restoredPreviewHold_.store(true,std::memory_order_release);
 }
 static mpc::PluginInfo info(){mpc::PluginInfo i;i.name="REminiSCENT";i.vendor="Yeti Fingers";i.uniqueId=MPC_FOURCC('R','m','2','0');i.version=2700;i.isInstrument=true;i.numInputs=0;i.numOutputs=2;return i;}
 REminiSCENTMPC():mpc::Plugin(info()){
  hostIndices_.fill(-1);
  for(size_t i=0;i<ui07::FIELDS.size();++i){
    const auto &f=ui07::FIELDS[i];
    if(isUiOnly(f.id))continue;
    std::string label=f.id; for(char &ch:label) if(ch=='.')ch=' ';
    if(std::string(f.kind)=="bool")hostIndices_[i]=addParam(mpc::boolParam(f.id,label.c_str(),f.def!=0));
    else if(std::string(f.kind)=="choice"){
      std::vector<std::string> options; std::stringstream ss(f.choices);std::string item;while(std::getline(ss,item,'|'))options.push_back(item);
      hostIndices_[i]=addParam(mpc::choiceParam(f.id,label.c_str(),options,int(f.def)));
    } else hostIndices_[i]=addParam(mpc::intParam(f.id,label.c_str(),int(f.minimum),int(f.maximum),int(f.def)));
  }
  // Existing parameter IDs and indices stay untouched; new WHITE/PINK
  // acoustic noise colour is a separate MIDI-safe touch choice.
  missingUi_[0]=addParam(mpc::intParam("params.acousticNoise","Acoustic WHITE/PINK level",0,127,0));
  missingUi_[1]=addParam(mpc::intParam("params.spread","Osc stereo spread",0,127,64));
  missingUi_[2]=addParam(mpc::intParam("params.filterEnv","Filter ADSR depth",0,127,56));
  missingUi_[3]=addParam(mpc::intParam("params.filterTrack","LPF key track",0,127,64));
  selectChar_=addParam(mpc::choiceParam("ui.selectedChar","Character edit",{"Distortion","Lo-Fi Tape","Lo-Fi Vinyl","Bit Crush"},1));
  selectSend_=addParam(mpc::choiceParam("ui.selectedSend","Send FX edit",{"Delay","Reverb","Mod 1","Mod 2"},0));
  selectMod_=addParam(mpc::choiceParam("ui.selectedMod","Modulation edit",{"LFO 1","LFO 2","Envelope 2"},0));
  tabPage_=addParam(mpc::choiceParam("ui.page","Touch page",{"Acoustic","OSC","Blend","Envelope","Memory","Resonance","Filter","Character","Granular","Mod","Send FX"},0));
  for(int k=0;k<4;k++){
   std::string id="ui.qlink"+std::to_string(k+1),nm="Q-Link "+std::to_string(k+1);
   qLinkProxy_[k]=addParam(mpc::intParam(id.c_str(),nm.c_str(),0,127,64));
  }
  selectMemory_=addParam(mpc::choiceParam("ui.selectedMemory","Memory edit",{"Freeze","Reverse","Tide"},0));
  // The SDK's Plotter reads these actual DSP signals; none edits the sound.
  visualLfo_[0]=addParam(mpc::intParam("ui.live.lfo1","LFO 1 live signal",0,127,64));
  visualLfo_[1]=addParam(mpc::intParam("ui.live.lfo2","LFO 2 live signal",0,127,64));
  visualMemory_=addParam(mpc::intParam("ui.live.memory","MEMORY live audio",0,127,64));
  visualPlayhead_=addParam(mpc::intParam("ui.live.memoryPhase","MEMORY actual playhead",0,127,0));
  // Solaris v09: 150 source frames, 25 fps, six segments of 25 to stay
  // under the MPC skin renderer's texture height limits.
  splashGroup_=addParam(mpc::choiceParam("ui.splash.group","Solaris frame group",{"0","1","2","3","4","5","DONE"},0));
  splashFrame_=addParam(mpc::intParam("ui.splash.frame","Solaris frame",0,24,0));
  // Append only: old chunks identify all previous parameters by stable ID.
  acousticNoiseType_=addParam(mpc::choiceParam("ui.acousticNoiseType","Acoustic noise colour",{"WHITE","PINK"},0));
  // Append-only visual parameter: does not affect DSP or legacy 125 indices.
  visualFilterEffectiveCutoff_=addParam(mpc::intParam("ui.filter.effectiveCutoff","Filter ENV + KEY response position",0,127,64));
  visualFilterFrame_=addParam(mpc::intParam("ui.filter.visualFrame","Filter visual frame",0,31,0));
  visualFilterGroup_=addParam(mpc::choiceParam("ui.filter.visualGroup","Filter visual group",{"0","1"},0));
  syncQLinks();syncFilterVisual();
 }
 int qLinkTarget(int slot)const{
  // UI field numbers are NOT host parameter numbers: eight UI-only fields were
  // skipped, and four DSP-pending fields were appended. Always resolve through
  // hostIndices_ to prevent Q-Links editing the wrong instrument parameters.
  if(slot<0||slot>=4)return -1;
  static constexpr int fieldQ[][4]={
   {23,25,26,27}, // ACOUSTIC: blend / A level / B level / WHITE/PINK noise amount
   {28,32,33,34}, // OSC: level / tune / harmonics / stereo spread
   {24,30,29,31}, // BLEND: master blend / pitch / output / presence
   {35,36,37,38}, // ENVELOPE ADSR
   {39,40,41,42}, // MEMORY: window / speed / position / shape
   {44,45,46,47}, // RESONANCE
   {48,49,50,51}, // FILTER: cutoff / amp env depth / key track / mix
   {-1,-1,-1,-1},
   {52,53,54,55}, // GRANULAR
   {-1,-1,-1,-1},
   {-1,-1,-1,-1}
  };
  const int page=std::clamp(getInt(tabPage_),0,10);
  int field=fieldQ[page][slot];
  if(page==7)field=56+std::clamp(getInt(selectChar_),0,3)*4+slot;
  if(page==9)field=88+std::clamp(getInt(selectMod_),0,2)*4+slot;
  if(page==10)field=72+std::clamp(getInt(selectSend_),0,3)*4+slot;
  if(field<0 || field>=int(hostIndices_.size()))return -1;
  if(hostIndices_[field]>=0)return hostIndices_[field];
  switch(field){
   case 27:return missingUi_[0];
   case 34:return missingUi_[1];
   case 49:return missingUi_[2];
   case 50:return missingUi_[3];
   default:return -1;
  }
 }
 void syncFilterVisual(){
  if(visualFilterEffectiveCutoff_<0 || hostIndices_[48]<0)return;
  const float cutoff=get(hostIndices_[48]);
  const float env=get(missingUi_[2]), track=get(missingUi_[3]);
  const float effective=std::clamp(cutoff+(env-64.f)*37.f/127.f+(track-64.f)*15.f/127.f,0.f,127.f);
  const int v=int(std::lround(effective));
  if(getInt(visualFilterEffectiveCutoff_)!=v)set(visualFilterEffectiveCutoff_,float(v));
  const int step=std::clamp(int(std::lround(effective*63.f/127.f)),0,63);
  if(getInt(visualFilterFrame_)!=step%32)set(visualFilterFrame_,float(step%32));
  if(getInt(visualFilterGroup_)!=step/32)set(visualFilterGroup_,float(step/32));
 }
 void syncQLinks(){
  for(int k=0;k<4;k++){
   const int target=qLinkTarget(k);if(target<0||qLinkProxy_[k]<0)continue;
   set(qLinkProxy_[k],std::round(127.f*getNormalised(target)));
  }
 }
 void parameterChanged(int index,float plain)override{
  bool expected=false;
  if(!routing_.compare_exchange_strong(expected,true,std::memory_order_acquire))return;
  if(index==tabPage_||index==selectChar_||index==selectSend_||index==selectMod_){syncQLinks();}
  else{
   for(int k=0;k<4;k++){
    int t=qLinkTarget(k);
    if(index==qLinkProxy_[k]&&t>=0){
     // Hardware edits a proxy. Route to the real host parameter so the
     // DSP, direct-touch widgets and animated visuals share ONE state.
     // The routing guard deliberately prevents nested parameterChanged()
     // callbacks, so explicitly recompute derived visual handles below.
     const float next=std::clamp(plain/127.f,0.f,1.f);
     if(std::lround(param(t).toPlain(next))!=getInt(t)){
      setNormalised(t,next);
      if(t==hostIndices_[48] || t==missingUi_[2] || t==missingUi_[3])syncFilterVisual();
     }
    }else if(index==t){
     set(qLinkProxy_[k],std::round(127.f*getNormalised(t)));
    }
   }
  }
  if(index==hostIndices_[48] || index==missingUi_[2] || index==missingUi_[3])syncFilterVisual();
  routing_.store(false,std::memory_order_release);
 }
 bool formatValue(int index,float value,std::string &out)override{
  for(int k=0;k<4;k++)if(index==qLinkProxy_[k]){
   const int target=qLinkTarget(k);
   if(target>=0){
    // All four visible Q-Link positions display a consistent 0..100%,
    // regardless of whether the real DSP parameter is 0..127, signed,
    // an on/off choice, or a categorical parameter. Never change the real
    // parameter's scaling; only the front-panel proxy display is formatted.
    const int pct=std::clamp(int(std::lround(getNormalised(target)*100.f)),0,100);
    out=std::to_string(pct)+" %";
    return true;
   }
  }
  return false;
 }
 void prepare(double sampleRate,int) override {
  visualSampleRate_=std::max(1,int(std::lround(sampleRate)));
  visualSamples_=0;visualLastTick_=~uint64_t(0);
  if(!restoredPreviewHold_.load(std::memory_order_acquire)){
   set(splashGroup_,0.f);set(splashFrame_,0.f);
  }
  // The MPC may prepare repeatedly at different block sizes. Free the previous
  // bank before loading 254 samples again, avoiding 2x memory spikes.
  engine_.reset();
  auto next=std::make_unique<rem::Engine>(int(std::lround(sampleRate)));
  std::string err;int loaded=0;
  const std::string base=mpc::contentPath("");
  if(!rem::preloadAllBanks(*next,base,err,loaded)){mpc::log("PCM BANK FAILED: %s",err.c_str());bankOk_=false;}
  else {mpc::log("PCM BANK loaded: %d samples",loaded);bankOk_=true;}
  next->setPolyphony(8);engine_=std::move(next);
 }
 void reset() override {
  if(engine_)engine_->allSoundOff();
  // Called on state loads as well as fresh resume; never clobber an actual
  // restored snapshot with a new splash startup frame.
  if(!restoredPreviewHold_.load(std::memory_order_acquire)){
   visualSamples_=0;visualLastTick_=~uint64_t(0);
   set(splashGroup_,0.f);set(splashFrame_,0.f);
  }
 }
 void process(mpc::ProcessContext& ctx) override {
  if(!engine_||ctx.numOutputs<1||!ctx.outputs)return;
  std::array<float,ui07::FIELDS.size()> v{};
  for(size_t i=0;i<v.size();i++)v[i]=hostIndices_[i]<0?ui07::FIELDS[i].def:get(hostIndices_[i]);
  applyParams(*engine_,v);
  // These existing host parameters were UI-only in LAB23. Their values now
  // reach the real DSP without renumbering any of the saved 118 parameters.
  engine_->params.acousticNoiseLevel=float(getInt(missingUi_[0]))/127.f;
  engine_->params.oscSpread=float(getInt(missingUi_[1]))/127.f;
  engine_->params.lowPassEnv=float(getInt(missingUi_[2]))/127.f;
  engine_->params.lowPassTrack=float(getInt(missingUi_[3]))/127.f;
  engine_->params.acousticNoiseType=getInt(acousticNoiseType_);
  if(ctx.transport.tempoValid){engine_->params.lfoTempoBpm=std::max(30.f,std::min(300.f,float(ctx.transport.bpm)));}
  int pos=0;
  for(int i=0;i<ctx.numMidiEvents;i++){
    const auto &ev=ctx.midi[i];int at=std::max(pos,std::min(ctx.numFrames,ev.sampleOffset));renderRange(ctx,pos,at);pos=at;
    if(ev.size>=3)engine_->midiMessage(ev.data[0],ev.data[1],ev.data[2]);
  }
  renderRange(ctx,pos,ctx.numFrames);
  // Loading a project resets the DSP engine. With no new notes there is
  // nothing live to display: leave the visual snapshot exactly as saved.
  // On the first real note, resume LFO/MEMORY telemetry and skip the startup
  // splash (which only plays when creating a fresh instance).
  if(restoredPreviewHold_.load(std::memory_order_acquire)){
   if(engine_->activeVoices()==0)return;
   restoredPreviewHold_.store(false,std::memory_order_release);
   visualSamples_=uint64_t(visualSampleRate_)*6u;
   visualLastTick_=~uint64_t(0);
  }
  advanceVisuals(std::max(0,ctx.numFrames));
 }
private:
 // 25 fps UI clock derived from the HOST AUDIO SAMPLE CLOCK, not a visual
 // estimate. Outputs of the real LFO and MEMORY DSP drive the live Plotters.
 // Never call the VST host automation callback from this audio-thread path.
 void advanceVisuals(int renderedFrames){
  visualSamples_+=uint64_t(renderedFrames);
  const uint64_t tick=visualSamples_*25u/uint64_t(visualSampleRate_);
  if(tick==visualLastTick_)return;
  visualLastTick_=tick;
  const int splashTick=int(std::min<uint64_t>(tick,150u));
  const int group=(splashTick>=150)?6:splashTick/25;
  const int frame=(splashTick>=150)?0:splashTick%25;
  if(getInt(splashGroup_)!=group)set(splashGroup_,float(group));
  if(getInt(splashFrame_)!=frame)set(splashFrame_,float(frame));
  if(!engine_)return;
  const auto lfo=engine_->modulationBlackbox();
  for(int k=0;k<2;k++){
   const float signal=std::clamp(lfo[k],-1.f,1.f);
   const int value=std::clamp(int(std::lround(63.5f*(signal+1.f))),0,127);
   if(getInt(visualLfo_[k])!=value)set(visualLfo_[k],float(value));
  }
  const auto m=engine_->memoryBlackbox();
  // True post-MEMORY mono sample, not the simulated HTML buffer.
  const int value=std::clamp(int(std::lround(63.5f*(std::clamp(m.wet,-1.f,1.f)+1.f))),0,127);
  if(getInt(visualMemory_)!=value)set(visualMemory_,float(value));
  const uint32_t span=m.captured?m.capturedWindow:std::min(uint32_t(std::max(1,m.window)),m.available);
  const float rawPhase=span>1?std::clamp(float(m.phaseQ16/65536.0)/float(span-1),0.f,1.f):0.f;
  const float phase=m.reverse?1.f-rawPhase:rawPhase; // exact reverse-read direction
  const int play=std::clamp(int(std::lround(phase*127.f)),0,127);
  if(getInt(visualPlayhead_)!=play)set(visualPlayhead_,float(play));
 }
 bool bankOk_=false;
 static void applyParams(rem::Engine &e,const std::array<float,ui07::FIELDS.size()> &v){
  auto &p=e.params;
  // LAB19 preserves source IDs 0..27 with ID 8 reserved for the removed duduk.
  // UI presents 27 consecutive voices 0..26. Shift indices >=8 by one.
  const auto bankSource=[](float value){const int ui=std::clamp(int(value),0,26);return ui>=8?ui+1:ui;};
  p.sourceA=bankSource(v[0]); p.sourceB=bankSource(v[1]);
  p.levelA=(v[25]/127.f); p.levelB=(v[26]/127.f); p.masterLevel=(v[29]/127.f);
  p.masterPresence=(v[31]/127.f); p.masterOctave=int(v[30]);
  e.setParameter(rem::ParameterId::AcousticAOn,(v[7]>=0.5f)?1.f:0.f);
  e.setParameter(rem::ParameterId::AcousticBOn,(v[8]>=0.5f)?1.f:0.f);
  e.setParameter(rem::ParameterId::AcousticBlend,(v[23]/127.f));
  // No dedicated OSC power host parameter: level=0 is OFF. Raising OSC level enables it.
  e.setParameter(rem::ParameterId::OscOn,(v[28]>0.f)?1.f:0.f);
  e.setParameter(rem::ParameterId::OscWave,v[2]/7.f);
  e.setParameter(rem::ParameterId::OscLevel,(v[28]/127.f));
  e.setParameter(rem::ParameterId::OscOctave,(v[32]+3.f)/6.f);
  e.setParameter(rem::ParameterId::OscHarmonics,(v[33]/127.f));
  e.setParameter(rem::ParameterId::OscC99Mode,1.f);
  e.setParameter(rem::ParameterId::MasterBlend,(v[24]/127.f));
  e.setParameter(rem::ParameterId::Attack,(v[35]/127.f));
  e.setParameter(rem::ParameterId::Decay,(v[36]/127.f));
  e.setParameter(rem::ParameterId::Sustain,(v[37]/127.f));
  e.setParameter(rem::ParameterId::Release,(v[38]/127.f));
  e.setParameter(rem::ParameterId::MemoryFreeze,(v[9]>=0.5f)?1.f:0.f);
  e.setParameter(rem::ParameterId::MemoryReverse,(v[10]>=0.5f)?1.f:0.f);
  e.setParameter(rem::ParameterId::MemoryTide,(v[11]>=0.5f)?1.f:0.f);
  e.setParameter(rem::ParameterId::MemoryMix,(v[43]/127.f));
  e.setParameter(rem::ParameterId::MemoryWindow,(v[39]/127.f));
  e.setParameter(rem::ParameterId::MemorySpeed,(v[40]/127.f));
  e.setParameter(rem::ParameterId::MemoryPosition,(v[41]/127.f));
  e.setParameter(rem::ParameterId::MemoryShape,(v[42]/127.f));
  e.setParameter(rem::ParameterId::LowPassCutoff,(v[48]/127.f));
  e.setParameter(rem::ParameterId::LowPassMix,(v[51]/127.f));
  e.setParameter(rem::ParameterId::LowPassOn,(v[51]/127.f)>0.f?1.f:0.f);
  p.grainSize=(v[52]/127.f);
  p.grainDensity=(v[53]/127.f);
  p.grainPos=(v[54]/127.f);
  p.grainMix=(v[55]/127.f);
  p.resoBody=(v[44]/127.f);
  p.resoDecay=(v[45]/127.f);
  p.resoExcite=(v[46]/127.f);
  p.resoMix=(v[47]/127.f);
  p.characterOn[0]=(v[12]>=0.5f);
  p.character[0][0]=(v[56]/127.f);
  p.character[0][1]=(v[57]/127.f);
  p.character[0][2]=(v[58]/127.f);
  p.character[0][3]=(v[59]/127.f);
  p.characterOn[1]=(v[13]>=0.5f);
  p.character[1][0]=(v[60]/127.f);
  p.character[1][1]=(v[61]/127.f);
  p.character[1][2]=(v[62]/127.f);
  p.character[1][3]=(v[63]/127.f);
  p.characterOn[2]=(v[14]>=0.5f);
  p.character[2][0]=(v[64]/127.f);
  p.character[2][1]=(v[65]/127.f);
  p.character[2][2]=(v[66]/127.f);
  p.character[2][3]=(v[67]/127.f);
  p.characterOn[3]=(v[15]>=0.5f);
  p.character[3][0]=(v[68]/127.f);
  p.character[3][1]=(v[69]/127.f);
  p.character[3][2]=(v[70]/127.f);
  p.character[3][3]=(v[71]/127.f);
  p.sendOn[0]=(v[16]>=0.5f);
  p.send[0][0]=(v[72]/127.f);
  p.send[0][1]=(v[73]/127.f);
  p.send[0][2]=(v[74]/127.f);
  p.send[0][3]=(v[75]/127.f);
  p.sendOn[1]=(v[17]>=0.5f);
  p.send[1][0]=(v[76]/127.f);
  p.send[1][1]=(v[77]/127.f);
  p.send[1][2]=(v[78]/127.f);
  p.send[1][3]=(v[79]/127.f);
  p.sendOn[2]=(v[18]>=0.5f);
  p.send[2][0]=(v[80]/127.f);
  p.send[2][1]=(v[81]/127.f);
  p.send[2][2]=(v[82]/127.f);
  p.send[2][3]=(v[83]/127.f);
  p.sendOn[3]=(v[19]>=0.5f);
  p.send[3][0]=(v[84]/127.f);
  p.send[3][1]=(v[85]/127.f);
  p.send[3][2]=(v[86]/127.f);
  p.send[3][3]=(v[87]/127.f);
  p.sendAlgorithm[0]=int(v[111]);
  p.sendAlgorithm[1]=int(v[112]);
  p.modOn[0]=(v[20]>=0.5f);
  p.mod[0][0]=(v[88]/127.f);
  p.mod[0][1]=(v[89]/127.f);
  p.mod[0][2]=(v[90]/127.f);
  p.mod[0][3]=(v[91]/127.f);
  p.lfoSync[0]=(v[105]>=0.5f);
  p.lfoRetrigger[0]=(v[107]>=0.5f);
  p.lfoDivision[0]=int(v[106]);
  p.modOn[1]=(v[21]>=0.5f);
  p.mod[1][0]=(v[92]/127.f);
  p.mod[1][1]=(v[93]/127.f);
  p.mod[1][2]=(v[94]/127.f);
  p.mod[1][3]=(v[95]/127.f);
  p.lfoSync[1]=(v[108]>=0.5f);
  p.lfoRetrigger[1]=(v[110]>=0.5f);
  p.lfoDivision[1]=int(v[109]);
  p.env2On=(v[22]>=0.5f);
  p.lfoTempoBpm=v[104];
  p.modDestination[0]=int(v[100]);
  p.modDestination[1]=int(v[101]);
  p.modDestination[2]=int(v[102]);
  p.env2[0]=(v[96]/127.f);
  p.env2[1]=(v[97]/127.f);
  p.env2[2]=(v[98]/127.f);
  p.env2[3]=(v[99]/127.f);
  p.env2Amount=(v[103]/127.f);
 }
 void renderRange(mpc::ProcessContext& ctx,int start,int end){
  for(int pos=start;pos<end;){int n=std::min(BLOCK,end-pos);engine_->render(scratch_.data(),n);
   for(int j=0;j<n;j++){ctx.outputs[0][pos+j]=scratch_[j].l;if(ctx.numOutputs>1&&ctx.outputs[1])ctx.outputs[1][pos+j]=scratch_[j].r;}pos+=n;}
 }
};
MPC_PLUGIN_ENTRY(REminiSCENTMPC)