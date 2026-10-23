/* REminiSCENT v0.6: CPU-independent DSP stages for a possible FM-1 CPU1.
 * NO pthread, SDK, DMA, direct CPU1 registers or timing assumptions here.
 * Mutating events, acoustic decode and voice ownership are CPU0 prework.
 * Part stems are private by PART. Global FX remain CPU0 after worker joins.
 */
#include "rn_v12_dualcore_kernel.h"

int rn_dc_prepare(rn_v12_dsp *s,int32_t *out,unsigned frames,rn_dc_job *h){
 if(!s||!out||!h||frames!=128u||!s->acoustic.initialized)return -1;
 rn_seq_advance(&s->seq,s,frames);
 volatile int32_t *reset=(volatile int32_t *)out;
 for(unsigned i=0;i<256u;i++)reset[i]=0;
 if(s->acoustic.flash_guard){s->acoustic.suppressed_blocks++;return 1;}
 for(unsigned p=0;p<4;p++)for(unsigned j=0;j<256u;j++)s->acoustic_stems[p][j]=0;
 if(s->acoustic.source.bank.count&&as_render_parts(&s->acoustic.source,s->acoustic_stems,frames))return -2;
 /* CPU0 captures voice selection before CPU1 receives pointers to the engine.
  * Voice arrays of different PARTS are disjoint in the worker phase. */
 for(unsigned p=0;p<4;p++)h->count[p]=0;
 for(unsigned i=0;i<RN_OSC_VOICES;i++){
  const rn_osc_voice *v=&s->digital.voices[i];
  if(v->active && v->part<4u)h->selected[v->part][h->count[v->part]++]=(uint8_t)i;
 }
 h->engine=s;h->frames=frames;
 return 0;
}

void rn_dc_render_range(rn_dc_job *h,unsigned first,unsigned last){
 rn_v12_dsp *s=h->engine;
 int32_t scratch[256]; /* one private buffer per CPU worker, not shared */
 for(unsigned p=first;p<last;p++){
  for(unsigned j=0;j<256u;j++)scratch[j]=0;
  rn_osc_render_selected(&s->digital,p,h->selected[p],h->count[p],scratch,h->frames);
  for(unsigned j=0;j<256u;j+=2){
   unsigned blend=s->digital.part[p].blend;
   int32_t dryL=s->acoustic_stems[p][j],dryR=s->acoustic_stems[p][j+1];
   if(blend){
    int32_t digL=(int32_t)(((int64_t)scratch[j]*s->acoustic.source.gain_q15[p]*s->osc_level[p])/(32767ll*127));
    int32_t digR=(int32_t)(((int64_t)scratch[j+1]*s->acoustic.source.gain_q15[p]*s->osc_level[p])/(32767ll*127));
    dryL=blend==127?digL:(int32_t)(((int64_t)dryL*(127-blend)+(int64_t)digL*blend)/127);
    dryR=blend==127?digR:(int32_t)(((int64_t)dryR*(127-blend)+(int64_t)digR*blend)/127);
   }
   int32_t mono=(int32_t)(((int64_t)dryL+dryR)/2);
   int32_t wet=rn_lpf_process(&s->lowpass,p,rn_granular_process(&s->granular,p,rn_four_fx_process(&s->four_fx,p,rn_res_process(&s->resonance,p,rn_mm_process(&s->memory,p,mono)))));
   int64_t delta=(int64_t)wet-mono;
   s->acoustic_stems[p][j]=(int32_t)((int64_t)dryL+delta>8388607ll?8388607ll:(int64_t)dryL+delta< -8388608ll?-8388608ll:(int64_t)dryL+delta);
   s->acoustic_stems[p][j+1]=(int32_t)((int64_t)dryR+delta>8388607ll?8388607ll:(int64_t)dryR+delta< -8388608ll?-8388608ll:(int64_t)dryR+delta);
  }
 }
}

int rn_dc_finalize(rn_v12_dsp *s,int32_t *out,unsigned frames){
 if(!s||!out||frames!=128u)return -1;
 /* CPU0 alone owns global FX and preserves exact interleaved per-sample order. */
 for(unsigned j=0;j<256u;j+=2){
  int64_t mixL=0,mixR=0;
  int32_t send_input[4][2];
  for(unsigned p=0;p<4u;p++){
   send_input[p][0]=s->acoustic_stems[p][j];
   send_input[p][1]=s->acoustic_stems[p][j+1];
   mixL+=send_input[p][0];mixR+=send_input[p][1];
  }
  if(mixL>8388607ll)mixL=8388607ll;
  if(mixL< -8388608ll)mixL=-8388608ll;
  if(mixR>8388607ll)mixR=8388607ll;
  if(mixR< -8388608ll)mixR=-8388608ll;
  int32_t send_l=(int32_t)mixL,send_r=(int32_t)mixR;
  rn_sends_render(&s->sends,(const int32_t (*)[2])send_input,&send_l,&send_r);
  out[j]=send_l;out[j+1]=send_r;
 }
 s->acoustic.blocks++;
 return 0;
}

void rn_dc_cpu1_part34(void *arg){
 rn_dc_job *h=(rn_dc_job *)arg;
 if(h&&h->engine&&h->frames==128u)rn_dc_render_range(h,2,4);
}
