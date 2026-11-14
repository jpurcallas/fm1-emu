// REminiSCENT Bridge05: experimental parallel SEND FX DSP.
// Existing UI LAB07 ids only; mode mapping is deliberate and explicit:
// DELAY = stereo feedback delay; REVERB = four damped stereo combs.
// MOD1/MOD2 unspecified in the UI contract, so NOT assigned arbitrary effects.
// This file is included inside namespace rem in engine.cpp.
void Engine::SendFxState::clear(){
 delay.fill({});for(auto& c:comb)c.fill({});damp.fill({});
 for(auto& a:diffusion)a.fill({});predelay.fill({});
 delayPos=combPos=0;delayLP={};reverbCachedSize=reverbCachedDecay=-1.f;
 reverbCachedRate=0;for(auto &m:mod)m=ModSlot{};
}
Stereo Engine::SendFxState::process(Stereo x,const Params& p,int sr){
 Stereo result=x;
 // Parallel send 1 — stereo feedback delay with an adjustable low-pass tone.
 if(p.sendOn[0]){
  const auto& c=p.send[0];
  const float time=clamp(c[0],0.f,1.f),feedback=clamp(c[1],0.f,1.f);
  const float tone=clamp(c[2],0.f,1.f),mix=clamp(c[3],0.f,1.f);
  const unsigned samples=unsigned(clamp((.075f+1.75f*time*time)*sr,1.f,float(DELAY_SIZE-2)));
  const unsigned read=(delayPos+DELAY_SIZE-samples)&(DELAY_SIZE-1);
  Stereo wet=delay[read];
  const float alpha=.018f+.68f*tone;
  delayLP.l+=alpha*(wet.l-delayLP.l);delayLP.r+=alpha*(wet.r-delayLP.r);
  const float fb=.03f+.87f*feedback;
  delay[delayPos]={clamp(x.l+delayLP.l*fb,-2.f,2.f),clamp(x.r+delayLP.r*fb,-2.f,2.f)};
  if(mix>0.f){result.l+=wet.l*.65f*mix;result.r+=wet.r*.65f*mix;}
  delayPos=(delayPos+1u)&(DELAY_SIZE-1);
 }
 // Parallel SEND 2 — spatial HALL, not a short comb coloration.
 // Predelay -> 8 decorrelated/damped combs -> 4 stereo allpass diffusers.
 // SIZE governs the room/delay spacing; DECAY defines RT60 (approximately
 // 0.7..13 seconds); DAMPING absorbs top end; MIX is the send-return level.
 // Reverb can outlive Note Off but must decay; it never retriggers a note.
 if(p.sendOn[1]){
  const auto& c=p.send[1];
  const float size=clamp(c[0],0.f,1.f),damping=clamp(c[1],0.f,1.f);
  const float decay=clamp(c[2],0.f,1.f),mix=clamp(c[3],0.f,1.f);
  if(size!=reverbCachedSize||decay!=reverbCachedDecay||sr!=reverbCachedRate){
    constexpr float lengths[REVERB_COMBS]={.0307f,.0353f,.0411f,.0467f,.0521f,.0577f,.0637f,.0701f};
    constexpr unsigned diffLengths[4]={149,271,419,733};
    const float scale=.81f+1.35f*size;
    const float rt60=.70f+12.5f*decay*decay;
    preN=unsigned(clamp((.012f+.058f*size)*sr,1.f,float(PRE_SIZE-2)));
    for(int j=0;j<REVERB_COMBS;j++){
      combNL[j]=unsigned(clamp(lengths[j]*scale*sr,4.f,float(COMB_SIZE-30)));
      combNR[j]=std::min(unsigned(COMB_SIZE-3),combNL[j]+unsigned((.0009f+.00039f*j)*sr));
      combFBL[j]=std::exp(-6.90775528f*float(combNL[j])/(rt60*sr));
      combFBR[j]=std::exp(-6.90775528f*float(combNR[j])/(rt60*sr));
    }
    for(int k=0;k<4;k++){
      diffNL[k]=unsigned(clamp(float(diffLengths[k])*(.80f+.50f*size),2.f,float(DIFF_SIZE-15)));
      diffNR[k]=diffNL[k]+unsigned(7+13*k);
    }
    reverbCachedSize=size;reverbCachedDecay=decay;reverbCachedRate=sr;
  }
  // A 12..70ms pre-delay defines a perceptible separation from the source.
  const unsigned preRead=(combPos+PRE_SIZE-preN)&(PRE_SIZE-1);
  const Stereo early=predelay[preRead];
  predelay[combPos&(PRE_SIZE-1)]=x;
  const float alpha=.87f-.74f*damping;
  Stereo wet{};
  for(int j=0;j<REVERB_COMBS;j++){
    // Different L/R lengths, with incommensurate tap spacings for wide stereo.
    const unsigned readL=(combPos+COMB_SIZE-combNL[j])&(COMB_SIZE-1);
    const unsigned readR=(combPos+COMB_SIZE-combNR[j])&(COMB_SIZE-1);
    const Stereo delayed={comb[j][readL].l,comb[j][readR].r};
    damp[j].l+=alpha*(delayed.l-damp[j].l);
    damp[j].r+=alpha*(delayed.r-damp[j].r);
    // Per-line feedback is RT60-calibrated, not a fixed short echo.
    comb[j][combPos]={clamp(early.l*.26f+combFBL[j]*damp[j].l,-2.5f,2.5f),
                      clamp(early.r*.26f+combFBR[j]*damp[j].r,-2.5f,2.5f)};
    wet.l+=delayed.l;wet.r+=delayed.r;
  }
  wet.l*=.31f;wet.r*=.31f;
  // Four serial Schroeder allpasses smear the early echoes into a dense tail.
  for(int k=0;k<4;k++){
    const unsigned w=combPos&(DIFF_SIZE-1);
    const unsigned rL=(w+DIFF_SIZE-diffNL[k])&(DIFF_SIZE-1);
    const unsigned rR=(w+DIFF_SIZE-diffNR[k])&(DIFF_SIZE-1);
    const Stereo prev={diffusion[k][rL].l,diffusion[k][rR].r};
    constexpr float g=.61f;
    diffusion[k][w]={wet.l+g*prev.l,wet.r+g*prev.r};
    wet={prev.l-g*wet.l,prev.r-g*wet.r};
  }
  // Parallel sends ADD a wholly wet tail to the dry instrument. MIX=100%
  // gives full wet send level, not an insert-style replacement of dry input.
  if(mix>0.f){result.l+=1.04f*wet.l*mix;result.r+=1.04f*wet.r*mix;}
  combPos=(combPos+1u)&(COMB_SIZE-1);
 }
 // Both selectable MOD slots process the same dry input in parallel.
 // All algorithms respect the MIX parameter. Rate, Depth, Character, Mix are 4 Q-Links.
 // For amplitude/pan modulation, subtract the dry signal to avoid doubling it on the send bus.
 constexpr float TAU=2.f*float(PI);
 auto readDelay=[](const std::array<Stereo,MOD_SIZE>& buffer,uint32_t head,float frames)->Stereo{
  float pos=float(head)-frames;
  while(pos<0.f)pos+=float(MOD_SIZE);
  const int a=int(std::floor(pos))&(MOD_SIZE-1),b=(a+1)&(MOD_SIZE-1);
  const float frac=pos-std::floor(pos);
  return {buffer[a].l+(buffer[b].l-buffer[a].l)*frac,
          buffer[a].r+(buffer[b].r-buffer[a].r)*frac};
 };
 for(int slot=0;slot<2;slot++){
  if(!p.sendOn[slot+2])continue;
  ModSlot& st=mod[slot];
  const auto& c=p.send[slot+2];
  const float rate=.07f+4.93f*c[0]*c[0];
  const float depth=clamp(c[1],0.f,1.f),character=clamp(c[2],0.f,1.f);
  const float mix=clamp(c[3],0.f,1.f);
  if(mix<=0.f)continue;
  st.phase+=rate/float(sr);
  if(st.phase>=1.f)st.phase-=1.f;
  const float s=std::sin(TAU*st.phase);
  Stereo wet=x;
  switch(p.sendAlgorithm[slot]){
   case 0:{ // CHORUS: 2 modulated tape heads with stereo width.
    const float leftMs=18.f+7.f*depth*s;
    const float rightMs=18.f+7.f*depth*std::sin(TAU*(st.phase+.12f+.38f*character));
    wet={readDelay(st.history,st.write,clamp(leftMs*sr*.001f,2.f,float(MOD_SIZE-2))).l,
         readDelay(st.history,st.write,clamp(rightMs*sr*.001f,2.f,float(MOD_SIZE-2))).r};
    st.history[st.write]=x;
    break;
   }
   case 1:{ // FLANGER: short modulated comb, bounded feedback.
    const float delayMs=5.f+4.3f*depth*s;
    wet=readDelay(st.history,st.write,clamp(delayMs*sr*.001f,2.f,float(MOD_SIZE-2)));
    st.history[st.write]={clamp(x.l+wet.l*.78f*character,-2.f,2.f),
                          clamp(x.r+wet.r*.78f*character,-2.f,2.f)};
    break;
   }
   case 2:{ // PHASER: four cascaded time-varying first-order all-pass stages.
    const float hz=330.f*std::pow(9.f,.5f+.5f*depth*s);
    const float t=std::tan(float(PI)*clamp(hz,50.f,.42f*sr)/float(sr));
    const float coefficient=(1.f-t)/(1.f+t);
    wet={clamp(x.l+character*.65f*st.phaserFeedback.l,-2.f,2.f),
         clamp(x.r+character*.65f*st.phaserFeedback.r,-2.f,2.f)};
    for(auto& ap:st.allpass){
     const Stereo y={-coefficient*wet.l+ap.l,-coefficient*wet.r+ap.r};
     ap={wet.l+coefficient*y.l,wet.r+coefficient*y.r};
     wet=y;
    }
    st.phaserFeedback=wet;
    break;
   }
   case 3:{ // TREMOLO: bipolar triangle/sine shape crossfade.
    const float triangle=std::asin(s)/std::asin(1.f);
    const float lfo=s*(1.f-character)+triangle*character;
    const float gain=1.f-.5f*depth*(1.f+lfo);
    wet={x.l*gain,x.r*gain};
    break;
   }
   case 4:{ // AUTO-PAN: complementary stereo gains, width = Character.
    const float pan=clamp(depth*s,-1.f,1.f);
    const float left=std::sqrt(clamp(1.f-pan,0.f,2.f));
    const float right=std::sqrt(clamp(1.f+pan,0.f,2.f));
    const float width=.35f+.65f*character;
    wet={x.l*(1.f-width+width*left),x.r*(1.f-width+width*right)};
    break;
   }
   default:break;
  }
  if(p.sendAlgorithm[slot]==0||p.sendAlgorithm[slot]==1)
   st.write=(st.write+1u)&(MOD_SIZE-1);
  // Wet return as delta: mix=0 is mathematically dry, mix=1 fully effected.
  result.l+=mix*(wet.l-x.l);result.r+=mix*(wet.r-x.r);
 }
 return result;
}