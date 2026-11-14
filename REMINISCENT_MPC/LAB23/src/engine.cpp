#include "engine.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <cstring>
#if defined(__unix__) || defined(__APPLE__)
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#endif
#define RN_TABLE
#include "rn_osc_tables.inc"
#undef RN_TABLE

namespace rem {
static constexpr double PI=3.14159265358979323846;
static float clamp(float x,float a,float b){return std::max(a,std::min(x,b));}
const Sample* Bank::nearest(int note) const {const Sample* best=nullptr;int dist=9999;for(auto& s:layers){int d=std::abs(note-s.root);if(d<dist){best=&s;dist=d;}}return best;}
static uint16_t rd16(const uint8_t* p){return uint16_t(p[0])|(uint16_t(p[1])<<8);}
static uint32_t rd32(const uint8_t* p){return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);}
bool Bank::loadWav(const std::string& path,int root,std::string& err){
 std::ifstream f(path,std::ios::binary);if(!f){err="No se puede abrir "+path;return false;}
 uint8_t head[12];if(!f.read((char*)head,12)||memcmp(head,"RIFF",4)||memcmp(head+8,"WAVE",4)){err="Formato RIFF/WAVE inválido";return false;}
 int format=0,ch=0,bits=0,rate=0;size_t dataSize=0;std::streamoff dataOffset=-1;
 while(f){uint8_t h[8];if(!f.read((char*)h,8))break;uint32_t n=rd32(h+4);std::string id((char*)h,4);
  if(n>300000000){err="Chunk WAV excesivo";return false;}
  if(id=="fmt "){std::vector<uint8_t> b(n);if(!f.read((char*)b.data(),n)||n<16){err="fmt roto";return false;}format=rd16(b.data());ch=rd16(b.data()+2);rate=rd32(b.data()+4);bits=rd16(b.data()+14);}
  else if(id=="data"){dataOffset=f.tellg();dataSize=n;f.seekg(n,std::ios::cur);}
  else f.seekg(n,std::ios::cur);
  if(n&1)f.seekg(1,std::ios::cur);
 }
 if(ch<1||ch>2||rate<8000||rate>192000||!((format==1&&(bits==16||bits==24||bits==32))||(format==3&&bits==32))){err="WAV no soportado (PCM16/24/32 o FLOAT32)";return false;}
 if(dataOffset<0||!dataSize){err="WAV sin audio";return false;}
 int bps=bits/8;size_t frames=dataSize/(bps*ch);if(frames==0){err="WAV sin audio";return false;}
 Sample s;s.root=root;s.rate=rate;s.channels=ch;s.bits=bits;s.wavFormat=format;s.frames=frames;
 // Read-only map of the exact PCM on disk: no format conversion and no
 // allocation/copy of the full 372 MB bank before the instrument opens.
 // The OS pages source data as required; physical MPC timing remains to test.
#if defined(__unix__) || defined(__APPLE__)
 int fd=::open(path.c_str(),O_RDONLY);
 if(fd>=0){struct stat st{};if(::fstat(fd,&st)==0&&st.st_size>0&&
     uint64_t(dataOffset)+uint64_t(dataSize)<=uint64_t(st.st_size)){
   const size_t fileSize=size_t(st.st_size);
   void* mem=::mmap(nullptr,fileSize,PROT_READ,MAP_PRIVATE,fd,0);
   if(mem!=MAP_FAILED){
    s.mappedPcm=std::shared_ptr<const uint8_t>(static_cast<const uint8_t*>(mem),[fileSize](const uint8_t* p){::munmap(const_cast<uint8_t*>(p),fileSize);});
    s.mappedOffset=size_t(dataOffset);
   }
  }
  ::close(fd);
 }
#endif
 if(!s.mappedPcm){
  // Same lossless source, portable fallback if file mapping is unavailable.
  f.clear();f.seekg(dataOffset);
  s.pcm.resize(dataSize);
  if(!f.read(reinterpret_cast<char*>(s.pcm.data()),std::streamsize(dataSize))){err="data roto";return false;}
 }
 layers.push_back(std::move(s));return true;
}
void Engine::setPolyphony(int n){limit=std::max(1,std::min(MAX_VOICES,n));for(int i=limit;i<MAX_VOICES;i++)voices[i].active=false;}
void Engine::noteOn(int note,float velocity){ if(note<0||note>127) return; velocity=clamp(velocity,0.f,1.f); if(velocity<=0.f){noteOff(note);return;} int idx=-1;for(int i=0;i<limit;i++)if(!voices[i].active){idx=i;break;}
 if(idx<0){for(int i=0;i<limit;i++)if(!voices[i].held){if(idx<0||voices[i].born<voices[idx].born)idx=i;}}
 if(idx<0){idx=0;for(int i=1;i<limit;i++)if(voices[i].born<voices[idx].born)idx=i;}
 Voice v;v.active=true;v.held=true;v.velocity=velocity;v.note=note;v.noiseSeed=0xa341316cu^(uint32_t(note)*0x9e3779b9u);if(!v.noiseSeed)v.noiseSeed=1;
 v.acousticNoiseSeed=0x6e624eb7u^(uint32_t(note)*0x85ebca6bu)^uint32_t(clock);
 if(!v.acousticNoiseSeed)v.acousticNoiseSeed=1;
 v.born=++clock;// LAB19: loaded source A and source B are held in their dedicated banks.
 v.a=(params.sourceA>=0 && params.sourceA<28 && !sourceBanks[params.sourceA].layers.empty())?sourceBanks[params.sourceA].nearest(note):bankA.nearest(note);
 v.b=(params.sourceB==10 && !didgeridooB.layers.empty())?didgeridooB.nearest(note):((params.sourceB>=0 && params.sourceB<28 && !sourceBanks[params.sourceB].layers.empty())?sourceBanks[params.sourceB].nearest(note):bankB.nearest(note));v.stage=Voice::Stage::Attack;
 if(v.a)v.rateA=std::pow(2.,double(note-v.a->root)/12.-double(v.a->tuneCents)/1200.)*v.a->rate/sr;
 if(v.b)v.rateB=std::pow(2.,double(note-v.b->root)/12.-double(v.b->tuneCents)/1200.)*v.b->rate/sr;
 voices[idx]=v;
 // KEY retrigger applies globally to the selected LFO; FREE never resets phase.
 for(int l=0;l<2;l++)if(params.lfoRetrigger[l]){modulation.cycle[l]=0.f;}
}
void Engine::startRelease(Voice& v){v.held=false;v.sustainHeld=false;v.stage=Voice::Stage::Release;v.releaseDelta=v.level/std::max(1.f,params.release*sr);
 v.env2Stage=Voice::Stage::Release;
 v.env2ReleaseDelta=v.env2Level/std::max(1.f,(.005f+3.f*params.env2[3])*sr);
}
void Engine::noteOff(int note){
 // Release the most recently pressed matching note, not all overlapping voices.
 Voice* newest=nullptr;
 for(int i=0;i<limit;i++){auto& v=voices[i];if(v.active&&v.held&&v.note==note&&(!newest||v.born>newest->born))newest=&v;}
 if(!newest)return;
 if(pedalDown){newest->held=false;newest->sustainHeld=true;}
 else startRelease(*newest);
}
void Engine::allNotesOff(){for(auto& v:voices)if(v.active)startRelease(v);}
void Engine::allSoundOff(){for(auto& v:voices)v=Voice{}; memory.clear();granular.clear();resonance.clear();character.clear();sendFx.clear();modulation.clear();presenceLP={};lpL=lpR=0;pedalDown=false;}
void Engine::midiMessage(uint8_t st,uint8_t d1,uint8_t d2){
 switch(st&0xf0){
 case 0x90: if(d2) noteOn(d1,d2/127.f);else noteOff(d1);break;
 case 0x80: noteOff(d1);break;
 case 0xb0:
   if(d1==64){bool down=d2>=64;if(pedalDown&&!down){for(auto& v:voices)if(v.active&&v.sustainHeld)startRelease(v);}pedalDown=down;}
   else if(d1==123)allNotesOff();
   else if(d1==120)allSoundOff();
   break;
 default:break;
 }
}
float Engine::envelope(Voice& v){switch(v.stage){
 case Voice::Stage::Attack:v.level+=1.f/std::max(1.f,params.attack*sr);if(v.level>=1){v.level=1;v.stage=Voice::Stage::Decay;}break;
 case Voice::Stage::Decay:v.level-=(1.f-params.sustain)/std::max(1.f,params.decay*sr);if(v.level<=params.sustain){v.level=params.sustain;v.stage=Voice::Stage::Sustain;}break;
 case Voice::Stage::Sustain:v.level=params.sustain;break;
 case Voice::Stage::Release:v.level-=v.releaseDelta;if(v.level<=0){v.level=0;v.active=false;}break;
 }return v.level;}
