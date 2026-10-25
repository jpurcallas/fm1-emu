/* BIOMECH 3 v0.16 / Yeti Fingers. SDK-cooperative CPU1 experiment.
 * NEVER INSTALL: post-link SDK callsite patch is unsupported on physical FM-1.
 * Keeps the SDK CPU1 service alive before executing BIOMECH 3's 3+3 job.
 * Original BIOMECH synthesis, all FX, sequencer and source files unchanged.
 */
#include <stdint.h>
#include "biomech.h"
#include "ram_attr.h"
#define BR3_COOP_ALIVE 0xB316C001u
#define BR3_COOP_SENTINEL 0xBA5EBA11u
#define BR3_COOP_LIMIT 800000u
#define BR3_COOP_CHECK 0xB316A008u
typedef void(*BR3Job)(void*);
typedef struct __attribute__((aligned(64))) {
  volatile uint32_t seq,done,alive,fault;
  volatile uintptr_t fn,arg;
  volatile uint32_t frames,checksum,accepted,completed,timeouts,spins;
  uint32_t reserved[4];
} BR3CoopMailbox;
BR3CoopMailbox br3_coop_mailbox __attribute__((aligned(64)));
/* Patched with the OWN linked SDK original worker address by gated post-link
 * script. Not an arbitrary device address or a borrowed REM constant. */
volatile uint32_t br3_sdk_original_worker_addr __attribute__((used,section(".ram0_data"))) = BR3_COOP_SENTINEL;
static inline void coop_barrier(void){__asm__ volatile("csync" ::: "memory");}
static uint32_t checksum(uint32_t s,uint32_t n,uintptr_t f,uintptr_t a){
 return BR3_COOP_CHECK^(s*0x9e3779b1u)^(n*0x85ebca6bu)^(uint32_t)f^(uint32_t)a;
}
void BR_RAMCODE br3_coop_service_wrapper(void){
 uint32_t sdk_worker=br3_sdk_original_worker_addr;
 if(sdk_worker==BR3_COOP_SENTINEL||!sdk_worker){br3_coop_mailbox.fault=1;return;}
 /* Preserve the original mandatory SDK CPU1 service FIRST, then music. */
 ((void(*)(void))(uintptr_t)sdk_worker)();
 BR3CoopMailbox *m=&br3_coop_mailbox;
 m->alive=BR3_COOP_ALIVE;
 coop_barrier();
 uint32_t seq=m->seq;
 if(seq==m->done)return;
 uint32_t n=m->frames;uintptr_t fn=m->fn,arg=m->arg;
 if(!fn||!arg||n==0u||n>32u||m->checksum!=checksum(seq,n,fn,arg)){
   m->fault=2;coop_barrier();m->done=seq;return;
 }
 ((BR3Job)fn)((void*)arg);
 coop_barrier();m->completed++;m->done=seq;
 coop_barrier();
}
/* Explicit address-taken reference keeps the uncalled wrapper through LTO.
 * The post-link patch changes exactly one SDK call instruction in RAM image. */
volatile uintptr_t br3_coop_link_anchor __attribute__((used,section(".ram0_data")))=(uintptr_t)&br3_coop_service_wrapper;
static uint32_t waiting_seq;
static int coop_submit(void(*fn)(void*),void*arg,uint32_t frames){
 BR3CoopMailbox *m=&br3_coop_mailbox;
 if(!fn||!arg||frames==0u||frames>32u||m->fault||m->alive!=BR3_COOP_ALIVE)return 0;
 coop_barrier();if(m->seq!=m->done||waiting_seq)return 0;
 uint32_t seq=m->seq+1u;if(!seq)seq=1u;
 m->fn=(uintptr_t)fn;m->arg=(uintptr_t)arg;m->frames=frames;
 m->checksum=checksum(seq,frames,(uintptr_t)fn,(uintptr_t)arg);
 coop_barrier();m->seq=seq;m->accepted++;waiting_seq=seq;
 coop_barrier();return 1;
}
static int coop_wait(void){
 BR3CoopMailbox *m=&br3_coop_mailbox;
 uint32_t seq=waiting_seq;
 if(!seq)return 0;
 uint32_t spins=0;
 while(m->done!=seq){
    coop_barrier();
    if(spins<BR3_COOP_LIMIT){++spins;continue;}
    /* SDK worker may still write the segment. Never let the engine's
     * fallback race CPU1: after watchdog expiration wait for ACK instead
     * of returning false. Lab-only hang protection; no hardware flashing. */
    m->timeouts++;m->fault=3;coop_barrier();
    while(m->done!=seq)coop_barrier();
    break;
 }
 m->spins+=spins;waiting_seq=0;coop_barrier();
 return m->fault==0;
}
void br3_coop_register(void){
 BR3Executor ops={coop_submit,coop_wait};
 br3_set_executor(&ops);
}
uint32_t br3_coop_stat(unsigned n){
 BR3CoopMailbox *m=&br3_coop_mailbox;
 switch(n){
 case 0:return m->alive;case 1:return m->accepted;
 case 2:return m->completed;case 3:return m->fault;
 case 4:return m->timeouts;default:return m->spins;
 }
}
