#include "ram_attr.h"
/* BIOMECH RHYTHM — by Yeti Fingers
   Portable C99 ENGINEERING PORT of the approved browser prototype 0.9.10.
   No allocation, OS calls, file I/O or blocking operations in br_render().
   Copyright (c) 2026 Yeti Fingers — original project attribution.
   IMPORTANT: native effects ≠ exact Web Audio impulse/CompressorNode, see docs/PARITY.md.
*/
#include "biomech.h"
#include <math.h>
#include <string.h>
#include <float.h>
#define BR_PI 3.14159265358979323846f
#define BR_SR 44100.0f
#define BR_MIN(a,b) ((a)<(b)?(a):(b))
#define BR_MAX(a,b) ((a)>(b)?(a):(b))
#define BR_CLAMP(x,a,b) BR_MAX((a),BR_MIN((x),(b)))
static const char br_project_new_label[] BR_RAMCONST = "NEW PROJECT";
static const char br_init_label[] BR_RAMCONST = "INIT SOUND";
/* Exact argument caching: repeated libm inputs return the identical float32
 * result. Unlike a LUT or recurrence, this never substitutes a math formula.
 * Each engine owns its state; live parameters are encoded in the arguments.
 * NaNs do not compare equal, so they always go through the original libm. */
static float BR_RAMCODE br_env_exp_cached(BREngine *e,float arg){
  if(e->exp_cached_valid && arg==e->exp_cached_arg)return e->exp_cached_result;
  float result=expf(arg);
  e->exp_cached_arg=arg;e->exp_cached_result=result;e->exp_cached_valid=1;
  return result;
}
static float BR_RAMCODE br_pitch_pow_cached(BREngine *e,float base,float power){
  if(e->pow_cached_valid && base==e->pow_cached_base && power==e->pow_cached_power)
    return e->pow_cached_result;
  float result=powf(base,power);
  e->pow_cached_base=base;e->pow_cached_power=power;
  e->pow_cached_result=result;e->pow_cached_valid=1;
  return result;
}
static float BR_RAMCODE br_rand(BREngine *e){uint32_t x=e->rng;x^=x<<13;x^=x>>17;x^=x<<5;e->rng=x?x:0x9e3779b9u;return (float)(e->rng>>8)*(1.0f/16777216.0f);}
float BR_RAMCODE br_midi_hz(float note){return 440.0f*powf(2.0f,(note-69.0f)/12.0f);}
static float BR_RAMCODE br_chgain(float x){x=BR_CLAMP(x,0,100);return x<=75?x/75:powf(10.0f,(x-75)/25*6/20.0f);}
static float BR_RAMCODE br_db(float db){return powf(10.0f,db/20.0f);}
static void BR_RAMCODE br_init_step(BRStep *st){memset(st,0,sizeof(*st));st->active=1;st->prob=100;st->cond_mode=BR_PROBABILITY;st->cond_every=4;st->cond_on=1;st->ratchet=1;st->velocity=100;st->midi_note=-1;}
void BR_RAMCODE br_init_sound(BRTrack *v){
  BRStep saved[BR_STEPS]; /* preserve sequence */
  memcpy(saved,v->steps,sizeof(saved));
  v->family=BR_RESONANCE;v->waveform=BR_SINE;v->lfo_target=0;
  v->body=45;v->attack=35;v->texture=0;v->decay=55;
  v->env_attack_ms=4;v->env_decay_ms=350;v->env_sustain=0;v->env_release_ms=200;
  v->lfo_rate_hz=4;v->lfo_depth=0;v->fine_cents=0;v->pitch_sweep=0;
  v->voice_octave=0;v->oct_low=-1;v->oct_high=1;
  v->bit_depth=16;v->reduction_rate=44100;v->bit_mix=0;
  memcpy(v->steps,saved,sizeof(saved));
}
void BR_RAMCODE br_set_seed(BREngine *e,uint32_t seed){e->project.random_seed=seed?seed:0x4d595446u;e->rng=e->project.random_seed;}
void BR_RAMCODE br_new_project(BREngine *e){
  BRProject *p=&e->project;memset(p,0,sizeof(*p));
  memcpy(p->name,br_project_new_label,12);p->bpm=120;p->master=.86f;
  p->axis[BR_TIME]=30;p->axis[BR_DENSITY]=0;p->axis[BR_DYNAMICS]=60;
  p->axis[BR_TIMBRE]=15;p->axis[BR_RELATIONS]=70;p->axis[BR_STRUCTURE]=0;p->axis[BR_OCTAVE]=0;
  p->density_direction=BR_BOTH;p->structure_direction=BR_STRUCT_BOTH;p->roll_division=2;
  p->fx.drive=0;p->fx.delay_division=4;p->fx.delay_feedback=28;p->fx.delay_wet=45;
  p->fx.reverb_size=36;p->fx.reverb_wet=36;p->fx.comp_threshold_db=-12;p->fx.comp_ratio=1;
  p->fx.resonator_model=BR_TUBE;p->fx.resonator_tune=45;p->fx.resonator_decay=55;
  for(int i=0;i<BR_TRACKS;i++){
    BRTrack *v=&p->track[i];
    for(int n=0;n<BR_STEPS;n++)br_init_step(&v->steps[n]);
    br_init_sound(v);v->level=75;v->freedom=100;v->length=16;
    v->send_delay=25;v->send_reverb=18;v->send_resonator=25;
    v->relationship=BR_NO_REL;v->relation_source=(i+5)%BR_TRACKS;
    strcpy(v->name,br_init_label);
  }
  e->playing=0;e->recording=0;e->events_used=0;e->sample_clock=0;e->next_step_sample=0;
  e->step_position=0;e->step_fraction=0;e->external_clock_pulses=0;
  e->roll_held=0;e->jump_enabled=0;e->last_clock_sample=0;e->clock_interval_avg=0;
  memset(e->visits,0,sizeof(e->visits));
  memset(e->active,0,sizeof(e->active));
  memset(e->env_log_valid,0,sizeof(e->env_log_valid));
  br_set_seed(e,0x59455449u);
}
#ifdef BR_FM1_COMPACT_FX
void BR_RAMCODE br_init_compact_with_fx(BREngine *e,BRCompactFXBuffers *workspace){
  if(!e)return;
  memset(e,0,sizeof(*e));
#ifdef BR_COMPACT_EXTERNAL_FX_STORAGE
  e->compact_fx=workspace;
#else
  e->compact_fx=workspace?workspace:&e->compact_fx_embedded;
#endif
  if(e->compact_fx)memset(e->compact_fx,0,sizeof(*e->compact_fx));
  /* Conservative two-stage anti-alias filter at the original 44.1 kHz. */
  const float df=BR_SR/(3.8f*(float)BR_COMPACT_DELAY_DIV);
  const float rf=BR_SR/(3.8f*(float)BR_COMPACT_REVERB_DIV);
  e->compact_delay_filter_alpha=1.0f-expf(-2.0f*BR_PI*df/BR_SR);
  e->compact_reverb_filter_alpha=1.0f-expf(-2.0f*BR_PI*rf/BR_SR);
  /* Feedback's 4200 Hz lowpass cannot exceed compact Nyquist. */
  float cutoff=BR_MIN(4200.0f,BR_SR/(float)BR_COMPACT_DELAY_DIV*.38f);
  e->compact_feedback_alpha=1.0f-expf(-2.0f*BR_PI*cutoff/
                                        (BR_SR/(float)BR_COMPACT_DELAY_DIV));
  e->sync_source=BR_INTERNAL;
  br_new_project(e);
}
void BR_RAMCODE br_init_with_fx(BREngine *e,BRFXBuffers *unused){(void)unused;br_init_compact_with_fx(e,NULL);}
void BR_RAMCODE br_init(BREngine *e){br_init_compact_with_fx(e,NULL);}
#else
void br_init_with_fx(BREngine *e,BRFXBuffers *fx_memory){
  if(!e)return;
  memset(e,0,sizeof(*e));
#ifdef BR_EXTERNAL_FX_STORAGE
  e->fx=fx_memory;
#else
  (void)fx_memory;
  e->fx=&e->fx_embedded;
#endif
  if(e->fx){
    memset(e->fx,0,sizeof(*e->fx));
    const int lengths[4]={11183,12773,13937,15787};
    for(int i=0;i<4;i++)e->fx->reverb[i].length=(uint32_t)lengths[i];
  }
  e->delay_lp_coeff=1-expf(-2*BR_PI*4200/BR_SR);
  e->sync_source=BR_INTERNAL;
  br_new_project(e);
}
void br_init(BREngine *e){
#ifdef BR_EXTERNAL_FX_STORAGE
  br_init_with_fx(e,NULL);
#else
  br_init_with_fx(e,NULL);
#endif
}
#endif
void BR_RAMCODE br_clear_track(BREngine *e,unsigned track){if(track>=BR_TRACKS)return;for(int i=0;i<BR_STEPS;i++){br_init_step(&e->project.track[track].steps[i]);e->visits[track][i]=0;}}
void BR_RAMCODE br_clear_all(BREngine *e){for(unsigned i=0;i<BR_TRACKS;i++)br_clear_track(e,i);}
void BR_RAMCODE br_start(BREngine *e){e->playing=1;e->step_position=0;e->next_step_sample=e->sample_clock;e->transport_start_sample=e->sample_clock;e->step_fraction=0;e->external_clock_pulses=0;memset(e->visits,0,sizeof(e->visits));}
void BR_RAMCODE br_stop(BREngine *e){e->playing=0;e->events_used=0;e->roll_held=0;}