float Engine::env2Tick(Voice& v){
 if(!params.env2On)return 0.f;
 const float a=std::max(1.f,(.005f+3.f*params.env2[0])*sr);
 const float d=std::max(1.f,(.005f+3.f*params.env2[1])*sr);
 const float sustain=clamp(params.env2[2],0.f,1.f);
 switch(v.env2Stage){
 case Voice::Stage::Attack:v.env2Level+=1.f/a;if(v.env2Level>=1.f){v.env2Level=1.f;v.env2Stage=Voice::Stage::Decay;}break;
 case Voice::Stage::Decay:v.env2Level-=(1.f-sustain)/d;if(v.env2Level<=sustain){v.env2Level=sustain;v.env2Stage=Voice::Stage::Sustain;}break;
 case Voice::Stage::Sustain:v.env2Level=sustain;break;
 case Voice::Stage::Release:v.env2Level=std::max(0.f,v.env2Level-v.env2ReleaseDelta);break;
 }
 return v.env2Level*clamp(params.env2Amount,0.f,1.f);
}
// Read only the two neighboring frames needed for interpolation; source PCM is untouched.
static Stereo decodeFrame(const Sample& s, size_t frame){
 const size_t bps=size_t(s.bits/8);
 const uint8_t* p=s.pcmData()+frame*size_t(s.channels)*bps;
 auto val=[&](const uint8_t* b)->float{
  if(s.wavFormat==3){float v;memcpy(&v,b,4);return v;}
  if(s.bits==16)return float(int16_t(rd16(b)))/32768.f;
  if(s.bits==24){int32_t x=int32_t(b[0])|(int32_t(b[1])<<8)|(int32_t(b[2])<<16);if(x&0x800000)x|=~0xffffff;return float(x)/8388608.f;}
  return float(int32_t(rd32(b)))/2147483648.f;
 };
 return {val(p), val(p+size_t(s.channels-1)*bps)};
}
Stereo Engine::sampleAt(const Sample* s,double pos) const {
 if(!s||s->frames<2||pos<0||pos>=double(s->frames-1))return {};
 const size_t i=size_t(pos); const float t=float(pos-i);
 const Stereo a=decodeFrame(*s,i),b=decodeFrame(*s,i+1);
 Stereo y{a.l*(1-t)+b.l*t,a.r*(1-t)+b.r*t};
 // Preserve the exact previously-approved boundary-taper logic.
 const Stereo last=decodeFrame(*s,s->frames-1);
 if(std::max(std::abs(last.l),std::abs(last.r))>.015f){
  const double rem=double(s->frames-1)-pos;
  const double fadeFrames=std::max(64.,s->rate*.018);
  if(rem<fadeFrames){const float g=float(std::max(0.,rem/fadeFrames));y.l*=g;y.r*=g;}
 }
 return y;
}
float Engine::oscillator(Voice& v,float pitchSemitone,float pulseWidth){
 const float effectivePulse=clamp(pulseWidth<0.f?params.pulseWidth:pulseWidth,.05f,.95f);
 double f=440.*std::pow(2.,(v.note+(params.octave+params.masterOctave)*12+pitchSemitone-69)/12.);
 if(params.oscC99Mode){
  // The same eight sine-series coefficient sets and Q15 sine table from rn_osc.c.
  // Q32 phase increments are adapted to the current host sample rate (original=44100).
  if(!(f<sr*.5))return 0.f;
  uint32_t inc=uint32_t(std::llround(f*(4294967296.0/double(sr))));
  const int wave=std::max(0,std::min(7,int(params.waveform)));
  const uint8_t harm=uint8_t(std::lround(clamp(params.oscHarmonics,0,1)*127));
  const uint8_t width=uint8_t(std::lround(clamp(effectivePulse,0.f,1.f)*127));
  auto sineQ15=[](uint32_t phase)->int32_t{
   unsigned idx=phase>>23,frac=(phase>>14)&511u;
   int32_t a=rn_sine_q15[idx],b=rn_sine_q15[(idx+1u)&511u];
   return a+((b-a)*int32_t(frac))/512;
  };
  int32_t sum=0;
  uint32_t phase=v.phaseQ32,hp=phase;
  const uint32_t duty=13u+(uint32_t(width)*102u+63u)/127u;
  for(int h=1;h<=8;h++){
   if(uint64_t(inc)*h>=0x80000000ull)break;
   int32_t coef=0;
   if(wave==4){
    uint32_t angle=uint32_t((uint64_t(duty)*uint32_t(h)<<31)/128u);
    coef=(sineQ15(angle)*12500)/(32767*h);
   }else coef=rn_coeff[wave][h-1];
   if(h>1)coef=coef*harm/127;
   if(coef)sum+=(sineQ15(hp)*coef)/32768;
   hp+=phase;
  }
  v.phaseQ32+=inc;
  sum=std::max(-18000,std::min(18000,sum));
  if(params.oscNoiseType&&params.noiseLevel>0){
   uint32_t x=v.noiseSeed;x^=x<<13;x^=x>>17;x^=x<<5;v.noiseSeed=x;
   int32_t white=int32_t(x>>16)-32768,n=white;
   if(params.oscNoiseType==2){
    v.pinkFast+=(white-v.pinkFast)/8;
    v.pinkMid+=(white-v.pinkMid)/32;
    v.pinkSlow+=(white-v.pinkSlow)/128;
    n=(v.pinkFast+v.pinkMid+v.pinkSlow)/3;
   }
   int level=int(std::lround(clamp(params.noiseLevel,0,1)*127));
   sum+=n*level/(127*3);
  }
  sum=std::max(-32768,std::min(32767,sum));
  return float(sum)/32768.f;
 }
 double p=v.phase;v.phase+=f/sr;v.phase-=std::floor(v.phase);
 switch(params.waveform){case Wave::Sine:return std::sin(2*PI*p);case Wave::Triangle:return float(4*std::abs(p-.5)-1);case Wave::Saw:return float(2*p-1);case Wave::Square:return p<.5?1.f:-1.f;case Wave::Pulse:return p<effectivePulse?1.f:-1.f;
 // The three following are provisional *placeholders*, not the original C99 algorithms.
 case Wave::Organ:return float(.7*std::sin(2*PI*p)+.2*std::sin(4*PI*p)+.1*std::sin(6*PI*p));
 case Wave::Bright:return float(.5*std::sin(2*PI*p)+.3*std::sin(6*PI*p)+.2*std::sin(10*PI*p));
 case Wave::Hollow:return float(.7*std::sin(2*PI*p)+.3*std::sin(6*PI*p));}
 return 0;}
