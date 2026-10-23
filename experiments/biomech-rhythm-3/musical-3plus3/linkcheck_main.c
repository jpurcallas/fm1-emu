/* BIOMECH 3: native PI32v2 MUSIC DSP CPU1 on-board selftest.
 * Isolated test, NOT a user-facing audio firmware or installable .fwsc.
 */
#include "biomech.h"
#ifndef BR3_SERIAL_REFERENCE
#include "br3_cpu1_runtime.h"
#include "br3_blackbox.h"
#endif
#include <stdint.h>
#include <math.h>
#define BR3_TEST_PASS 0xB330A11Fu
#define BR3_TEST_FAIL_CPU1 0xB33E0001u
#define BR3_TEST_FAIL_DSP 0xB33E0002u
BREngine br3_synth;
BRCompactFXBuffers br3_effects;
float br3_samples[256];
volatile uint32_t br3_test_status,br3_test_peakbits,br3_test_checksum,br3_test_rendered;
void __attribute__((noreturn)) br3_cpu0_main(void){
  br3_test_status=0xB3300001u;
  br_init_compact_with_fx(&br3_synth,&br3_effects);
  /* Six existing tracks; sustain/MIDI to exercise all lanes. */
  for(unsigned t=0;t<BR_TRACKS;t++){
    BRTrack *v=&br3_synth.project.track[t];
    v->family=(uint8_t)(t%5u);
    v->waveform=(uint8_t)(1u+t%4u);
    v->texture=10.0f+(float)(t*9);
    v->env_attack_ms=3;
    v->env_decay_ms=250;
    v->env_sustain=25;
    v->bit_mix=(float)(t*4);
  }
  br3_test_status=0xB3300002u;
#ifndef BR3_SERIAL_REFERENCE
  if(!br3_cpu1_start()){
    br3_test_status=BR3_TEST_FAIL_CPU1;
    goto park;
  }
  br3_cpu1_attach();
#endif
  for(unsigned t=0;t<BR_TRACKS;t++)br_note_on(&br3_synth,t,36u+t*4u,100);
#ifdef BR3_NATIVE_STRESS
  /* Standalone emulated native stress: overlap far more notes than the
     64-slot pool and exercise deterministic voice stealing on each side. */
  for(unsigned t=0;t<BR_TRACKS;t++){
    BRTrack *v=&br3_synth.project.track[t];
    v->env_decay_ms=900.0f;
    v->env_sustain=80.0f;
  }
#endif
  float peak=0;
  uint32_t hash=2166136261u;
  for(unsigned b=0;b<32;b++){
#ifdef BR3_NATIVE_STRESS
    if(b<28u && !(b&1u)){
      for(unsigned t=0;t<BR_TRACKS;t++)
        br_note_on(&br3_synth,t,36u+(t*7u+b*3u)%46u,82u+(b%13u));
    }
    if(b==21u){
      for(unsigned t=0;t<BR_TRACKS;t++)br_note_off(&br3_synth,t,36u+t*4u);
    }
#endif
    br_render(&br3_synth,br3_samples,128);
    for(unsigned i=0;i<256;i++){
      float x=br3_samples[i];
      if(x>peak)peak=x;
      if(-x>peak)peak=-x;
      union {float f;uint32_t u;}bits;
      bits.f=x;
      hash=(hash^bits.u)*16777619u;
    }
    br3_test_rendered=b+1u;
  }
  {union {float f;uint32_t u;} peakbits;peakbits.f=peak; br3_test_peakbits=peakbits.u;}
  br3_test_checksum=hash;
#ifdef BR3_SERIAL_REFERENCE
  br3_test_status=(peak>0.00001f)?BR3_TEST_PASS:BR3_TEST_FAIL_DSP;
#else
  br3_test_status=(peak>0.00001f && br3_blackbox.jobs_sent>0u &&
     br3_blackbox.jobs_done>0u && br3_blackbox.job_timeouts==0u)?BR3_TEST_PASS:BR3_TEST_FAIL_DSP;
#endif
park:
  for(;;)__asm__ volatile("csync":::"memory");
}
