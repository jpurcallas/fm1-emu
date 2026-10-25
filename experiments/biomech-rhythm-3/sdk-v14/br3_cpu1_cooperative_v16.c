/* BIOMECH RHYTHM 3 — cooperative CPU1 service bridge, EMULATOR LAB ONLY.
 * Never boot, reset, hold or steal CPU1: stock SDK owns the worker.
 * The original SDK service MUST be executed by the verified post-link wrapper
 * before this function (integration is separately audited).
 * No modification of the six-track DSP, sequencer or effects.
 */
#include <stdint.h>
#include "biomech.h"
#include "br3_blackbox.h"
#ifndef BR3_EMULATOR_LAB
#error "SDK cooperative CPU1 bridge is EMULATOR LAB ONLY"
#endif
#ifndef BR3_SDK_CPU1_PROBE_SERIAL
#error "BIOMECH V14 bridge requires diagnostic serial fallback when unattached"
#endif
#define BR3_COOP_ALIVE 0xC103C003u
#define BR3_COOP_MAGIC 0xB330C016u
#define BR3_COOP_WAIT_BOUND 800000u
#define BR3_COOP_BARRIER() __asm__ volatile("csync" ::: "memory")
typedef struct __attribute__((aligned(64))) {
 volatile uint32_t magic,seq,done,alive;
 volatile uintptr_t fn,arg;
 volatile uint32_t accepted,completed,fault,timeouts;
 uint32_t reserved[6];
} BR3CoopMailbox;
BR3CoopMailbox br3_coop_mailbox;
volatile uintptr_t br3_coop_hook_anchor;
volatile uint32_t br3_coop_ready_seen;
static uint32_t br3_coop_waiting;
static void BR_RAMCODE br3_cpu1_dispatch_coop(void *arg);
static void BR_RAMCODE br3_cpu1_dispatch_coop(void *arg){
 (void)arg;
 BR3_COOP_BARRIER();
 if(br3_coop_mailbox.magic!=BR3_COOP_MAGIC){
   br3_coop_mailbox.fault=1u;return;
 }
 uint32_t seq=br3_coop_mailbox.seq;
 if(seq==br3_coop_mailbox.done)return;
 uintptr_t fn=br3_coop_mailbox.fn,job_arg=br3_coop_mailbox.arg;
 /* The C99 musical scheduler owns only its offered job; never execute an
  * arbitrary function from a corrupted mailbox. */
 if(!fn||!job_arg){br3_coop_mailbox.fault=2u;return;}
 ((void (*)(void*))fn)((void*)job_arg);
 BR3_COOP_BARRIER();
 br3_coop_mailbox.done=seq;
 br3_coop_mailbox.completed++;
 BR3_COOP_BARRIER();
}
/* Called ONLY by a future audited wrapper AFTER stock SDK CPU1 service.
 * Source is deliberately NOT wired to arbitrary SDK addresses yet. */
void BR_RAMCODE br3_coop_cpu1_service_after_sdk(void){
 br3_coop_mailbox.alive=BR3_COOP_ALIVE;
 BR3_COOP_BARRIER();
 br3_cpu1_dispatch_coop(0);
}
int br3_cpu1_exclusive_ready(void){
 /* Historical name required by v04 SDK staging; this does NOT assert
  * exclusive ownership. CPU1 is always SDK-owned. */
 return 0;
}
static int br3_coop_submit(void (*fn)(void*),void *arg,uint32_t frames){
 if(!br3_coop_ready_seen||br3_coop_mailbox.alive!=BR3_COOP_ALIVE||
    br3_coop_mailbox.fault||br3_coop_waiting||!fn||!arg||
    frames==0||frames>BR3_SLICE_FRAMES)return 0;
 BR3_COOP_BARRIER();
 if(br3_coop_mailbox.seq!=br3_coop_mailbox.done)return 0;
 unsigned seq=br3_coop_mailbox.seq+1u;if(!seq)seq=1u;
 br3_coop_mailbox.fn=(uintptr_t)fn;
 br3_coop_mailbox.arg=(uintptr_t)arg;
 BR3_COOP_BARRIER();
 br3_coop_mailbox.seq=seq;
 br3_coop_mailbox.accepted++;
 br3_coop_waiting=seq;
 BR3_COOP_BARRIER();
 return 1;
}
static int br3_coop_wait(void){
 uint32_t seq=br3_coop_waiting;
 if(!seq)return 0;
 for(uint32_t i=0;i<BR3_COOP_WAIT_BOUND;i++){
   BR3_COOP_BARRIER();
   if(br3_coop_mailbox.done==seq){br3_coop_waiting=0;return 1;}
   if(br3_coop_mailbox.fault)break;
 }
 /* Fail CLOSED: no indication that remote worker is quiescent, so do not
  * claim completion. Caller must suppress DMA and NOT serial-rerender. */
 br3_coop_mailbox.timeouts++;
 br3_coop_mailbox.fault=3u;
 BR3_COOP_BARRIER();
 return 0;
}
void br3_coop_init(void){
 br3_coop_mailbox.magic=BR3_COOP_MAGIC;
 br3_coop_hook_anchor=(uintptr_t)&br3_coop_cpu1_service_after_sdk;
}
void br3_coop_attach_if_alive(void){
 if(br3_coop_ready_seen||br3_coop_mailbox.alive!=BR3_COOP_ALIVE)return;
 if(br3_coop_mailbox.fault||br3_coop_mailbox.seq!=br3_coop_mailbox.done)return;
 BR3Executor e={br3_coop_submit,br3_coop_wait};
 br3_set_executor(&e);
 br3_coop_ready_seen=1;
}