// Acoustic WHITE/PINK, independent of the existing OSC noise and sample PCM.
// PINK is a 16-row Voss-McCartney octave noise source (no loops or sample edits).
static float acousticNoiseNext(Voice &v,int type){
 auto white=[&](){uint32_t x=v.acousticNoiseSeed;x^=x<<13;x^=x>>17;x^=x<<5;
  v.acousticNoiseSeed=x;return (float(int32_t(x>>16))-32768.f)/32768.f;};
 const float w=white();
 if(type==0)return w;
 const uint32_t count=++v.acousticPinkCounter;
 int row=0;while(row<15&&(count&(1u<<row))==0)++row;
 const float next=white();
 v.acousticPinkSum+=next-v.acousticPinkRows[row];
 v.acousticPinkRows[row]=next;
 return clamp((v.acousticPinkSum+w)*(2.6f/17.f),-1.f,1.f);
}
void Engine::render(Stereo* out,int frames){if(!out||frames<=0)return;const double masterPitchRatio=std::ldexp(1.,std::max(-2,std::min(2,params.masterOctave)));params.acousticBlend=clamp(params.acousticBlend,0,1);params.masterBlend=clamp(params.masterBlend,0,1);params.sustain=clamp(params.sustain,0,1);resonance.configure(params,sr);
 for(int i=0;i<frames;i++){
 const auto lfo=modulation.tick(params,sr);
 uiLastLfo_=lfo; // visual telemetry only, does not enter audio routing
 float routed[6]={};
 float ampLfoDepth=0.f;
 for(int k=0;k<2;k++){
  int dest=std::max(0,std::min(5,params.modDestination[k]));
  const float depth=clamp(params.mod[k][1],0.f,1.f);
  routed[dest]+=lfo[k]*depth;
  if(dest==2 && params.modOn[k])ampLfoDepth+=depth;
 }
 double L=0,R=0;
 float maxEnvCutoff=0.f;
 // Bridge16 has one shared post-voice LPF. Track a velocity-weighted
 // keyboard centroid and envelope level without replacing that filter.
 float filterWeight=0.f,filterEnvelopeWeighted=0.f,filterNoteWeighted=0.f;
 // Independent ENV2 ticks once per voice per frame, separate from AMP ADSR.
 for(int j=0;j<limit;j++){auto& v=voices[j];if(!v.active)continue;float gain=envelope(v);if(!v.active)continue;
 const float filterVoiceWeight=gain*v.velocity;
 filterWeight+=filterVoiceWeight;
 filterEnvelopeWeighted+=gain*filterVoiceWeight;
 filterNoteWeighted+=float(v.note-60)*filterVoiceWeight;
 float env=env2Tick(v); // unipolar independent envelope
 const bool envActive=params.env2On&&env>0.f;
 const int envDest=params.modDestination[2];
 float lane[6];for(int k=0;k<6;k++)lane[k]=routed[k];
 if(envActive&&envDest>=0&&envDest<6)lane[envDest]+=env;
 if(envActive&&envDest==1)maxEnvCutoff=std::max(maxEnvCutoff,env);
 const float pitchSemitone=lane[0]; // +/-1 semitone per full-scale modulation source
 const double pitchRatio=std::pow(2.0,double(pitchSemitone)/12.0);
 Stereo a=params.acousticA?sampleAt(v.a,v.posA):Stereo{};Stereo b=params.acousticB?sampleAt(v.b,v.posB):Stereo{};
 v.posA+=v.rateA*masterPitchRatio*pitchRatio;v.posB+=v.rateB*masterPitchRatio*pitchRatio;
 float ab=clamp(params.acousticBlend,0.f,1.f);
 float ga=params.acousticA?(params.acousticB?1-ab:1):0;
 float gb=params.acousticB?(params.acousticA?ab:1):0;
 float pw=clamp(params.pulseWidth+.40f*lane[5],.05f,.95f);
 float s=params.oscOn?oscillator(v,pitchSemitone,pw)*params.oscLevel:0;
 // OSC SPREAD: phase decorrelation of left/right without modifying the
 // original oscillator state. At 64/127 the output is unchanged.
 float oscSide=0.f;
 const float spread=clamp(params.oscSpread,0.f,1.f)-64.f/127.f;
 if(params.oscOn&&std::abs(spread)>1e-7f){
  Voice shifted=v; shifted.phaseQ32+=0x20000000u;
  shifted.phase+=.125;shifted.phase-=std::floor(shifted.phase);
  const float shiftedSample=oscillator(shifted,pitchSemitone,pw)*params.oscLevel;
  oscSide=(shiftedSample-s)*(.8f*spread);
 }
 // Calibrated from PCM sample RMS (piano ~ -35dBFS, mbira ~ -34dBFS).
 // Preview Bridge02 OSC was masking the physical instruments by >10dB.
 // A/B remain individually controllable; headroom checked for eight MIDI voices.
 constexpr float ACOUSTIC_GAIN=3.4f;
 float acL=ACOUSTIC_GAIN*(a.l*ga*params.levelA+b.l*gb*params.levelB);
 float acR=ACOUSTIC_GAIN*(a.r*ga*params.levelA+b.r*gb*params.levelB);
 // Independent ACOUSTIC noise under the existing ADSR/velocity. Muted at
 // its saved default (0), preserving the exact original acoustic samples.
 if((params.acousticA||params.acousticB)&&params.acousticNoiseLevel>0.f){
  const float noise=.12f*clamp(params.acousticNoiseLevel,0.f,1.f)*
   acousticNoiseNext(v,params.acousticNoiseType);
  acL+=noise;acR+=noise;
 }
 float masterBlend=clamp(params.masterBlend+.5f*lane[4],0.f,1.f);
 float am=(params.acousticA||params.acousticB)?(params.oscOn?1-masterBlend:1):0;
 float sm=params.oscOn?((params.acousticA||params.acousticB)?masterBlend:1):0;
 // AMP: bipolar LFO conventional tremolo (0..1), ENV2 unipolar gain 0..1.
 float amp=clamp(1.f-.5f*(ampLfoDepth-routed[2]),0.f,1.f);
 if(envActive&&envDest==2)amp*=clamp((1.f-params.env2Amount)+env,0.f,1.f);
 float pan=clamp(lane[3],-1.f,1.f);
 const float vl=(acL*am+(s+oscSide)*sm)*gain*v.velocity*amp;
 const float vr=(acR*am+(s-oscSide)*sm)*gain*v.velocity*amp;
 L+=vl*(1.f-pan);R+=vr*(1.f+pan);
 }
 Stereo dry{float(L),float(R)};
 const float mono=(dry.l+dry.r)*.5f;
 const float wet=memory.process(mono,params,sr);
 debugLastMono=mono;debugLastWet=wet;
 // v1.5 reference: bypass if no mode, wet mono with stereo dry retained.
 const bool memActive=params.memoryMix>0.f&&(params.memoryFreeze||params.memoryReverse||params.memoryTide);
 (void)memActive;
 float delta=wet-mono;
 Stereo mix{dry.l+delta,dry.r+delta};
 mix=granular.process(mix,params,sr);
 mix=resonance.process(mix,params);
 mix=character.process(mix,params,sr);
 if(params.lowPassOn){
   // LFO2 sweeps cutoff up/down, up to 3 octaves in conventional filter modulation.
   const float envDepth=2.f*(clamp(params.lowPassEnv,0.f,1.f)-56.f/127.f);
   const float trackDepth=2.f*(clamp(params.lowPassTrack,0.f,1.f)-64.f/127.f);
   const float avgAmpEnv=filterWeight>0.f?filterEnvelopeWeighted/filterWeight:0.f;
   const float avgNote=filterWeight>0.f?filterNoteWeighted/filterWeight:0.f;
   // New depth controls are bipolar: their LAB23 stored defaults are
   // neutral, and neither replaces the previously approved LPF.
   const float cutoffOctaves=3.f*(routed[1]+maxEnvCutoff)+
       3.f*envDepth*avgAmpEnv+trackDepth*avgNote/12.f;
   float hz=clamp(params.lowPassCutoff*std::pow(2.f,cutoffOctaves),20.f,sr*.46f);
   float alpha=1.f-std::exp(-2.f*float(PI)*hz/sr);
   lpL+=alpha*(mix.l-lpL);lpR+=alpha*(mix.r-lpR);
   float lm=clamp(params.lowPassMix,0.f,1.f);
   mix.l=mix.l*(1-lm)+lpL*lm;mix.r=mix.r*(1-lm)+lpR*lm;
 }else{lpL=mix.l;lpR=mix.r;}
 mix=sendFx.process(mix,params,sr);
 // MASTER PRESENCE: a broad, musically audible spectral tilt from about
 // 850 Hz, neutral exactly at 64/127. The previous 2.2kHz +/-6dB shelf was
 // effectively invisible on many soft/acoustic timbres. This is +/-12dB.
 const float alpha=1.f-std::exp(-2.f*float(PI)*850.f/sr);
 presenceLP.l+=alpha*(mix.l-presenceLP.l);
 presenceLP.r+=alpha*(mix.r-presenceLP.r);
 const float center=64.f/127.f;
 const float presence=clamp(params.masterPresence,0.f,1.f);
 const float db=presence<center?-12.f*(center-presence)/center:12.f*(presence-center)/(1.f-center);
 const float highGain=std::pow(10.f,db/20.f);
 if(presence!=center){
  mix.l=presenceLP.l+(mix.l-presenceLP.l)*highGain;
  mix.r=presenceLP.r+(mix.r-presenceLP.r)*highGain;
 }
 mix.l*=params.masterLevel;mix.r*=params.masterLevel;out[i]=mix;
 }
}
Engine::MemoryBlackbox Engine::memoryBlackbox() const {
 MemoryBlackbox b;
 b.write=memory.write;b.available=memory.available;b.capturedWindow=memory.capturedWindow;
 b.audibleFrames=memory.audibleFrames;b.phaseQ16=memory.phaseQ16;b.direction=memory.direction;
 b.captured=memory.captured;b.freeze=params.memoryFreeze;b.reverse=params.memoryReverse;b.tide=params.memoryTide;
 b.mix=params.memoryMix;b.speed=params.memorySpeed;b.position=params.memoryPosition;b.shape=params.memoryShape;
 b.dry=debugLastMono;b.wet=debugLastWet;b.window=params.memoryWindow;b.voices=activeVoices();
 return b;
}
int Engine::activeVoices() const{int n=0;for(int i=0;i<limit;i++)n+=voices[i].active;return n;}
}

