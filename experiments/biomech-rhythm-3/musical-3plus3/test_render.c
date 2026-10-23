#include "biomech.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#ifdef BR3_DUAL_CORE
#include <pthread.h>
#include <semaphore.h>
static sem_t req,done;
static pthread_t thread;
static void (*job)(void *);
static void *arg;
static int stop;
static uint32_t jobs;
static int inject_errors;
static void *worker(void *ignored) {
  (void)ignored;
  for(;;) {
    sem_wait(&req);
    if(stop)break;
    job(arg);
    sem_post(&done);
  }
  return NULL;
}
static int launch(void (*f)(void*),void *a,uint32_t frames) {
  if(frames==0 || frames>32)return 0;
  ++jobs;
  if(inject_errors && jobs%13==0)return 0; /* fallback without dispatch */
  job=f;arg=a;sem_post(&req);return 1;
}
static int join_cpu1(void) {
  for(;;){if(!sem_wait(&done))break;if(errno!=EINTR)return 0;}
  return !(inject_errors && jobs%7==0); /* simulated late finish AFTER joining worker */
}
#endif
int main(int argc,char**argv){
  if(argc!=2 && argc!=3)return 2;
  const int seq_mode=argc==3?atoi(argv[2]):0;
#ifdef BR3_DUAL_CORE
  inject_errors = getenv("BR3_INJECT_CPU1_ERRORS")!=NULL;
#endif
#ifdef BR3_DUAL_CORE
  sem_init(&req,0,0);sem_init(&done,0,0);
  pthread_create(&thread,0,worker,0);
  BR3Executor exec={launch,join_cpu1};br3_set_executor(&exec);
#endif
  BREngine *e=calloc(1,sizeof(*e));
  BRCompactFXBuffers *fx=calloc(1,sizeof(*fx));
  if(!e||!fx)return 3;
  br_init_compact_with_fx(e,fx);
  e->project.fx.drive=9.0f;
  e->project.fx.delay_wet=24.0f;
  e->project.fx.reverb_wet=26.0f;
  e->project.fx.comp_ratio=2.0f;
  e->project.axis[BR_DENSITY]=12;
  e->project.axis[BR_TIME]=8;
  e->project.axis[BR_DYNAMICS]=25;
  for(int t=0;t<6;t++){
    br_init_sound(&e->project.track[t]);
    e->project.track[t].family=(uint8_t)(t%5);
    e->project.track[t].waveform=(uint8_t)(1+(t%4));
    e->project.track[t].texture=(float)(10+t*13);
    e->project.track[t].bit_mix=(float)(t*11);
    e->project.track[t].pitch_sweep=32.0f;
    e->project.track[t].lfo_depth=25.0f;
    e->project.track[t].send_reverb=5+t*7;
    e->project.track[t].send_delay=15+t*4;
    e->project.track[t].level=58+t*4;
  }
  if(seq_mode==1){
    for(int t=0;t<6;t++){
      e->project.track[t].length=(uint8_t)(8+t*4);
      for(int n=0;n<BR_STEPS;n++){
        BRStep *st=&e->project.track[t].steps[n];
        st->on=(uint8_t)((n%(2+(t%3)))==0);
        st->prob=(uint8_t)(55+(n%3)*15);
        st->ratchet=(uint8_t)((n%5)==0?2:1);
        st->velocity=(uint8_t)(75+n%30);
      }
    }
    br_start(e);
  }
  FILE *f=fopen(argv[1],"wb");if(!f)return 4;
  float out[128*2];
  const int chunks=seq_mode?1024:512; // includes FX tails, triggers, MIDI and generated steps
  for(int b=0;b<chunks;b++){
    if(seq_mode==2 && b%2==0){
      for(int t=0;t<6;t++)br_note_on(e,t,(unsigned)(24+(b/2+t*7)%72),95);
    }
    if(seq_mode==0 && (b==0||b==64||b==128||b==256||b==340)){
      for(int t=0;t<6;t++)br_note_on(e,t,42+t*3,70+8*t);
    }
    if(seq_mode==0 && (b==32||b==96||b==175||b==290||b==410)){
      for(int t=0;t<6;t++)br_note_off(e,t,42+t*3);
    }
    if(b==200){for(int t=0;t<6;t++)e->project.track[t].env_sustain=(float)(t*11);}
    if(b==260){for(int t=0;t<6;t++)e->project.track[t].pitch_sweep=52+t*2;}
    if(seq_mode && b==350)br_roll_hold(e,1);
    if(seq_mode && b==390)br_roll_hold(e,0);
    if(seq_mode && b==520)e->project.bpm=143;
    if(seq_mode && b==620)br_step_jump(e,6,1);
    if(seq_mode && b==625)br_step_jump(e,6,0);
    if(seq_mode && b==730)br_stop(e);
    br_render(e,out,128);
#ifdef BR3_DEBUG_EVENT
    uint64_t hash=0xcbf29ce484222325ull;
    const unsigned char *bytes=(const unsigned char*)e->active;
    for(size_t z=0;z<sizeof(e->active);z++)hash=(hash^bytes[z])*0x100000001b3ull;
    fprintf(stderr,"STATE b=%d clock=%llu rng=%08x voicehash=%016llx\n",b,(unsigned long long)e->sample_clock,e->rng,(unsigned long long)hash);
#endif
    if(fwrite(out,sizeof(out),1,f)!=1)return 5;
  }
  fclose(f);
#ifdef BR3_DUAL_CORE
  stop=1;sem_post(&req);pthread_join(thread,0);sem_destroy(&req);sem_destroy(&done);
#endif
  fprintf(stderr,"DONE seed=%08x active=%u triggers=%llu clips=%llu\n",e->rng,(unsigned)e->events_used,(unsigned long long)e->total_triggers,(unsigned long long)e->compact_clip_count);
  free(fx);free(e);
  return 0;
}