void BR_RAMCODE br_roll_hold(BREngine *e,int pressed){e->roll_held=pressed?1:0;if(pressed)e->next_roll_sample=e->sample_clock;}
void BR_RAMCODE br_step_jump(BREngine *e,unsigned step,int pressed){
 if(!pressed){e->jump_enabled=0;return;}
 int t=BR_CLAMP(e->project.selected_track,0,5);const BRTrack *v=&e->project.track[t];
 int len=BR_CLAMP(v->length,1,64),ordinal=0,found=-1;
 for(int i=0;i<len;i++)if(v->steps[i].active){if((unsigned)i>=step){found=ordinal;break;}ordinal++;}
 e->jump_step=(uint8_t)(found>=0?found:0);e->jump_enabled=1;
}
void BR_RAMCODE br_record_note(BREngine *e,unsigned track,unsigned note,unsigned velocity,unsigned quantize_division,float strength){
 if(track>=BR_TRACKS||note>127||!e->playing||!e->recording)return;
 BRTrack *v=&e->project.track[track];
 float step_samples=BR_SR*60.0f/(BR_CLAMP(e->project.bpm,40,240)*4.0f);
 float raw=(float)(e->sample_clock-e->transport_start_sample)/step_samples;
 float grid=(quantize_division==32)?.5f:1.0f;
 float snapped=roundf(raw/grid)*grid;
 float target=quantize_division==0?raw:raw+(snapped-raw)*BR_CLAMP(strength,0,1);
 int chosen=(int)lroundf(target),len=BR_CLAMP(v->length,1,64);
 int step=((chosen%len)+len)%len;
 BRStep *s=&v->steps[step];s->on=1;s->midi_note=(int16_t)note;s->velocity=(uint8_t)BR_CLAMP(velocity,1,127);
 s->micro_ms=(int16_t)BR_CLAMP((int)lroundf((target-chosen)*step_samples*1000/BR_SR),-120,120);
}