namespace rem {
namespace {
constexpr ParameterSpec specs[] = {
 {ParameterId::AcousticAOn,"acoustic_a_on","bool",0,1,1,true},
 {ParameterId::AcousticBOn,"acoustic_b_on","bool",0,1,1,true},
 {ParameterId::AcousticBlend,"acoustic_blend","percent",0,100,50,false},
 {ParameterId::OscOn,"osc_on","bool",0,1,1,true},
 {ParameterId::OscWave,"osc_wave","index_0_7",0,7,1,true},
 {ParameterId::OscLevel,"osc_level","percent",0,100,30,false},
 {ParameterId::OscOctave,"osc_octave","octaves",-3,3,0,true},
 {ParameterId::OscPulseWidth,"osc_pulse_width","percent",5,95,50,false},
 {ParameterId::MasterBlend,"master_blend","percent",0,100,30,false},
 {ParameterId::Attack,"amp_attack","seconds",0,3,.015f,false},
 {ParameterId::Decay,"amp_decay","seconds",0,3,.25f,false},
 {ParameterId::Sustain,"amp_sustain","percent",0,100,70,false},
 {ParameterId::Release,"amp_release","seconds",0,4.5f,.4f,false},
 {ParameterId::MemoryFreeze,"memory_freeze","bool",0,1,0,true},
 {ParameterId::MemoryReverse,"memory_reverse","bool",0,1,0,true},
 {ParameterId::MemoryTide,"memory_tide","bool",0,1,0,true},
 {ParameterId::MemoryMix,"memory_mix","percent",0,100,0,false},
 {ParameterId::MemoryWindow,"memory_window","samples",2205,192000,35000,true},
 {ParameterId::MemorySpeed,"memory_speed","percent",0,100,50,false},
 {ParameterId::MemoryPosition,"memory_position","percent",0,100,0,false},
 {ParameterId::MemoryShape,"memory_shape","percent",0,100,50,false},
 {ParameterId::LowPassOn,"lpf_on","bool",0,1,0,true},
 {ParameterId::LowPassCutoff,"lpf_cutoff","hz",20,20000,13000,false},
 {ParameterId::LowPassMix,"lpf_mix","percent",0,100,100,false},
 {ParameterId::OscC99Mode,"osc_c99_model","bool",0,1,0,true},
 {ParameterId::OscHarmonics,"osc_harmonics","percent",0,100,80.f*100/127,false},
 {ParameterId::OscNoiseType,"osc_noise_type","index_0_2",0,2,0,true},
 {ParameterId::OscNoiseLevel,"osc_noise_level","percent",0,100,0,false}
};
static_assert(sizeof(specs)/sizeof(specs[0])==static_cast<int>(ParameterId::COUNT),"parameter registry mismatch");
}
int parameterCount(){return static_cast<int>(ParameterId::COUNT);}
const ParameterSpec& parameterSpec(ParameterId id){int n=int(id);if(n<0||n>=parameterCount())n=0;return specs[n];}
void Engine::setParameter(ParameterId id,float normalized){
 if(!std::isfinite(normalized))return;
 float x=clamp(normalized,0.f,1.f);
 switch(id){
 case ParameterId::AcousticAOn:params.acousticA=x>=.5f;break;
 case ParameterId::AcousticBOn:params.acousticB=x>=.5f;break;
 case ParameterId::AcousticBlend:params.acousticBlend=x;break;
 case ParameterId::OscOn:params.oscOn=x>=.5f;break;
 case ParameterId::OscWave:params.waveform=Wave(std::min(7,int(std::round(x*7.f))));break;
 case ParameterId::OscLevel:params.oscLevel=x;break;
 case ParameterId::OscOctave:params.octave=std::max(-3,std::min(3,int(std::round(x*6.f))-3));break;
 case ParameterId::OscPulseWidth:params.pulseWidth=.05f+.9f*x;break;
 case ParameterId::MasterBlend:params.masterBlend=x;break;
 case ParameterId::Attack:params.attack=x*3.f;break;
 case ParameterId::Decay:params.decay=x*3.f;break;
 case ParameterId::Sustain:params.sustain=x;break;
 case ParameterId::Release:params.release=x*4.5f;break;
 case ParameterId::MemoryFreeze:params.memoryFreeze=x>=.5f;break;
 case ParameterId::MemoryReverse:params.memoryReverse=x>=.5f;break;
 case ParameterId::MemoryTide:params.memoryTide=x>=.5f;break;
 case ParameterId::MemoryMix:params.memoryMix=x;break;
 case ParameterId::MemoryWindow:params.memoryWindow=std::max(128,std::min(MemoryState::SIZE-1,int(std::lround(sr*(.05f+3.95f*x*x)))));break;
 case ParameterId::MemorySpeed:params.memorySpeed=x;break;
 case ParameterId::MemoryPosition:params.memoryPosition=x;break;
 case ParameterId::MemoryShape:params.memoryShape=x;break;
 case ParameterId::LowPassOn:params.lowPassOn=x>=.5f;break;
 case ParameterId::LowPassCutoff:params.lowPassCutoff=20.f*std::pow(1000.f,x);break;
 case ParameterId::LowPassMix:params.lowPassMix=x;break;
 case ParameterId::OscC99Mode:params.oscC99Mode=x>=.5f;break;
 case ParameterId::OscHarmonics:params.oscHarmonics=x;break;
 case ParameterId::OscNoiseType:params.oscNoiseType=std::min(2,int(std::lround(x*2)));break;
 case ParameterId::OscNoiseLevel:params.noiseLevel=x;break;
 default:break;
 }
}
float Engine::getParameter(ParameterId id) const{
 switch(id){
 case ParameterId::AcousticAOn:return params.acousticA?1.f:0.f;
 case ParameterId::AcousticBOn:return params.acousticB?1.f:0.f;
 case ParameterId::AcousticBlend:return params.acousticBlend;
 case ParameterId::OscOn:return params.oscOn?1.f:0.f;
 case ParameterId::OscWave:return int(params.waveform)/7.f;
 case ParameterId::OscLevel:return params.oscLevel;
 case ParameterId::OscOctave:return (params.octave+3)/6.f;
 case ParameterId::OscPulseWidth:return (params.pulseWidth-.05f)/.9f;
 case ParameterId::MasterBlend:return params.masterBlend;
 case ParameterId::Attack:return params.attack/3.f;
 case ParameterId::Decay:return params.decay/3.f;
 case ParameterId::Sustain:return params.sustain;
 case ParameterId::Release:return params.release/4.5f;
 case ParameterId::MemoryFreeze:return params.memoryFreeze?1.f:0.f;
 case ParameterId::MemoryReverse:return params.memoryReverse?1.f:0.f;
 case ParameterId::MemoryTide:return params.memoryTide?1.f:0.f;
 case ParameterId::MemoryMix:return params.memoryMix;
 case ParameterId::MemoryWindow:return std::sqrt(clamp((float(params.memoryWindow)/sr-.05f)/3.95f,0.f,1.f));
 case ParameterId::MemorySpeed:return params.memorySpeed;
 case ParameterId::MemoryPosition:return params.memoryPosition;
 case ParameterId::MemoryShape:return params.memoryShape;
 case ParameterId::LowPassOn:return params.lowPassOn?1.f:0.f;
 case ParameterId::LowPassCutoff:return std::log(clamp(params.lowPassCutoff,20.f,20000.f)/20.f)/std::log(1000.f);
 case ParameterId::LowPassMix:return params.lowPassMix;
 case ParameterId::OscC99Mode:return params.oscC99Mode?1.f:0.f;
 case ParameterId::OscHarmonics:return params.oscHarmonics;
 case ParameterId::OscNoiseType:return params.oscNoiseType/2.f;
 case ParameterId::OscNoiseLevel:return params.noiseLevel;
 default:return 0;
 }
}
void Engine::MemoryState::clear(){
 ring.fill(0);write=available=0;phaseQ16=0;direction=1;captured=priorFreeze=false;priorWindow=2048;
 activityEnvelope=0.f;captureSoundFrames=audibleFrames=capturedWindow=0;
}
float Engine::MemoryState::process(float mono,const Params& p,int sr){
 // Direct C++ adaptation of author's original rn_memory.c v1.5 Q23/Q16 algorithm.
 // The fixed-point core below keeps the same integer operations as C99.
 const bool freeze=p.memoryFreeze,reverse=p.memoryReverse,tide=p.memoryTide;
 const uint8_t mix=uint8_t(std::lround(clamp(p.memoryMix,0.f,1.f)*127));
 const uint32_t window=uint32_t(std::max(128,std::min(SIZE-1,p.memoryWindow)));
 const uint8_t speed=uint8_t(std::lround(clamp(p.memorySpeed,0.f,1.f)*127));
 const uint8_t position=uint8_t(std::lround(clamp(p.memoryPosition,0.f,1.f)*127));
 const uint8_t shape=uint8_t(std::lround(clamp(p.memoryShape,0.f,1.f)*127));
 if((freeze!=priorFreeze)||(int(window)!=priorWindow)){
  phaseQ16=0;direction=1;captured=false;
  if(!freeze)captureSoundFrames=0;
 }
 priorFreeze=freeze;priorWindow=window;
 // Hold an armed FREEZE until a complete audible window has been recorded.
 // This is a host-laboratory safety extension, not a claim of C99 parity.
 activityEnvelope=std::max(std::fabs(mono),activityEnvelope*.9995f);
 if(activityEnvelope>=.0010f)audibleFrames=std::min(uint32_t(SIZE),audibleFrames+1u);
 else audibleFrames=0;
 // Native C99 represents sample audio as signed 24-bit in an int32 word.
 const int32_t input=int32_t(std::fmax(-8388608.f,std::fmin(8388607.f,mono*8388608.f)));
 auto record=[&](){ring[write]=int16_t(input>>8);write=(write+1)&(SIZE-1);if(available<SIZE)available++;};
 if(!mix||(!freeze&&!reverse&&!tide)){record();return mono;}
 if(!freeze||!captured)record();
 
 if(freeze&&!captured){
  // Freeze an existing audible history instantly. If armed before a note,
  // collect at least 250ms of actual audio instead of latching silence.
  if(activityEnvelope<.0010f)return mono;
  const uint32_t minimum=std::min(window,uint32_t(sr/4));
  if(audibleFrames<minimum)return mono;
  capturedWindow=std::min(window,std::min(available,audibleFrames));
  if(capturedWindow<128)return mono;
  captured=true;phaseQ16=0;direction=1;
 }
 const uint32_t playbackWindow=freeze?capturedWindow:std::min(window,available);
 if(playbackWindow<128)return mono;
 uint32_t idx=uint32_t(phaseQ16>>16);
 if(idx>=playbackWindow)idx=playbackWindow-1;
 const uint32_t history=available-playbackWindow;
 const uint32_t shift=history*uint32_t(position)/127u;
 const uint32_t base=(write-playbackWindow-shift)&(SIZE-1);
 const uint32_t offset=reverse?(playbackWindow-1-idx):idx;
 const uint32_t a=(base+offset)&(SIZE-1);
 const uint32_t b=(a+(reverse?-1:1))&(SIZE-1);
 const uint32_t frac=uint32_t(phaseQ16)&65535u;
 int32_t sample=int32_t(((int64_t)ring[a]*(65536-frac)+(int64_t)ring[b]*frac)>>16);
 if(shape){
   const uint32_t edge=uint32_t(shape)*playbackWindow/(127u*4u);
   if(edge){
     uint32_t gain=65536u;
     if(idx<edge)gain=idx*65536u/edge;
     else if(idx>=playbackWindow-edge)gain=(playbackWindow-1u-idx)*65536u/edge;
     sample=int32_t((int64_t(sample)*gain)>>16);
   }
 }
 const int32_t wet=sample*256;
 const int32_t result=int32_t(((int64_t)input*(127-mix)+(int64_t)wet*mix)/127);
 const int64_t delta=int64_t((uint32_t(speed)+1)*65536u/65u);
 if(tide){
  phaseQ16+=delta*direction;
  if(phaseQ16>=((int64_t(playbackWindow)-1)<<16)){phaseQ16=(int64_t(playbackWindow)-1)<<16;direction=-1;}
  if(phaseQ16<0){phaseQ16=0;direction=1;}
 }else{
  phaseQ16+=delta;
  if(phaseQ16>=(int64_t(playbackWindow)<<16))phaseQ16%=(int64_t(playbackWindow)<<16);
 }
 // Decode fixed-point delta; dry stereo remains untouched.
 return float(result)/8388608.f;
}
}

