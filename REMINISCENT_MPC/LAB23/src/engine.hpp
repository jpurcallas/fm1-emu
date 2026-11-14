#pragma once
#include <array>
#include <vector>
#include <string>
#include <cstdint>
#include <cstddef>
#include <memory>

namespace rem {
struct Stereo { float l=0, r=0; };
struct Sample {
 int root=60, rate=48000, channels=2, bits=16, wavFormat=1;
 float tuneCents=0.f;
 std::vector<uint8_t> pcm; // Portable fallback: original bytes, unchanged.
 std::shared_ptr<const uint8_t> mappedPcm; // Read-only file-backed lossless sample.
 size_t mappedOffset=0;
 const uint8_t* pcmData() const {return mappedPcm ? mappedPcm.get()+mappedOffset : pcm.data();}
 size_t frames=0;
};
struct Bank {
 std::vector<Sample> layers;
 const Sample* nearest(int note) const;
 bool loadWav(const std::string& path,int root,std::string& error);
};
enum class Wave : int { Sine=0, Triangle=1, Saw=2, Square=3, Pulse=4, Organ=5, Bright=6, Hollow=7 };

// Fixed IDs are a host-agnostic bridge, NOT screen layout. Add new IDs only at the end.
enum class ParameterId : int {
 AcousticAOn=0, AcousticBOn, AcousticBlend, OscOn, OscWave, OscLevel,
 OscOctave, OscPulseWidth, MasterBlend, Attack, Decay, Sustain, Release,
 MemoryFreeze, MemoryReverse, MemoryTide, MemoryMix, MemoryWindow,
 MemorySpeed, MemoryPosition, MemoryShape,
 LowPassOn, LowPassCutoff, LowPassMix,
 OscC99Mode, OscHarmonics, OscNoiseType, OscNoiseLevel,
 COUNT
};
struct ParameterSpec {
 ParameterId id;
 const char* key;
 const char* units;
 float minValue, maxValue, defaultValue;
 bool discrete;
};
const ParameterSpec& parameterSpec(ParameterId id);
int parameterCount();

struct Params {
 float acousticBlend=0.f, masterBlend=0.f, oscLevel=0.f;
 bool acousticA=true,acousticB=false,oscOn=false;
 int sourceA=0,sourceB=1; // indices 0..27 from LAB19 bank.tsv
 float levelA=1.f,levelB=1.f,masterLevel=1.f;
 float masterPresence=64.f/127.f; // LAB10 wide +/-12dB presence shelf, 64 neutral
 int masterOctave=0; // LAB10 MASTER PITCH: -2..+2 octaves for A+B+OSC
 Wave waveform=Wave::Triangle; float pulseWidth=.5f;
 float attack=.015f,decay=.25f,sustain=.7f,release=.4f;
 int octave=0; float noiseLevel=0;
 bool oscC99Mode=false;float oscHarmonics=80.f/127.f;int oscNoiseType=0;
 bool memoryFreeze=false,memoryReverse=false,memoryTide=false;
 float memoryMix=0.f; int memoryWindow=2048;
 float memorySpeed=.5f,memoryPosition=0.f,memoryShape=.5f;
 bool lowPassOn=false;float lowPassCutoff=20000.f,lowPassMix=1.f;
 // LAB24 acoustic noise and filter/OSC controls. Defaults preserve LAB23 audio.
 float oscSpread=64.f/127.f; // centered = original mono OSC
 float lowPassEnv=56.f/127.f; // neutral at former stored value
 float lowPassTrack=64.f/127.f; // neutral at former stored value
 float acousticNoiseLevel=0.f; // independently synthesized, OFF by default
 int acousticNoiseType=0; // 0=WHITE, 1=PINK Voss-McCartney
 float grainSize=.43f,grainDensity=.35f,grainPos=.54f,grainMix=0.f;
 // UI LAB07 legacy controls; same persistent 102 IDs.
 float resoBody=.57f,resoDecay=.39f,resoExcite=.38f,resoMix=0.f;
 // Order distortion, tape, vinyl, crush. Four normalized controls each.
 std::array<bool,4> characterOn{{false,false,false,false}};
 std::array<std::array<float,4>,4> character{{
  {{.31f,.63f,.50f,.24f}},{{.38f,.24f,.16f,.59f}},
  {{.35f,.12f,.24f,.51f}},{{.60f,.47f,.14f,.43f}}
 }};
 // Original LAB07 FX slots. LAB09 adds standard flanger (MOD1) and chorus (MOD2).
 std::array<bool,4> sendOn{{false,false,false,false}};
 // Per-slot selectable modulation algorithm: 0 chorus, 1 flanger, 2 phaser, 3 tremolo, 4 auto-pan.
 std::array<int,2> sendAlgorithm{{1,0}};
 std::array<std::array<float,4>,4> send{{
   {{45.f/127,52.f/127,60.f/127,1.f}},
   {{105.f/127,50.f/127,110.f/127,1.f}},
   {{47.f/127,60.f/127,22.f/127,1.f}},
   {{35.f/127,45.f/127,64.f/127,1.f}}
 }};
 // Fixed routes in laboratory: LFO1 -> pitch, LFO2 -> low-pass cutoff.
 // UI LAB10 has no destination selection or host-BPM mapping yet.
 std::array<bool,2> modOn{{false,false}};
 // rate / depth / shape / phase; normalized exactly as in LAB10.
 std::array<std::array<float,4>,2> mod{{
  {{45.f/127,60.f/127,25.f/127,0.f}},
  {{75.f/127,32.f/127,80.f/127,45.f/127}}
 }};
 // 0 PITCH 1 CUTOFF 2 AMP 3 PAN 4 MASTER BLEND 5 PULSE WIDTH
 std::array<int,3> modDestination{{0,1,1}};
 bool env2On=false;
 std::array<float,4> env2{{35.f/127,42.f/127,80.f/127,50.f/127}};
 float env2Amount=64.f/127;
 // Bridge11: global manual BPM in preview; MPC host transport not connected.
 float lfoTempoBpm=120.f;
 std::array<bool,2> lfoSync{{false,false}},lfoRetrigger{{false,false}};
 // 0=1/1, 1=1/2, 2=1/4, 3=1/8, 4=1/16, 5=1/4 dotted, 6=1/8 dotted, 7=1/4 triplet, 8=1/8 triplet.
 std::array<int,2> lfoDivision{{2,2}};

};
struct Voice {
 bool active=false, held=false, sustainHeld=false; int note=0; uint64_t born=0;
 const Sample *a=nullptr,*b=nullptr; double posA=0,posB=0,rateA=1,rateB=1,phase=0;
 uint32_t phaseQ32=0,noiseSeed=0x13579bdf;
 int32_t pinkSlow=0,pinkMid=0,pinkFast=0;
 // Independent of the OSC noise generator, so enabling acoustic noise
 // never perturbs oscillator noise or the approved PCM voices.
 uint32_t acousticNoiseSeed=0x91351f17u,acousticPinkCounter=0;
 std::array<float,16> acousticPinkRows{};float acousticPinkSum=0.f;
 float velocity=1.f,level=0,releaseDelta=0;
 float env2Level=0.f,env2ReleaseDelta=0.f;
 enum class Stage{Attack,Decay,Sustain,Release} stage=Stage::Attack,env2Stage=Stage::Attack;
};
class Engine {
public:
 // Read-only laboratory telemetry; no logging or disk IO in the DSP callback.
 struct MemoryBlackbox {
  uint32_t write=0, available=0, capturedWindow=0, audibleFrames=0;
  int64_t phaseQ16=0; int direction=1;
  bool captured=false, freeze=false, reverse=false, tide=false;
  float mix=0, speed=0, position=0, shape=0, dry=0, wet=0;
  int window=0, voices=0;
 };
 MemoryBlackbox memoryBlackbox() const;
 // Read-only actual modulation samples for SDK Plotter; never feeds DSP or MIDI.
 std::array<float,2> modulationBlackbox() const { return uiLastLfo_; }