static int BR_RAMCODE br_track_active(const BREngine *e,int i){
  if(e->project.track[i].muted)return 0;
  int anysolo=0;for(int j=0;j<BR_TRACKS;j++)anysolo|=e->project.track[j].solo;
  return !anysolo||e->project.track[i].solo;
}
float BR_RAMCODE br_effective_freedom(const BREngine *e,unsigned track,BRFreedomAxis axis){
  if(track>=BR_TRACKS||axis>=BR_DIMENSIONS||e->project.freeze||e->project.track[track].anchor)return 0;
  const BRTrack *v=&e->project.track[track];
  return BR_CLAMP(e->project.global_freedom,0,100)/100.0f * BR_CLAMP(v->freedom,0,100)/100.0f * BR_CLAMP(e->project.axis[axis],0,100)/100.0f;
}
static float BR_RAMCODE br_axis(BREngine *e,int t,const BRStep *s,BRFreedomAxis a){return (s->anchor||e->project.freeze)?0:br_effective_freedom(e,t,a);}
static int BR_RAMCODE br_index(const BRTrack *v,uint64_t pos){
  int length=BR_CLAMP(v->length,1,64),count=0;
  for(int j=0;j<length;j++)if(v->steps[j].active)count++;
  if(!count)return -1;
  int target=(int)(pos%(uint64_t)count);
  for(int j=0;j<length;j++)if(v->steps[j].active){if(target--==0)return j;}
  return -1;
}
BRLedState BR_RAMCODE br_step_led(const BREngine *e,unsigned track,unsigned page,unsigned key){
  if(track>=BR_TRACKS||page>=4||key>=16)return BR_LED_OFF;
  unsigned step=page*16+key;
  /* White playhead overrides amber programmed-step indicator. */
  if(e->playing&&br_index(&e->project.track[track],e->step_position?e->step_position-1:0)==(int)step)return BR_LED_PLAYHEAD_WHITE;
  return e->project.track[track].steps[step].on?BR_LED_STEP_AMBER:BR_LED_OFF;
}
static void BR_RAMCODE br_heap_push(BREngine *e,BREvent ev){
  if(e->events_used>=BR_EVENTS){e->overflows++;e->event_overflows++;return;}
  size_t k=e->events_used++;while(k){size_t prev=(k-1)/2;if(e->event_heap[prev].sample<=ev.sample)break;e->event_heap[k]=e->event_heap[prev];k=prev;}e->event_heap[k]=ev;
}
static BREvent BR_RAMCODE br_heap_pop(BREngine *e){
  BREvent first=e->event_heap[0],last=e->event_heap[--e->events_used];
  if(e->events_used){size_t j=0;while(2*j+1<e->events_used){size_t a=2*j+1,b=a+1;if(b<e->events_used&&e->event_heap[b].sample<e->event_heap[a].sample)a=b;if(last.sample<=e->event_heap[a].sample)break;e->event_heap[j]=e->event_heap[a];j=a;}e->event_heap[j]=last;}
  return first;
}
static void BR_RAMCODE br_queue_event(BREngine *e,int track,int step,uint64_t base,int slices,int vel,int accent,float jitter,int pitch,int note,int choke,float timbre,float dt){
  BRStep *st=&e->project.track[track].steps[step];
  for(int i=0;i<slices;i++){
    float seconds=(float)st->micro_ms*.001f + i*dt/slices + (i==0?0:0)+jitter;
    int64_t scheduled=(int64_t)base + (int64_t)llroundf(seconds*BR_SR);
    BREvent ev;memset(&ev,0,sizeof(ev));ev.sample=(uint64_t)BR_MAX(scheduled,(int64_t)e->sample_clock);
    ev.track=(uint8_t)track;ev.accent=(uint8_t)accent;ev.choke=(uint8_t)choke;ev.velocity=(uint8_t)vel;ev.pitch=(int16_t)pitch;ev.note=(int16_t)note;ev.timbre=timbre;
    br_heap_push(e,ev);
  }
}
typedef struct {int track,step,choke,echo;BRStep st;} BRPending;
static void BR_RAMCODE br_emit(BREngine *e,uint64_t base){
  float dt=60.0f/BR_CLAMP(e->project.bpm,40,240)/4.0f;
  uint8_t fired[BR_TRACKS]={0};
  BRPending pending[BR_TRACKS*2];int count=0;
  uint64_t pos=e->jump_enabled?e->jump_step:e->step_position;
  for(int i=0;i<BR_TRACKS;i++){
    BRTrack *v=&e->project.track[i];int n=br_index(v,pos);if(n<0)continue;
    BRStep *st=&v->steps[n];e->visits[i][n]++;
    if(!br_track_active(e,i))continue;
    float density=br_axis(e,i,st,BR_DENSITY),structure=br_axis(e,i,st,BR_STRUCTURE);
    int fire=st->on,conditional=st->cond_mode==BR_CONDITION;
    if(!conditional&&density>0){
      if(fire&&e->project.density_direction!=BR_ADD&&br_rand(e)<density*.26f)fire=0;
      else if(!fire&&e->project.density_direction!=BR_REMOVE&&br_rand(e)<density*.13f)fire=1;
    }
    if(!conditional&&structure&&e->project.structure_direction!=BR_ELABORATE&&fire&&br_rand(e)<structure*.18f)fire=0;
    int gate=st->cond_mode==BR_CONDITION ? ((e->visits[i][n]-1)%BR_CLAMP(st->cond_every,1,16)==BR_CLAMP(st->cond_on,1,BR_CLAMP(st->cond_every,1,16))-1) : (br_rand(e)*100<=st->prob);
    if(!fire||!gate){if(e->step_observer)e->step_observer(e->step_observer_ctx,(uint8_t)i,(uint8_t)n,0);continue;}
    fired[i]=1;pending[count++]=(BRPending){i,n,0,0,*st};
    if(e->step_observer)e->step_observer(e->step_observer_ctx,(uint8_t)i,(uint8_t)n,1);
  }
  for(int i=0;i<BR_TRACKS;i++){
    BRTrack *v=&e->project.track[i];int src=v->relation_source;
    if(!br_track_active(e,i)||src<0||src>=BR_TRACKS||src==i||!fired[src]||v->relationship==BR_NO_REL)continue;
    int n=br_index(v,pos);if(n<0)continue;
    BRStep *st=&v->steps[n];float rel=br_axis(e,i,st,BR_RELATIONS);
    if(!rel||br_rand(e)>=rel||st->cond_mode==BR_CONDITION)continue;
    if(v->relationship==BR_AVOID){
      for(int k=0;k<count;k++)if(pending[k].track==i){memmove(&pending[k],&pending[k+1],(size_t)(count-k-1)*sizeof(pending[0]));count--;k--;}
    }else if((v->relationship==BR_FOLLOW||v->relationship==BR_ECHO||v->relationship==BR_CHOKE)&&count<(int)(sizeof(pending)/sizeof(pending[0]))){
      BRPending ev={i,n,v->relationship==BR_CHOKE,v->relationship==BR_ECHO,*st};ev.st.ratchet=1;ev.st.micro_ms=0;ev.st.velocity=65;ev.st.accent=BR_GHOST;pending[count++]=ev;
    }
  }
  for(int k=0;k<count;k++){
    BRPending *p=&pending[k];BRTrack *v=&e->project.track[p->track];BRStep *st=&p->st;
    float timing=br_axis(e,p->track,st,BR_TIME),dyn=br_axis(e,p->track,st,BR_DYNAMICS),timbre=br_axis(e,p->track,st,BR_TIMBRE),structure=br_axis(e,p->track,st,BR_STRUCTURE),octave=br_axis(e,p->track,st,BR_OCTAVE);
    int slices=BR_CLAMP(st->ratchet,1,8);
    if(structure&&e->project.structure_direction!=BR_SIMPLIFY&&br_rand(e)<structure*.23f)slices=BR_MIN(8,slices+(br_rand(e)<.5f?1:2));
    if(structure&&e->project.structure_direction==BR_SIMPLIFY&&slices>1&&br_rand(e)<structure*.4f)slices--;
    int velocity=st->velocity;int accent=st->accent;
    if(dyn)velocity=BR_CLAMP((int)roundf(velocity*(1+(br_rand(e)*2-1)*dyn*.55f)),1,127);
    if(dyn&&accent==BR_NORMAL&&br_rand(e)<dyn*.25f)accent=br_rand(e)<.5f?BR_ACCENT:BR_GHOST;
    int octShift=0;
    if(octave&&br_rand(e)<octave*.8f){
      int lo=BR_CLAMP(v->oct_low,-3,3),hi=BR_CLAMP(v->oct_high,lo,3),choices[7],num=0;
      for(int x=lo;x<=hi;x++)if(x)choices[num++]=x;
      if(num)octShift=choices[(unsigned)(br_rand(e)*num)%num];
    }
    float jitter=timing?(br_rand(e)*2-1)*timing*.045f:0;
    uint64_t event_base=base+(uint64_t)llroundf((p->echo?dt:0)*BR_SR);
    br_queue_event(e,p->track,p->step,event_base,slices,velocity,accent,jitter,(st->pitch_semitones+12*octShift),st->midi_note==-1?-1:st->midi_note+12*octShift,p->choke,timbre?(br_rand(e)*2-1)*timbre:0,dt);
  }
  e->steps_generated++;e->step_position++;
}
void BR_RAMCODE br_step_once(BREngine *e){br_emit(e,e->sample_clock);}
static void BR_RAMCODE br_audio_voice(BREngine *e,unsigned track,unsigned velocity,int note,int pitch,BRAccent accent,int choke,float timbre,int held){
  if(track>=BR_TRACKS||!br_track_active(e,track))return;
  const BRTrack *v=&e->project.track[track];
  int slot=-1;for(int i=0;i<BR_POLYPHONY;i++)if(!e->active[i].active){slot=i;break;}
  if(slot<0){float age=-1;for(int i=0;i<BR_POLYPHONY;i++){if(e->active[i].elapsed>age){age=e->active[i].elapsed;slot=i;}}e->overflows++;e->voice_steals++;}
  BRPlayingVoice *q=&e->active[slot];memset(q,0,sizeof(*q));q->active=1;q->track=(uint8_t)track;q->held=(uint8_t)held;q->midi_key=(int16_t)note;q->midi_note=(int16_t)note;q->accent=accent;q->choke=choke;
  q->velocity=BR_CLAMP(velocity,1,127);q->timbre=timbre;
  float b=v->body/100.0f;
  static const float bases[] BR_RAMCONST={38,170,80,60,90},spans[] BR_RAMCONST={90,520,370,140,220};
  int family=BR_CLAMP(v->family,0,4);
  float freq=bases[family]+b*spans[family];
  if(note>=0)freq=br_midi_hz((float)note)*powf(2.0f,v->fine_cents/1200.0f);
  else freq*= (1.0f+timbre*.12f)*powf(2.0f,(float)pitch/12.0f);
  freq*=powf(2.0f,(float)v->voice_octave);
  freq=BR_CLAMP(freq,18.0f,16000.0f);
  q->frequency=freq;
  q->pitch_start=note<0?(family==BR_IMPACT?3.5f:1.35f):powf(2.0f,v->pitch_sweep/12.0f);
  q->pitch_end=1.0f;
  float dec=BR_MAX(.008f,v->env_decay_ms*.001f);
  q->duration=BR_MAX(.045f,dec+.08f+v->decay/100*.32f);
  q->pitch_sweep_time=BR_MIN(.14f,q->duration*.7f);
  q->osc_gain=family==BR_FRACTURE?.34f:.7f;
  q->noise_gain=BR_CLAMP(v->texture/100.0f,0,1)*(family==BR_IMPACT?.28f:.55f)*(accent==BR_GHOST?.55f:1.0f);
  q->peak=(.74f+v->attack/100.0f*.13f)*br_chgain(v->level)*(q->velocity/100.0f)*(accent==BR_ACCENT?1.38f:accent==BR_GHOST?.36f:1);
  q->release_time=BR_MAX(.012f,(choke?20:v->env_release_ms)*.001f/3.0f);
  e->total_triggers++;
}
void BR_RAMCODE br_trigger(BREngine *e,unsigned track,unsigned velocity,int midi_note){br_audio_voice(e,track,velocity,midi_note,0,BR_NORMAL,0,0,midi_note>=0);}
void BR_RAMCODE br_note_on(BREngine *e,unsigned track,unsigned note,unsigned velocity){
  if(velocity==0){br_note_off(e,track,note);return;}
  br_trigger(e,track,velocity,(int)note);
}
void BR_RAMCODE br_note_off(BREngine *e,unsigned track,unsigned note){
  if(track>=BR_TRACKS)return;
  for(int i=0;i<BR_POLYPHONY;i++){BRPlayingVoice *v=&e->active[i];if(v->active&&v->held&&v->track==track&&v->midi_key==(int)note){v->held=0;v->release_level=-1;v->release_start=v->elapsed;v->duration=BR_MAX(v->duration,v->elapsed+.6f);}}
}
static float BR_RAMCODE br_wave(int wave,float phase){
  float cycle=phase-floorf(phase);
  switch(wave){
    case BR_TRIANGLE:return 1.0f-4.0f*fabsf(cycle-.5f);
    case BR_SAW:return cycle*2.0f-1;
    case BR_SQUARE:return cycle<.5f?1.0f:-1.0f;
    default:return sinf(phase*(2*BR_PI));
  }
}
static float BR_RAMCODE br_voice_env(BREngine *e,BRPlayingVoice *q,const BRTrack *v){
  float t=q->elapsed,atk=BR_MAX(.001f,v->env_attack_ms*.001f),dec=BR_MAX(.008f,v->env_decay_ms*.001f);
  float sus=BR_CLAMP(v->env_sustain/100,0,1);
  float before=t;
  if(q->release_level<0.0f)before=q->release_start;
  else if(q->release_level>0.0f)before=q->release_start;
  float lev;
  /* The post-decay branch overwrites the earlier envelope unconditionally.
   * Do not evaluate that overwritten exponential and logarithm. */
  if(before>=atk+dec){
    float post=before-atk-dec;
    if(q->held&&sus>0)lev=sus;
    else if(q->release_level==0.0f)lev=BR_MAX(.0001f,sus)*br_env_exp_cached(e,-post/q->release_time);
    else lev=BR_MAX(.0001f,sus);
  }else if(before<atk){
    lev=BR_MAX(.0001f,before/atk);
  }else{
    /* Exactly the original log argument, cached until live sustain changes. */
    if(!e->env_log_valid[q->track]||e->env_log_source[q->track]!=sus){
      e->env_log_source[q->track]=sus;
      e->env_log_cache[q->track]=logf(BR_MAX(.0001f,sus));
      e->env_log_valid[q->track]=1;
    }
    lev=BR_MAX(.0001f,br_env_exp_cached(e,e->env_log_cache[q->track]*BR_MIN(1.0f,(before-atk)/dec)));
  }
  if(q->release_level<0.0f)q->release_level=BR_MAX(.0001f,lev);
  if(q->release_level>0.0f)lev=q->release_level*br_env_exp_cached(e,-(t-q->release_start)/BR_MAX(.015f,v->env_release_ms*.001f/3));
  return BR_MAX(0,lev*q->peak);
}
static float BR_RAMCODE br_voice_post(BREngine *e,BRPlayingVoice *q,
        const BRTrack *v,float env,float precomputed_noise){

  int w=v->waveform;
  if(w==BR_AUTO){static const int forms[] BR_RAMCONST={BR_SINE,BR_SINE,BR_SQUARE,BR_TRIANGLE,BR_SAW};w=forms[BR_CLAMP(v->family,0,4)];}
  /* Skip the LFO sine when its result is multiplied by exactly zero. */
  float lf=BR_CLAMP(v->lfo_depth/100,0,1),lfo=lf>0.0f?sinf(q->lfo_phase*2*BR_PI):0.0f;
  q->lfo_phase+=BR_CLAMP(v->lfo_rate_hz,.1f,30)/BR_SR;
  if(q->lfo_phase>=1.0f)q->lfo_phase-=1;
  float sweep=1.0f;
  if(fabsf(q->pitch_start-1)>0.00001f&&q->elapsed<q->pitch_sweep_time)sweep=(e?br_pitch_pow_cached(e,q->pitch_start,1.0f-q->elapsed/BR_MAX(.001f,q->pitch_sweep_time)):
      powf(q->pitch_start,1.0f-q->elapsed/BR_MAX(.001f,q->pitch_sweep_time)));
  float freq=q->frequency*sweep+(v->lfo_target==0?q->frequency*lf*.45f*lfo:0);
  freq=BR_CLAMP(freq,20.0f,BR_SR*.45f);
  q->phase+=freq/BR_SR;
  if(q->phase>1)q->phase-=floorf(q->phase);
  float tone=br_wave(w,q->phase)*q->osc_gain;
  float texture=BR_CLAMP(v->texture/100.0f,0,1);
  if(texture>.02f&&q->elapsed<BR_MIN(q->duration,.45f)){
    float noise=precomputed_noise;
    if(v->family==BR_ORGANIC){q->noise_state=(q->noise_state+noise*.13f)/1.13f;noise=q->noise_state*2;}
    /* Compact state-variable bandpass approximates Web Audio BiquadFilter. */
    if(!q->bp_ready||q->bp_last_texture!=texture){
      const float center=BR_CLAMP(350+texture*6500,50,BR_SR*.35f);
      const float qfact=.45f+texture*3;
      q->bp_f=BR_CLAMP(2.0f*sinf(BR_PI*center/BR_SR),.001f,.8f);
      q->bp_damp=BR_CLAMP(1.0f/qfact,.02f,1.0f);
      q->bp_last_texture=texture;q->bp_ready=1;
    }
    q->bp_low+=q->bp_f*q->bp_band;
    float high=noise-q->bp_low-q->bp_damp*q->bp_band;
    q->bp_band+=q->bp_f*high;
    tone+=(v->family==BR_IMPACT?high:q->bp_band)*q->noise_gain;
  }
  float x=env*tone;
  if(v->lfo_target==1)x*=1.0f+lf*.15f*lfo;
  if(v->bit_mix>0){
    float mix=BR_CLAMP(v->bit_mix/100,0,1),rate=BR_CLAMP(v->reduction_rate,4000,BR_SR);
    q->bit_phase+=rate/BR_SR;
    if(q->bit_phase>=1){q->bit_phase-=floorf(q->bit_phase);int bits=(int)BR_CLAMP(v->bit_depth,6,16);float levels=(float)(1u<<(bits-1));q->bit_hold=roundf(BR_CLAMP(x,-1,1)*levels)/levels;}
    x=x*(1-mix)+q->bit_hold*mix;
  }
  q->elapsed+=1/BR_SR;
  return x;
}
static float BR_RAMCODE br_one_voice(BREngine *e,BRPlayingVoice *q){
  if(!q->active)return 0;
  const BRTrack *v=&e->project.track[q->track];
  if(q->elapsed>q->duration+.35f&&!(q->held&&v->env_sustain>0)){q->active=0;return 0;}
  if(q->held&&q->elapsed>12.0f){q->held=0;q->duration=q->elapsed+.5f;}
  float env=br_voice_env(e,q,v);
  if(env<.000015f&&q->elapsed>BR_MAX(.05f,v->env_attack_ms*.001f)){q->active=0;return 0;}
  float noise=0;
  if(v->texture/100.0f>.02f && q->elapsed<BR_MIN(q->duration,.45f))noise=br_rand(e)*2-1;
  return br_voice_post(e,q,v,env,noise);
}
/* The browser convolves a random impulse. Native C reverb below is a four-comb
   feedback network; deliberately documented as a non-identical DSP substitute. */