namespace rem {
void Engine::GranularState::clear(){
 history.fill({});grains.fill({});write=filled=spawnCount=0;random=0x83a7b54du;
}
Stereo Engine::GranularState::process(Stereo x,const Params& p,int sr){
 // Record continuously so engaging GRANULAR does not start from an empty buffer.
 history[write]=x;write=(write+1u)&(SIZE-1);if(filled<SIZE)++filled;
 const float wetAmount=std::max(0.f,std::min(1.f,p.grainMix));
 if(wetAmount<=0.00001f){grains.fill({});spawnCount=0;return x;}
 const float size=std::max(0.f,std::min(1.f,p.grainSize));
 const float density=std::max(0.f,std::min(1.f,p.grainDensity));
 const float position=std::max(0.f,std::min(1.f,p.grainPos));
 const int length=std::max(128,int(float(sr)*(.027f+.135f*size)));
 // An audible, overlapped 4-grain treatment. Density controls spawn frequency.
 const int interval=std::max(64,int(float(length)/(1.2f+2.6f*density)));
 if(++spawnCount>=unsigned(interval)&&filled>unsigned(std::min(128,sr/120))){
  spawnCount=0;
  for(auto& g:grains)if(!g.active){
   random^=random<<13;random^=random>>17;random^=random<<5;
   const float jitter=float(int(random%1025)-512)/512.f;
   int delay=int(float(sr)*(.012f+.30f*position)+jitter*float(sr)*(.008f+.023f*density));
   delay=std::max(2,std::min(delay,int(filled)-2));
   // Rates deliberately vary slightly to yield real texture, not simply a static delay.
   g.rate=std::max(.45f,std::min(1.6f,1.f+.26f*jitter));
   g.pos=float((int(write)+SIZE-delay)&(SIZE-1));
   g.age=0;g.length=length;g.active=true;break;
  }
 }
 Stereo wet{};float sum=0.f;
 for(auto& g:grains){
  if(!g.active)continue;
  float phase=float(g.age)/float(g.length);
  float env=phase<.5f?(2.f*phase):(2.f*(1.f-phase)); // triangle Hann-like window
  env=std::max(0.f,env);
  const int i0=int(g.pos)&(SIZE-1),i1=(i0+1)&(SIZE-1);
  const float frac=g.pos-float(int(g.pos));
  Stereo a=history[i0],b=history[i1];
  wet.l+=(a.l+(b.l-a.l)*frac)*env;wet.r+=(a.r+(b.r-a.r)*frac)*env;sum+=env;
  g.pos+=g.rate;if(g.pos>=SIZE)g.pos-=SIZE;
  if(++g.age>=g.length)g.active=false;
 }
 if(sum<=.0001f)return x; // no dropouts in gaps between grains
 wet.l/=sum;wet.r/=sum;
 return {x.l*(1.f-wetAmount)+wet.l*wetAmount,x.r*(1.f-wetAmount)+wet.r*wetAmount};
}
}