 static constexpr int MAX_VOICES=16;
 explicit Engine(int rate=48000):sr(rate){}
 Bank bankA, bankB; std::array<Bank,28> sourceBanks; Bank didgeridooB; Params params; // Retained for compatibility with Engine 05.
 void setPolyphony(int count);
 void noteOn(int note,float velocity=1.f);
 void noteOff(int note);
 void allNotesOff();                  // MIDI CC123 / release (memory tail may continue)
 void allSoundOff();                  // MIDI CC120 / panic, clears memory
 void midiMessage(uint8_t status,uint8_t data1,uint8_t data2);
 void render(Stereo* out,int frames); // no allocation or disk IO in audio callback
 void setParameter(ParameterId id,float normalized);
 float getParameter(ParameterId id) const;
 int activeVoices() const;
 int polyphony() const {return limit;}
 int sampleRate() const {return sr;}
private:
 struct MemoryState {
  static constexpr int SIZE=262144; // 5.94 seconds at 44.1kHz
  std::array<int16_t,SIZE> ring{};
  uint32_t write=0,available=0;
  int64_t phaseQ16=0;
  int8_t direction=1;
  bool captured=false,priorFreeze=false;
  int priorWindow=2048;
  // Bridge06: don't latch silence when FREEZE is armed before a note.
  float activityEnvelope=0.f;
  uint32_t captureSoundFrames=0, audibleFrames=0, capturedWindow=0;
  void clear();
  float process(float mono,const Params& p,int sr);
 } memory;
 struct GranularState {
  static constexpr int SIZE=32768; // ~0.68 seconds at 48 kHz
  struct Grain {bool active=false;float pos=0,rate=1;int age=0,length=1;};
  std::array<Stereo,SIZE> history{};
  std::array<Grain,4> grains{};
  uint32_t write=0,filled=0,spawnCount=0,random=0x83a7b54du;
  void clear();
  Stereo process(Stereo x,const Params& p,int sr);
 } granular;
 struct ResonanceState {
  struct Mode {float l1=0,l2=0,r1=0,r2=0,coef=0,decay2=0,inject=0;};
  std::array<Mode,3> mode{};
  void clear();void configure(const Params&,int sr);
  Stereo process(Stereo x,const Params&);
 } resonance;
 struct CharacterState {
  static constexpr int SIZE=16384;
  std::array<Stereo,SIZE> tape{},vinyl{};
  uint32_t tapeWrite=0,vinylWrite=0,random=0x9e3779b9u;
  float tapePhase=0,flutterPhase=0,warpPhase=0;
  Stereo vinylLP{},tapeLP{},crushHold{};
  uint32_t crushCount=0;
  float noiseGate=0.f,dustEnvelope=0.f;
  void clear();Stereo process(Stereo x,const Params&,int sr);
 } character;
 struct SendFxState {
  // Fixed-size buffers; no dynamic memory allocation in the audio callback.
  static constexpr int DELAY_SIZE=131072; // >2 seconds even at 48kHz
  static constexpr int COMB_SIZE=8192;
  std::array<Stereo,DELAY_SIZE> delay{};
  // Bridge16: hall/space reverb. 8 independent damped combs with four diffusion
  // allpasses, decorrelated stereo delay lengths and pre-delay; fixed buffers.
  static constexpr int REVERB_COMBS=8;
  static constexpr int DIFF_SIZE=4096;
  static constexpr int PRE_SIZE=8192;
  std::array<std::array<Stereo,COMB_SIZE>,REVERB_COMBS> comb{};
  std::array<Stereo,REVERB_COMBS> damp{};
  std::array<std::array<Stereo,DIFF_SIZE>,4> diffusion{};
  std::array<Stereo,PRE_SIZE> predelay{};
  uint32_t delayPos=0,combPos=0;
  // No transcendental math in the audio-sample loop. Recompute tap gains
  // only when SIZE, DECAY, or host sample rate changes.
  float reverbCachedSize=-1.f,reverbCachedDecay=-1.f;
  int reverbCachedRate=0;
  unsigned preN=0;
  std::array<unsigned,REVERB_COMBS> combNL{},combNR{};
  std::array<float,REVERB_COMBS> combFBL{},combFBR{};
  std::array<unsigned,4> diffNL{},diffNR{};
  Stereo delayLP{};
  static constexpr int MOD_SIZE=4096;
  struct ModSlot {
   std::array<Stereo,MOD_SIZE> history{};
   uint32_t write=0;
   float phase=0.f;
   Stereo phaserFeedback{};
   std::array<Stereo,4> allpass{};
  };
  std::array<ModSlot,2> mod{};
  void clear();
  Stereo process(Stereo x,const Params&,int sr);
 } sendFx;
 struct ModulationState {
  std::array<float,2> cycle{{0.f,0.f}},held{{-.22f,.35f}};
  std::array<uint32_t,2> random{{0x315634b1u,0x9b8ae21fu}};
  void clear();std::array<float,2> tick(const Params& p,int sr);
 } modulation;
 Stereo presenceLP{};
 std::array<Voice,MAX_VOICES> voices{};
 int sr=48000,limit=8; uint64_t clock=0;
 float debugLastMono=0.f,debugLastWet=0.f;
 std::array<float,2> uiLastLfo_{{0.f,0.f}};
 bool pedalDown=false;
 float lpL=0.f,lpR=0.f;
 float envelope(Voice& v);
 Stereo sampleAt(const Sample* s,double pos) const;
 float oscillator(Voice& v,float pitchSemitone=0.f,float pulseWidth=-1.f);
 float env2Tick(Voice& v);
 void startRelease(Voice& v);
};
}