#ifndef BR_FM1_COMPACT_FX
static float br_reverb(BREngine *e,float input){
  float sum=0;
  float size=BR_CLAMP(e->project.fx.reverb_size/100,0,1),feedback=.48f+size*.29f;
  for(int i=0;i<4;i++){
    BRReverbLine *c=&e->fx->reverb[i];int delay=(int)((float)c->length*(.58f+.38f*size));
    uint32_t read=(c->write+c->length-(uint32_t)delay)%c->length;
    float old=c->data[read];c->lp=c->lp*.65f+old*.35f;
    c->data[c->write]=input + c->lp*feedback;
    if(++c->write>=c->length)c->write=0;
    sum+=old*.25f;
  }
  return sum*(e->project.fx.reverb_wet/100.0f)*.8f;
}
/* Exact same floating-point resonator equations as before; the expensive
   constant coefficients are recalculated only on TUNE/DECAY edits. */
static void br_resonator_update(BREngine *e){
  const BRFX *fx=&e->project.fx;
  if(e->res_cache_valid && e->res_last_tune==fx->resonator_tune &&
     e->res_last_decay==fx->resonator_decay)return;
  const float norm=BR_CLAMP(fx->resonator_tune/100,0,1);
  const float dec=BR_CLAMP(fx->resonator_decay/100,0,1);
  const float thz=55.0f*powf(440.0f/55.0f,norm);
  const float shz=150.0f*powf(1200.0f/150.0f,norm);
  for(int r=0;r<3;r++){
    const float freq=r==0?thz:shz*(r==1?1:1.011f);
    const float fb=r==0?.33f+dec*.54f:.42f+dec*.46f;
    const uint32_t period=(uint32_t)BR_CLAMP((int)(BR_SR/freq),1,BR_RESONATOR_MAX-1);
    const float fc=r==0?440+norm*2800:2800+norm*7300;
    const float a=1.0f-expf(-2.0f*BR_PI*fc/BR_SR);
    e->res_period[r]=period;e->res_feedback[r]=fb;e->res_alpha[r]=a;
  }
  e->res_last_tune=fx->resonator_tune;e->res_last_decay=fx->resonator_decay;
  e->res_cache_valid=1;
}
static float br_resonator(BREngine *e,float input){
  const BRFX *fx=&e->project.fx;
  br_resonator_update(e);
  float out=0;
  for(int r=0;r<3;r++){
    const uint32_t read=(e->res_write[r]+BR_RESONATOR_MAX-e->res_period[r])%BR_RESONATOR_MAX;
    const float old=e->fx->resonator[r][read];
    e->res_lp[r]+=e->res_alpha[r]*(old-e->res_lp[r]);
    e->fx->resonator[r][e->res_write[r]]=input+e->res_lp[r]*e->res_feedback[r];
    if(++e->res_write[r]>=BR_RESONATOR_MAX)e->res_write[r]=0;
    if(r==0&&fx->resonator_model==BR_TUBE)out+=old*1.28f;
    else if(r>0&&fx->resonator_model==BR_STRING)out+=old*.83f;
  }
  return out;
}
#endif /* baseline reverb and resonator */
#ifdef BR_FM1_COMPACT_FX
/* The compact chain retains physical delay time and the four-comb reverb
   topology; it trades bandwidth, float precision and resonator for RAM.
   No allocation or file/network I/O in the audio thread. */
