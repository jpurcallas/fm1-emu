#include "rn_v12_cpu1_guard.h"
#include <string.h>
static int healthy(rn_dc_cpu1_guard *g){
 return g&&g->leased&&!g->poisoned&&
        g->platform.owns_cpu1(g->platform.ctx)&&
        g->platform.memory_coherent(g->platform.ctx);
}
static void poison(rn_dc_cpu1_guard *g){
 if(!g->poisoned){g->poisoned=1;g->poisoned_count++;}
}
int rn_dc_cpu1_guard_arm(rn_dc_cpu1_guard *g,const rn_dc_cpu1_platform *p,uint32_t deadline_ticks){
 if(!g||!p||!p->owns_cpu1||!p->memory_coherent||!p->send||
    !p->wait_complete||!p->quiesced||!deadline_ticks)return -1;
 if(!p->owns_cpu1(p->ctx)||!p->memory_coherent(p->ctx))return -2;
 memset(g,0,sizeof(*g));g->platform=*p;g->deadline_ticks=deadline_ticks;g->leased=1;
 return 0;
}
static int guard_ready(void *opaque){
 rn_dc_cpu1_guard *g=opaque;
 if(!g)return 0;
 if(!healthy(g)||g->inflight){
  if(g->leased&&!g->poisoned&&
     (!g->platform.owns_cpu1(g->platform.ctx)||
      !g->platform.memory_coherent(g->platform.ctx)))poison(g);
  return 0;
 }
 return 1;
}
static int guard_submit(void *opaque,void(*fn)(void*),void *arg,unsigned frames){
 rn_dc_cpu1_guard *g=opaque;
 if(!g)return 0;
 if(!healthy(g)||g->inflight||fn!=rn_dc_cpu1_part34||!arg||frames!=128u){
  if(g->leased&&!g->poisoned&&
     (!g->platform.owns_cpu1(g->platform.ctx)||
      !g->platform.memory_coherent(g->platform.ctx)))poison(g);
  g->refused++;return 0;
 }
 uint32_t seq=g->next_sequence+1u;
 if(seq==0u)seq=1u;
 if(!g->platform.send(g->platform.ctx,fn,arg,frames,seq)){
  /* send returning false MUST guarantee no remote worker can write. */
  g->refused++;return 0;
 }
 g->next_sequence=seq;g->inflight=seq;g->accepted++;return 1;
}
static int guard_wait(void *opaque){
 rn_dc_cpu1_guard *g=opaque;
 if(!g||!g->inflight)return 0;
 uint32_t seq=g->inflight;
 int ok=g->platform.wait_complete(g->platform.ctx,seq,g->deadline_ticks);
 if(!ok||!g->platform.owns_cpu1(g->platform.ctx)||
    !g->platform.memory_coherent(g->platform.ctx)){
  /* Keep in-flight marked: CPU1 may still write to job/DSP. */
  poison(g);return 0;
 }
 g->inflight=0;g->completed++;return 1;
}
rn_dc_executor rn_dc_cpu1_guard_executor(rn_dc_cpu1_guard *g){
 rn_dc_executor e={g,guard_submit,guard_wait,guard_ready};return e;
}
int rn_dc_cpu1_guard_rearm(rn_dc_cpu1_guard *g){
 if(!g||!g->leased||!g->poisoned)return -1;
 if(!g->platform.quiesced(g->platform.ctx))return -2;
 if(!g->platform.owns_cpu1(g->platform.ctx)||
    !g->platform.memory_coherent(g->platform.ctx))return -3;
 g->poisoned=0;g->inflight=0;return 0;
}
