// REminiSCENT Bridge04 - experimental physical resonance and character algorithms.
// All control ranges 0..1 from UI LAB07 (no UI edits, host ID additions or allocation).
void Engine::ResonanceState::clear(){ mode.fill({}); }
void Engine::ResonanceState::configure(const Params& p,int sr){
 const float body=clamp(p.resoBody,0.f,1.f);
 const float decay=clamp(p.resoDecay,0.f,1.f);
 const float excite=clamp(p.resoExcite,0.f,1.f);
 const float f0=85.f+260.f*body*body;
 const float frequencies[3]={f0,f0*(3.9f+body),f0*(9.4f+2.f*body)};
 const float gains[3]={.90f,.56f,.34f};
 for(int i=0;i<3;i++){
  const float t=.042f+(0.12f+1.35f*decay*decay)/(1.f+i*.32f);
  const float r=std::exp(-1.f/(float(sr)*t));
  auto& m=mode[i];
  m.coef=2.f*r*std::cos(2.f*float(PI)*std::min(frequencies[i],float(sr)*.43f)/sr);
  m.decay2=r*r;
  // Small injection, normalized against decay time. Distinct 3 frequency bands.
  // Bridge06: calibrate modal injection; Bridge05's effect was below audibility.
  // Retain all modal frequencies and decay laws. No output boost on bypass.
  m.inject=(1.f-r)*7.5f*(.6f+1.8f*excite)*gains[i];
 }
}
Stereo Engine::ResonanceState::process(Stereo x,const Params& p){
 Stereo wet{};
 for(auto& m:mode){
  float l=m.coef*m.l1-m.decay2*m.l2+m.inject*x.l;
  float r=m.coef*m.r1-m.decay2*m.r2+m.inject*x.r;
  m.l2=m.l1;m.l1=l;m.r2=m.r1;m.r1=r;
  wet.l+=l;wet.r+=r;
 }
 const float mix=clamp(p.resoMix,0.f,1.f);
 // MIX must reach an unmistakably wet resonant timbre at 100%.
 // Earlier Bridges mixed only a small additive signal into the full dry source,
 // and multiplied MIX by EXCITE, preventing independent control.
 const float wetL=std::tanh(wet.l*1.35f)*.88f;
 const float wetR=std::tanh(wet.r*1.35f)*.88f;
 return {x.l*(1.f-mix)+wetL*mix,x.r*(1.f-mix)+wetR*mix};
}
void Engine::CharacterState::clear(){
 tape.fill({});vinyl.fill({});tapeWrite=vinylWrite=0;
 random=0x9e3779b9u;tapePhase=flutterPhase=warpPhase=0.f;
 vinylLP={};tapeLP={};crushHold={};crushCount=0;noiseGate=dustEnvelope=0.f;
}
Stereo Engine::CharacterState::process(Stereo x,const Params& p,int sr){
 auto rnd=[&](){random^=random<<13;random^=random>>17;random^=random<<5;
  return (float(random&65535u)/32767.5f)-1.f;};
 auto mix=[&](Stereo dry,Stereo wet,float amt)->Stereo{
  amt=clamp(amt,0.f,1.f);return {dry.l+(wet.l-dry.l)*amt,dry.r+(wet.r-dry.r)*amt};};
 auto n=[&](int id,int slot){return clamp(p.character[id][slot],0.f,1.f);};
 // Audio-dependent gate prevents constant hiss or crackle in complete silence.
 noiseGate=std::max(noiseGate*.99975f,std::min(1.f,2.2f*(std::abs(x.l)+std::abs(x.r))));
 if(p.characterOn[0]){
  const float drive=1.f+20.f*n(0,0)*n(0,0),bias=(n(0,2)-.5f)*.42f;
  const float tone=.008f+.3f*n(0,1);
  auto distort=[&](float a,float &lp){
   const float wet=(std::tanh(drive*(a+bias))-std::tanh(drive*bias))/(1.f+0.10f*drive);
   lp+=tone*(wet-lp);
   return .32f*lp+.68f*wet;
  };
  x=mix(x,{distort(x.l,tapeLP.l),distort(x.r,tapeLP.r)},n(0,3));
 }
 // Saturated tape: wow/flutter delay wobble plus restrained tape noise.
 if(p.characterOn[1]){
  const float wow=n(1,0),flutter=n(1,1),hiss=n(1,2);
  tape[tapeWrite]=x;
  tapePhase+=2.f*float(PI)*(.17f+wow*.78f)/sr;
  flutterPhase+=2.f*float(PI)*(4.f+flutter*7.f)/sr;
  if(tapePhase>2.f*float(PI))tapePhase-=2.f*float(PI);
  if(flutterPhase>2.f*float(PI))flutterPhase-=2.f*float(PI);
  const float delay=220.f+85.f*wow*std::sin(tapePhase)+33.f*flutter*std::sin(flutterPhase);
  float where=float(tapeWrite)-delay;
  while(where<0.f)where+=SIZE;
  const unsigned j=unsigned(where)&(SIZE-1),k=(j+1)&(SIZE-1);
  const float frac=where-std::floor(where);
  Stereo wet{tape[j].l+(tape[k].l-tape[j].l)*frac,
             tape[j].r+(tape[k].r-tape[j].r)*frac};
  wet.l=std::tanh(wet.l*1.38f)/1.15f+noiseGate*.009f*hiss*rnd();
  wet.r=std::tanh(wet.r*1.38f)/1.15f+noiseGate*.009f*hiss*rnd();
  x=mix(x,wet,n(1,3));tapeWrite=(tapeWrite+1)&(SIZE-1);
 }
 // Vinyl: wear = high-frequency rolloff; dust = sparse short surface impulses;
 // warp = low-rate speed drift of a dedicated delay, not a fake UI animation.
 if(p.characterOn[2]){
  const float wear=n(2,0),dust=n(2,1),warp=n(2,2);
  vinyl[vinylWrite]=x;
  warpPhase+=2.f*float(PI)*(.32f+.55f*warp)/sr;
  if(warpPhase>2.f*float(PI))warpPhase-=2.f*float(PI);
  const float delay=180.f+90.f*warp*std::sin(warpPhase);
  float where=float(vinylWrite)-delay;
  while(where<0.f)where+=SIZE;
  const unsigned j=unsigned(where)&(SIZE-1),k=(j+1)&(SIZE-1);
  const float frac=where-std::floor(where);
  Stereo wet{vinyl[j].l+(vinyl[k].l-vinyl[j].l)*frac,
             vinyl[j].r+(vinyl[k].r-vinyl[j].r)*frac};
  const float alpha=.75f*(1.f-wear)+.018f*wear;
  vinylLP.l+=alpha*(wet.l-vinylLP.l);
  vinylLP.r+=alpha*(wet.r-vinylLP.r);
  // Dust uses a short decaying impulse (not an inaudible single-sample click).
  if(rnd()>(1.f-.0012f*dust)) dustEnvelope=.13f*dust*noiseGate*rnd();
  else dustEnvelope*=.96f;
  const float crackle=dustEnvelope;
  wet={vinylLP.l+crackle,vinylLP.r+crackle};
  x=mix(x,wet,n(2,3));vinylWrite=(vinylWrite+1)&(SIZE-1);
 }
 // Bit-crush: independent sample hold + quantization + dither.
 if(p.characterOn[3]){
  const int bits=std::max(3,std::min(16,int(std::lround(16.f-13.f*n(3,0)))));
  const uint32_t hold=1u+uint32_t(std::lround(n(3,1)*31.f));
  if(crushCount++>=hold){
   crushCount=0;
   const float steps=std::ldexp(1.f,bits-1);
   const float dither=n(3,2)/steps*.5f;
   crushHold.l=std::round((x.l+dither*rnd())*steps)/steps;
   crushHold.r=std::round((x.r+dither*rnd())*steps)/steps;
  }
  x=mix(x,crushHold,n(3,3));
 }
 return x;
}