static int16_t BR_RAMCODE br_fx_pcm16(BREngine *e,float x){
  /* Fixed-headroom PCM storage, deliberately preserving headroom for
     concurrent polyphonic sends; exact peak and clips reported by stress. */
  float a=fabsf(x);
  if(a>e->compact_write_peak_max)e->compact_write_peak_max=a;
  /* Soft-knee protects 16-bit FX storage against massive concurrent sends.
     Quiet/music-level signals pass unmodified. Overload is *not* identical
     to the float32 ring; record each intervention transparently. */
  const float knee=BR_COMPACT_PCM_RANGE*.75f;
  if(a>knee){
    const float over=a-knee,room=BR_COMPACT_PCM_RANGE-knee;
    const float limited=knee+room*over/(room+over);
    x=x>=0?limited:-limited;
    e->compact_limiter_count++;
  }
  if(x>BR_COMPACT_PCM_RANGE){x=BR_COMPACT_PCM_RANGE;e->compact_clip_count++;}
  if(x<-BR_COMPACT_PCM_RANGE){x=-BR_COMPACT_PCM_RANGE;e->compact_clip_count++;}
  return (int16_t)lrintf(x*(32767.0f/BR_COMPACT_PCM_RANGE));
}
static float BR_RAMCODE br_fx_float(int16_t x){return (float)x*(BR_COMPACT_PCM_RANGE/32767.0f);}
static float BR_RAMCODE br_delay_compact(BREngine *e,float input){
  const BRFX *fx=&e->project.fx;
  /* 2-pole continuous anti-alias filtering. Updated at the master rate. */
#if BR_COMPACT_DELAY_DIV == 1
  /* Native-rate DELAY requires no anti-alias filter; preserve transients. */
  e->compact_delay_lp2=input;
#else
  e->compact_delay_lp1+=(input-e->compact_delay_lp1)*e->compact_delay_filter_alpha;
  e->compact_delay_lp2+=(e->compact_delay_lp1-e->compact_delay_lp2)*e->compact_delay_filter_alpha;
#endif
  if(e->compact_delay_phase==0){
    const float dt=60.0f/BR_CLAMP(e->project.bpm,40,240)*4.0f/
                   BR_CLAMP(fx->delay_division,2,8);
    const float rate=BR_SR/(float)BR_COMPACT_DELAY_DIV;
    const uint32_t len=(uint32_t)BR_CLAMP((int)(dt*rate),1,BR_COMPACT_DELAY_FRAMES-1);
    const uint32_t rd=(e->compact_delay_write+BR_COMPACT_DELAY_FRAMES-len)%BR_COMPACT_DELAY_FRAMES;
    const float old=br_fx_float(e->compact_fx->delay[rd]);
    e->delay_lp+=(old-e->delay_lp)*e->compact_feedback_alpha;
    const float wr=e->compact_delay_lp2 + e->delay_lp*
                     BR_CLAMP(fx->delay_feedback/100*.78f,0,.75f);
    e->compact_fx->delay[e->compact_delay_write]=br_fx_pcm16(e,wr);
    if(++e->compact_delay_write>=BR_COMPACT_DELAY_FRAMES)e->compact_delay_write=0;
    e->compact_delay_previous=e->compact_delay_current;
    e->compact_delay_current=old;
  }
  const float frac=(float)e->compact_delay_phase/(float)BR_COMPACT_DELAY_DIV;
#if BR_COMPACT_DELAY_DIV == 1
  const float result=e->compact_delay_current;
#else
  const float result=e->compact_delay_previous+(e->compact_delay_current-e->compact_delay_previous)*frac;
#endif
  e->compact_delay_phase++;
  if(e->compact_delay_phase>=BR_COMPACT_DELAY_DIV)e->compact_delay_phase=0;
  return result*(fx->delay_wet/100.0f)*.7f;
}
static float BR_RAMCODE br_reverb_compact(BREngine *e,float input){
  const BRFX *fx=&e->project.fx;
  e->compact_reverb_lp1+=(input-e->compact_reverb_lp1)*e->compact_reverb_filter_alpha;
  e->compact_reverb_lp2+=(e->compact_reverb_lp1-e->compact_reverb_lp2)*e->compact_reverb_filter_alpha;
  if(e->compact_reverb_phase==0){
    static const uint32_t len[4] BR_RAMCONST={BR_COMPACT_R0,BR_COMPACT_R1,BR_COMPACT_R2,BR_COMPACT_R3};
    static const uint32_t offs[4] BR_RAMCONST={0,BR_COMPACT_R0,BR_COMPACT_R0+BR_COMPACT_R1,
                            BR_COMPACT_R0+BR_COMPACT_R1+BR_COMPACT_R2};
    const float size=BR_CLAMP(fx->reverb_size/100.0f,0,1);
    const float feedback=.48f+size*.29f;
    float sum=0;
    for(int i=0;i<4;i++){
      const uint32_t delay=(uint32_t)BR_CLAMP((int)((float)len[i]*(.58f+.38f*size)),1,(int)len[i]-1);
      const uint32_t wr=e->compact_reverb_write[i];
      const uint32_t rd=(wr+len[i]-delay)%len[i];
      const float old=br_fx_float(e->compact_fx->reverb[offs[i]+rd]);
      e->compact_reverb_line_lp[i]=e->compact_reverb_line_lp[i]*.65f+old*.35f;
      const float write=e->compact_reverb_lp2+e->compact_reverb_line_lp[i]*feedback;
      e->compact_fx->reverb[offs[i]+wr]=br_fx_pcm16(e,write);
      e->compact_reverb_write[i]=(wr+1)%len[i];
      sum+=old*.25f;
    }
    e->compact_reverb_previous=e->compact_reverb_current;
    e->compact_reverb_current=sum;
  }
  const float frac=(float)e->compact_reverb_phase/(float)BR_COMPACT_REVERB_DIV;
  const float result=e->compact_reverb_previous+(e->compact_reverb_current-e->compact_reverb_previous)*frac;
  e->compact_reverb_phase++;
  if(e->compact_reverb_phase>=BR_COMPACT_REVERB_DIV)e->compact_reverb_phase=0;
  return result*(fx->reverb_wet/100.0f)*.8f;
}
#endif
static float BR_RAMCODE br_drive(BREngine *e,float x){
  float k=BR_CLAMP(e->project.fx.drive,0,100)/100*70.0f;
  if(k<.01f)return x;
  if(!e->drive_cache_valid||e->drive_last!=e->project.fx.drive){
    e->drive_last=e->project.fx.drive;
    e->drive_denom=tanhf(1+k*.065f);
    e->drive_cache_valid=1;
  }
  return tanhf(x*(1+k*.065f))/e->drive_denom;
}
static float BR_RAMCODE br_soft_clip(float x){
  float m=fabsf(x),k=.78f;
  return (x<0?-1.0f:1.0f)*(m<=k?m:k+(1-k)*tanhf((m-k)/(1-k)));
}
static float BR_RAMCODE br_compress(BREngine *e,float x){
  BRFX *f=&e->project.fx;if(f->comp_ratio<=1.05f)return x;
  float amp=fabsf(x);
  float a=amp>e->compressor_envelope?.02f:.0003f;
  e->compressor_envelope+=a*(amp-e->compressor_envelope);
  if(!e->comp_cache_valid||e->comp_last_ratio!=f->comp_ratio||
     e->comp_last_threshold!=f->comp_threshold_db){
    e->comp_threshold=br_db(f->comp_threshold_db);
    e->comp_inv_ratio=1.0f/BR_MAX(f->comp_ratio,1)-1.0f;
    const float makeupDb=BR_CLAMP((-f->comp_threshold_db-6)*(1-1.0f/f->comp_ratio)*.5f,0,5);
    e->comp_makeup=br_db(makeupDb);
    e->comp_last_ratio=f->comp_ratio;e->comp_last_threshold=f->comp_threshold_db;
    e->comp_cache_valid=1;
  }
  float gain=1;
  if(e->compressor_envelope>e->comp_threshold){
    const float over=e->compressor_envelope/BR_MAX(e->comp_threshold,1e-6f);
    gain=powf(over,e->comp_inv_ratio);
  }
  return x*gain*e->comp_makeup;
}
#ifdef BR3_DUAL_CORE
/* Six TRACKS, NOT six slots: all BR_POLYPHONY instances remain intact. */
static BR3Executor br3_executor;
void br3_set_executor(const BR3Executor *ops){
  if(ops)br3_executor=*ops;
  else memset(&br3_executor,0,sizeof(br3_executor));
}
#endif
#ifdef BR3_DUAL_CORE
/* Batch a bounded number of samples per request. Scheduler runs only at exact
   boundaries, so no note/step/event is incorrectly moved in time. */