namespace rem {
#include "ui07_effects04.inc"
}

namespace rem {
#include "ui07_send05.inc"
}

// LAB09: two conservative free-running low-frequency oscillators, no host tempo yet.
namespace rem {
void Engine::ModulationState::clear(){
 cycle.fill(0.f);held={{-.22f,.35f}};random={{0x315634b1u,0x9b8ae21fu}};
}
std::array<float,2> Engine::ModulationState::tick(const Params& p,int sr){
 std::array<float,2> result{{0.f,0.f}};
 for(int i=0;i<2;i++){
  if(!p.modOn[i]||p.mod[i][1]<=.00001f)continue;
  // FREE preserves the original oscillator rate exactly; SYNC uses musical beat divisions.
  static constexpr float beats[9]={4.f,2.f,1.f,.5f,.25f,1.5f,.75f,2.f/3.f,1.f/3.f};
  const int div=std::max(0,std::min(8,p.lfoDivision[i]));
  const float freeRate=.05f*std::pow(240.f,clamp(p.mod[i][0],0.f,1.f)); // 0.05-12 Hz
  const float rate=p.lfoSync[i] ? clamp(p.lfoTempoBpm,40.f,240.f)/(60.f*beats[div]) : freeRate;
  cycle[i]+=rate/std::max(1,sr);
  if(cycle[i]>=1.f){cycle[i]-=std::floor(cycle[i]);
    uint32_t z=random[i];z^=z<<13;z^=z>>17;z^=z<<5;random[i]=z;
    held[i]=2.f*(float(z&65535u)/65535.f)-1.f;
  }
  const float t=cycle[i]+clamp(p.mod[i][3],0.f,1.f);
  const float phase=t-std::floor(t);
  const int shape=std::min(4,int(std::lround(clamp(p.mod[i][2],0.f,1.f)*4.f)));
  switch(shape){
   case 0:result[i]=std::sin(2.f*float(PI)*phase);break;
   case 1:result[i]=1.f-4.f*std::abs(phase-.5f);break;
   case 2:result[i]=2.f*phase-1.f;break;
   case 3:result[i]=phase<.5f?1.f:-1.f;break;
   case 4:result[i]=held[i];break;
  }
 }
 return result;
}
}