#define BR3_SLICE_FRAMES 32u
typedef struct {
  BREngine *engine;
  BRPlayingVoice cpu1_shadow[BR_POLYPHONY];
  BRPlayingVoice cpu1_before[BR_POLYPHONY]; /* rollback if CPU1 was forcibly held */
  uint8_t ready[BR3_SLICE_FRAMES][BR_POLYPHONY];
  float env[BR3_SLICE_FRAMES][BR_POLYPHONY];
  float noise[BR3_SLICE_FRAMES][BR_POLYPHONY];
  float sample[BR3_SLICE_FRAMES][BR_POLYPHONY];
  uint32_t frames;
} BR3Segment;
static BR3Segment br3_seg;
static void BR_RAMCODE br3_upper_segment(void *data){
  BR3Segment *s=(BR3Segment*)data;
  BREngine *e=s->engine;
  for(uint32_t n=0;n<s->frames;n++){
    for(int i=0;i<BR_POLYPHONY;i++){
      BRPlayingVoice *q=&s->cpu1_shadow[i];
      if(s->ready[n][i] && q->track>=3)
        s->sample[n][i]=br_voice_post(NULL,q,&e->project.track[q->track],s->env[n][i],s->noise[n][i]);
    }
  }
}
static void BR_RAMCODE br3_fx(BREngine *e,float dry,float ds,float rv,float rs,float *interleaved_stereo){
#ifndef BR_FM1_COMPACT_FX
  BRFX *fx=&e->project.fx;
#endif
    float delayed=0,reverb=0,res=0;
#ifdef BR_FM1_COMPACT_FX
    (void)rs; /* deliberate FM-1 build concession: resonator absent. */
    delayed=br_delay_compact(e,ds);
    reverb=br_reverb_compact(e,rv);
#else
    {float dt=60.0f/BR_CLAMP(e->project.bpm,40,240)*4.0f/BR_CLAMP(fx->delay_division,2,8);
     uint32_t delayFrames=(uint32_t)BR_CLAMP((int)(dt*BR_SR),1,BR_DELAY_MAX-1);
     uint32_t rd=(e->delay_write+BR_DELAY_MAX-delayFrames)%BR_DELAY_MAX;
     float recirc=e->fx->delay[rd];
     e->delay_lp+=e->delay_lp_coeff*(recirc-e->delay_lp);
     e->fx->delay[e->delay_write]=ds + e->delay_lp*BR_CLAMP(fx->delay_feedback/100*.78f,0,.75f);
     if(++e->delay_write>=BR_DELAY_MAX)e->delay_write=0;
     delayed=recirc*(fx->delay_wet/100)*.7f;
    }
    reverb=br_reverb(e,rv);
    res=br_resonator(e,rs);
#endif
    float mono=br_drive(e,dry)+delayed+reverb+res;
    mono=br_compress(e,mono)*2.2f;
    mono=br_soft_clip(mono)*BR_CLAMP(e->project.master,0,1);
    interleaved_stereo[0]=mono;interleaved_stereo[1]=mono;
    e->sample_clock++;
}
static void BR_RAMCODE br3_render_segmented(BREngine *e,float *out,size_t frames){
  BR3Segment *s=&br3_seg;
  s->engine=e;
  size_t offset=0;
  while(offset<frames){
    /* Same order as the original br_render: step, roll, queued events. */
    if(e->playing&&e->sync_source==BR_INTERNAL&&e->sample_clock>=e->next_step_sample){
      br_emit(e,e->next_step_sample);
      double stepSamples=BR_SR*60.0/(BR_CLAMP(e->project.bpm,40,240)*4.0);
      e->step_fraction+=stepSamples;
      uint64_t increment=(uint64_t)e->step_fraction;
      e->step_fraction-=increment;e->next_step_sample+=increment?increment:1;
    }
    if(e->roll_held&&e->sample_clock>=e->next_roll_sample){
      int division=e->project.roll_division;
      float seconds=60.0f/BR_CLAMP(e->project.bpm,40,240) *
          (division==0?.5f:division==1?.25f:division==2?.125f:(1.0f/6.0f));
      br_audio_voice(e,BR_CLAMP(e->project.selected_track,0,5),100,-1,0,BR_NORMAL,0,0,0);
      e->next_roll_sample=e->sample_clock+(uint64_t)BR_MAX(1,lroundf(seconds*BR_SR));
    }
    while(e->events_used&&e->event_heap[0].sample<=e->sample_clock){
      BREvent ev=br_heap_pop(e);
      br_audio_voice(e,ev.track,ev.velocity,ev.note,ev.pitch,(BRAccent)ev.accent,ev.choke,ev.timbre,0);
    }
    uint64_t span=(uint64_t)(frames-offset);
    if(span>BR3_SLICE_FRAMES)span=BR3_SLICE_FRAMES;
    if(e->playing&&e->sync_source==BR_INTERNAL&&e->next_step_sample>e->sample_clock){
      uint64_t n=e->next_step_sample-e->sample_clock;if(n<span)span=n;
    }
    if(e->roll_held&&e->next_roll_sample>e->sample_clock){
      uint64_t n=e->next_roll_sample-e->sample_clock;if(n<span)span=n;
    }
    if(e->events_used&&e->event_heap[0].sample>e->sample_clock){
      uint64_t n=e->event_heap[0].sample-e->sample_clock;if(n<span)span=n;
    }
    if(!span)span=1;
    s->frames=(uint32_t)span;
    BRPlayingVoice simulated[BR_POLYPHONY];
    memcpy(simulated,e->active,sizeof(simulated));
    for(uint32_t n=0;n<span;n++){
      for(int i=0;i<BR_POLYPHONY;i++){
        BRPlayingVoice *q=&simulated[i];
        s->ready[n][i]=0;s->sample[n][i]=0;
        if(!q->active)continue;
        const BRTrack *v=&e->project.track[q->track];
        if(q->elapsed>q->duration+.35f&&!(q->held&&v->env_sustain>0)){q->active=0;continue;}
        if(q->held&&q->elapsed>12.0f){q->held=0;q->duration=q->elapsed+.5f;}
        float env=br_voice_env(e,q,v);
        if(env<.000015f&&q->elapsed>BR_MAX(.05f,v->env_attack_ms*.001f)){q->active=0;continue;}
        s->env[n][i]=env;s->noise[n][i]=0;
        if(v->texture/100.0f>.02f && q->elapsed<BR_MIN(q->duration,.45f))
          s->noise[n][i]=br_rand(e)*2-1;
        s->ready[n][i]=1;
        q->elapsed+=1/BR_SR;
      }
    }
    /* Refresh all slot identities: a globally shared polyphony slot can be
       stolen and reassigned from CPU1's lane to CPU0's lane between batches. */
    for(int i=0;i<BR_POLYPHONY;i++)s->cpu1_shadow[i]=e->active[i];
    memcpy(s->cpu1_before,s->cpu1_shadow,sizeof(s->cpu1_shadow));
    int started=br3_executor.submit ? br3_executor.submit(br3_upper_segment,s,s->frames):0;
    if(!started)br3_upper_segment(s);
    for(uint32_t n=0;n<span;n++){
      for(int i=0;i<BR_POLYPHONY;i++){
        BRPlayingVoice *q=&e->active[i];
        if(s->ready[n][i] && q->track<3)
          s->sample[n][i]=br_voice_post(NULL,q,&e->project.track[q->track],s->env[n][i],s->noise[n][i]);

      }
    }
    if(started && br3_executor.wait && !br3_executor.wait()){
      /* The wait callback MUST have halted CPU1 before returning failure. */
      memcpy(s->cpu1_shadow,s->cpu1_before,sizeof(s->cpu1_shadow));
      br3_upper_segment(s);
    }
    for(int i=0;i<BR_POLYPHONY;i++){
      if(simulated[i].track>=3)e->active[i]=s->cpu1_shadow[i];
      /* Envelope state was advanced in serial-order by CPU0's preflight.
         Oscillator/filter state was advanced independently by its owner. */
      e->active[i].active=simulated[i].active;
      e->active[i].held=simulated[i].held;
      e->active[i].duration=simulated[i].duration;
      e->active[i].release_level=simulated[i].release_level;
      e->active[i].release_start=simulated[i].release_start;
    }
    for(uint32_t n=0;n<span;n++){
      float dry=0,ds=0,rv=0,rs=0;
      for(int i=0;i<BR_POLYPHONY;i++){
        if(!s->ready[n][i])continue;
        const BRTrack *v=&e->project.track[simulated[i].track];
        float value=s->sample[n][i];



        dry+=value;ds+=value*v->send_delay/100.0f;
        rv+=value*v->send_reverb/100.0f;rs+=value*v->send_resonator/100.0f;
      }
      br3_fx(e,dry,ds,rv,rs,out+(offset+n)*2);
    }
    offset+=span;
  }
}
#endif
void BR_RAMCODE br_render(BREngine *e,float *interleaved_stereo,size_t frames){
  if(!e||!interleaved_stereo)return;
#ifdef BR_FM1_COMPACT_FX
  if(!e->compact_fx){memset(interleaved_stereo,0,frames*2*sizeof(float));return;}
#else
  if(!e->fx){memset(interleaved_stereo,0,frames*2*sizeof(float));return;}
#endif
#ifdef BR3_DUAL_CORE
  br3_render_segmented(e,interleaved_stereo,frames);
  return;
#else
#ifndef BR_FM1_COMPACT_FX
  BRFX *fx=&e->project.fx;
#endif
  for(size_t n=0;n<frames;n++){
    if(e->playing&&e->sync_source==BR_INTERNAL&&e->sample_clock>=e->next_step_sample){
      br_emit(e,e->next_step_sample);
      double stepSamples=BR_SR*60.0/(BR_CLAMP(e->project.bpm,40,240)*4.0);
      e->step_fraction+=stepSamples;
      uint64_t increment=(uint64_t)e->step_fraction;
      e->step_fraction-=increment;e->next_step_sample+=increment?increment:1;
    }
    if(e->roll_held&&e->sample_clock>=e->next_roll_sample){
      int division=e->project.roll_division;
      float seconds=60.0f/BR_CLAMP(e->project.bpm,40,240) *
          (division==0?.5f:division==1?.25f:division==2?.125f:(1.0f/6.0f));
      br_audio_voice(e,BR_CLAMP(e->project.selected_track,0,5),100,-1,0,BR_NORMAL,0,0,0);
      e->next_roll_sample=e->sample_clock+(uint64_t)BR_MAX(1,lroundf(seconds*BR_SR));
    }
    while(e->events_used&&e->event_heap[0].sample<=e->sample_clock){
      BREvent ev=br_heap_pop(e);
      br_audio_voice(e,ev.track,ev.velocity,ev.note,ev.pitch,(BRAccent)ev.accent,ev.choke,ev.timbre,0);
    }
    float dry=0,ds=0,rv=0,rs=0;
#ifdef BR3_DUAL_CORE
    br3_mix_voices(e,&dry,&ds,&rv,&rs);
#else
    for(int i=0;i<BR_POLYPHONY;i++){
      BRPlayingVoice *q=&e->active[i];if(!q->active)continue;
      float value=br_one_voice(e,q);const BRTrack *v=&e->project.track[q->track];
      dry+=value;ds+=value*v->send_delay/100.0f;rv+=value*v->send_reverb/100.0f;rs+=value*v->send_resonator/100.0f;
    }
#endif
    float delayed=0,reverb=0,res=0;
#ifdef BR_FM1_COMPACT_FX
    (void)rs; /* deliberate FM-1 build concession: resonator absent. */
    delayed=br_delay_compact(e,ds);
    reverb=br_reverb_compact(e,rv);
#else
    {float dt=60.0f/BR_CLAMP(e->project.bpm,40,240)*4.0f/BR_CLAMP(fx->delay_division,2,8);
     uint32_t delayFrames=(uint32_t)BR_CLAMP((int)(dt*BR_SR),1,BR_DELAY_MAX-1);
     uint32_t rd=(e->delay_write+BR_DELAY_MAX-delayFrames)%BR_DELAY_MAX;
     float recirc=e->fx->delay[rd];
     e->delay_lp+=e->delay_lp_coeff*(recirc-e->delay_lp);
     e->fx->delay[e->delay_write]=ds + e->delay_lp*BR_CLAMP(fx->delay_feedback/100*.78f,0,.75f);
     if(++e->delay_write>=BR_DELAY_MAX)e->delay_write=0;
     delayed=recirc*(fx->delay_wet/100)*.7f;
    }
    reverb=br_reverb(e,rv);
    res=br_resonator(e,rs);
#endif
    float mono=br_drive(e,dry)+delayed+reverb+res;
    mono=br_compress(e,mono)*2.2f;
    mono=br_soft_clip(mono)*BR_CLAMP(e->project.master,0,1);
    interleaved_stereo[n*2]=mono;interleaved_stereo[n*2+1]=mono;
    e->sample_clock++;
  }
#endif
}
void BR_RAMCODE br_set_sync(BREngine *e,BRClockSource source){e->sync_source=(uint8_t)source;e->external_clock_pulses=0;}
static int BR_RAMCODE br_midi_channel_track(BREngine *e,int channel,int note){
  if(channel>=0&&channel<6)return channel;
  if(channel==9)return BR_CLAMP(note-36,0,BR_TRACKS-1);
  return BR_CLAMP(e->project.selected_track,0,5);
}
/* MIDI IN: running status, realtime interleaving, note on/off and MIDI Clock. */
void BR_RAMCODE br_midi_byte(BREngine *e,uint8_t b,BRClockSource source){
  if(b>=0xf8){
    if(e->sync_source!=(uint8_t)source)return;
    if(b==0xfa){br_start(e);e->external_clock_pulses=0;}
    if(b==0xfb){e->playing=1;}
    if(b==0xfc){br_stop(e);}
    if(b==0xf8&&e->playing){
      if(e->last_clock_sample&&e->sample_clock>e->last_clock_sample){
        float interval=(float)(e->sample_clock-e->last_clock_sample);
        e->clock_interval_avg=e->clock_interval_avg<=0?interval:(.9f*e->clock_interval_avg+.1f*interval);
        float bpm=BR_SR*60/(e->clock_interval_avg*24);
        if(bpm>=40&&bpm<=240)e->project.bpm=bpm;
      }
      e->last_clock_sample=e->sample_clock;
      if(++e->external_clock_pulses>=6){e->external_clock_pulses=0;br_emit(e,e->sample_clock);}
    }
    return;
  }
  if(b&0x80){
    if(b>=0xf0){e->midi_status=0;e->midi_index=0;return;}
    e->midi_status=b;e->midi_index=0;e->midi_expected=((b&0xf0)==0xc0||(b&0xf0)==0xd0)?1:2;return;
  }
  if(!e->midi_status)return;
  e->midi_data[e->midi_index++]=b;
  if(e->midi_index<e->midi_expected)return;
  int command=e->midi_status&0xf0,ch=e->midi_status&15;
  int note=e->midi_data[0],velocity=e->midi_data[1],track=br_midi_channel_track(e,ch,note);
  if(command==0x90){if(velocity)br_note_on(e,track,note,velocity);else br_note_off(e,track,note);}
  else if(command==0x80)br_note_off(e,track,note);
  e->midi_index=0;
}
