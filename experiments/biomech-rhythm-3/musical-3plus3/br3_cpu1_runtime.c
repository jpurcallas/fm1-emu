/* BIOMECH RHYTHM 3: direct CPU1 job executor for the PI32v2 FM-1.
 * Source-only experimental bridge. Requires that the application owns CPU1:
 * the stock SDK's CPU1 scheduler must NOT simultaneously control this core.
 * Uses proven startup/entry sequence from BR3 native self-test.
 * No change to the six-voice DSP or sequencer.
 */
#include <stdint.h>
#include <stddef.h>
#include "biomech.h"
#include "br3_blackbox.h"
#if !defined(BR3_DUAL_CORE) || !defined(__GCC_PI32V2__) && !defined(BR3_PI32V2)
#error "Build this file only for BIOMECH3 native PI32v2 + BR3_DUAL_CORE"
#endif
#define R32(addr) (*(volatile uint32_t*)(uintptr_t)(addr))
#define C1_CON 0x01EEE004u
#define C1_CLK 0x00010008u
#define C1_ENTRY 0x01C7FFF8u
#define C1_IRQ 0x01EEF300u
#define TMR4 0x00010804u
#define BUS_SYNC() __asm__ volatile("csync" ::: "memory")
#define BR3_MAGIC 0x42523333u
#define BR3_ALIVE 0xC133A11Fu
#define BR3_DONE 0xB330C0DEu
#define BR3_TIMER_HZ 24000000u /* FM-1 TIMER4 */
#define BR3_BOOT_TICKS (24u*20000u) /* 20 ms */
#ifndef BR3_SLICE_FRAMES
#define BR3_SLICE_FRAMES 32u /* production reference; must match synth build */
#endif
#if BR3_SLICE_FRAMES > 32u && !defined(BR3_LARGE_SLICE_LAB)
#error "Large slice size is a native diagnostics-only experiment"
#endif
/* Optional PERFORMANCE LAB knob. Default 1 retains every BLACK BOX event.
 * When >1, counters remain exact and faults are always logged; ordinary
 * per-job tracing is sampled so we can measure instrumentation overhead. */
#ifndef BR3_BB_SAMPLE_RATE
#define BR3_BB_SAMPLE_RATE 1u
#endif
#if BR3_BB_SAMPLE_RATE < 1 || BR3_BB_SAMPLE_RATE > 256
#error "BR3_BB_SAMPLE_RATE must be 1..256"
#endif
#define BR3_TRACE_JOB(seq) (((seq) % BR3_BB_SAMPLE_RATE)==0u)
typedef void (*br3_job)(void*);
typedef struct __attribute__((aligned(64))) {
  volatile uint32_t sequence;
  volatile uint32_t opcode;
  volatile uintptr_t arg;
  volatile uintptr_t fn;
  volatile uint32_t checksum;
  uint32_t pad[11];
} BR3Request;
typedef struct __attribute__((aligned(64))) {
  volatile uint32_t alive;
  volatile uint32_t done;
  volatile uint32_t rejected;
  volatile uint32_t last_bad_seq;
  uint32_t pad[12];
} BR3Reply;
typedef struct __attribute__((aligned(64))) {
  BR3Request request;
  BR3Reply reply;
} BR3Mailbox;
/* Guest PI32v2 pointers are 32-bit; on a 64-bit HOST this file is syntax
   checked only, not used to emulate hardware mailbox layout. */
#if UINTPTR_MAX == UINT32_MAX
typedef char br3_request_cache_line_check[(sizeof(BR3Request)==64)?1:-1];
typedef char br3_reply_cache_line_check[(sizeof(BR3Reply)==64)?1:-1];
#endif
BR3Mailbox br3_mailbox __attribute__((aligned(64)));
volatile uint32_t br3_cpu1_stage;
volatile uint32_t br3_cpu0_stage;
volatile uint32_t br3_completed_jobs;
volatile uint32_t br3_timeouts;
volatile uint32_t br3_fallback_jobs;
volatile uint32_t br3_cache_faults;
static uint32_t br3_enabled;
static uint32_t br3_inflight;
static uint32_t br3_saved_clock;
static uint32_t br3_job_start_tick,br3_job_deadline_ticks;
extern void br3_cpu1_entry(void);
static uint32_t br3_check(uint32_t seq,uint32_t opcode,uintptr_t fn,uintptr_t arg){
  return BR3_MAGIC^(seq*0x9e3779b1u)^(opcode*0x85ebca6bu)^(uint32_t)fn^(uint32_t)arg;
}
static void br3_hold(void){
  R32(C1_CON)|=2u;R32(C1_CON)&=~8u;
  BUS_SYNC();br3_enabled=0;
}
void __attribute__((noreturn,section(".br3_cpu1_text"))) br3_cpu1_main(void){
  uint32_t last=0;
  br3_cpu1_stage=0xC1000001u;
  br3_bb_event(1,BR3_BB_CPU1_ALIVE,R32(TMR4),0,(uint32_t)(uintptr_t)&br3_cpu1_main,0);
  br3_mailbox.reply.alive=BR3_ALIVE;
  BUS_SYNC();
  for(;;){
    uint32_t seq=br3_mailbox.request.sequence;
    BUS_SYNC();
    if(seq==last)continue;
    uint32_t opcode=br3_mailbox.request.opcode;
    uintptr_t arg=br3_mailbox.request.arg;
    uintptr_t fn=br3_mailbox.request.fn;
    uint32_t check=br3_mailbox.request.checksum;
    if(seq!=last+1u||opcode!=1u||!fn||check!=br3_check(seq,opcode,fn,arg)){
      br3_mailbox.reply.last_bad_seq=seq;
      br3_mailbox.reply.rejected++;
      br3_cpu1_stage=0xC1BAD001u;
      br3_bb_event(1,BR3_BB_BAD_JOB,R32(TMR4),seq,check,fn);
      BUS_SYNC();
      /* A bad message cannot be acknowledged or executed as valid work. */
      last=seq;
      continue;
    }
    if(BR3_TRACE_JOB(seq)) br3_bb_event(1,BR3_BB_JOB_ACCEPT,R32(TMR4),seq,(uint32_t)fn,(uint32_t)arg);
    ((br3_job)fn)((void*)arg);
    BUS_SYNC();
    br3_mailbox.reply.done=seq;
    br3_cpu1_stage=BR3_DONE;
    if(BR3_TRACE_JOB(seq)) br3_bb_event(1,BR3_BB_JOB_DONE,R32(TMR4),seq,(uint32_t)fn,0);
    BUS_SYNC();
    last=seq;
  }
}
/* Must run before any other SDK code has booted CPU1, or after explicitly
   quiescing the SDK worker in a separately linked application. */
int br3_cpu1_start(void){
  if(br3_enabled)return 1;
  /* SDK V14 (or another firmware service) may already own this core.
   * The standalone CPU1 proof used a clean boot, so NEVER pulse HOLD,
   * reset the CPU1 IRQs or write ENTRY when RUN/HOLD or the release clock
   * is already asserted by an unknown owner. This is a refusal gate, not
   * proof that a nominally idle CPU1 can be reserved inside V14: a
   * separately ordered early-boot handoff is still mandatory. */
  const uint32_t prior_con=R32(C1_CON), prior_clk=R32(C1_CLK);
  if ((prior_con & 0x0au)!=0u || (prior_clk & 8u)!=0u) {
    br3_bb_init(0x0003E002u);
    br3_blackbox.last_error=0xB330F103u;
    br3_bb_event(0,BR3_BB_OWNER_UNCLAIMED,R32(TMR4),0,prior_con,prior_clk);
    return 0;
  }
  br3_hold();
  br3_bb_init(0x00030001u);
  br3_bb_event(0,BR3_BB_BOOT,R32(TMR4),0,(uint32_t)(uintptr_t)&br3_cpu1_entry,0);
  br3_mailbox.request.sequence=0;
  br3_mailbox.reply.done=0;
  br3_mailbox.reply.alive=0;
  br3_mailbox.reply.rejected=0;
  br3_cpu0_stage=0xC0000001u;
  br3_cpu1_stage=0;
  for(unsigned i=0;i<32;i++)R32(C1_IRQ+4u*i)=0;
  R32(C1_ENTRY)=(uint32_t)(uintptr_t)&br3_cpu1_entry;
  br3_saved_clock=R32(C1_CLK);
  R32(C1_CLK)=br3_saved_clock|8u;
  BUS_SYNC();
  R32(C1_CON)|=8u;R32(C1_CON)&=~2u;
  uint32_t started=R32(TMR4);
  while(br3_mailbox.reply.alive!=BR3_ALIVE && (uint32_t)(R32(TMR4)-started)<BR3_BOOT_TICKS)BUS_SYNC();
  R32(C1_CLK)=br3_saved_clock;
  if(br3_mailbox.reply.alive!=BR3_ALIVE){br3_hold();return 0;}
  br3_enabled=1;
  br3_cpu0_stage=0xC0000002u;
  br3_inflight=0;
  return 1;
}
static int br3_submit(br3_job fn,void *arg,uint32_t frames){
  if(!br3_enabled||br3_inflight||!fn || frames==0 || frames>BR3_SLICE_FRAMES)return 0;
  /* The whole job must fit in its actual 44.1-kHz sample-time window;
     85%% guard preserves time for final mix/FX and DMA after CPU1 finishes. */
  br3_job_deadline_ticks=(uint32_t)(((uint64_t)frames*BR3_TIMER_HZ*85u)/(44100u*100u));
  br3_job_start_tick=R32(TMR4);
  uint32_t seq=br3_mailbox.request.sequence+1u;
  br3_mailbox.request.opcode=1u;
  br3_mailbox.request.fn=(uintptr_t)fn;
  br3_mailbox.request.arg=(uintptr_t)arg;
  br3_mailbox.request.checksum=br3_check(seq,1u,(uintptr_t)fn,(uintptr_t)arg);
  BUS_SYNC();
  br3_mailbox.request.sequence=seq;
  BUS_SYNC();
  br3_inflight=seq;
  br3_blackbox.jobs_sent++;
  if(BR3_TRACE_JOB(seq)) br3_bb_event(0,BR3_BB_JOB_SEND,R32(TMR4),seq,(uint32_t)(uintptr_t)fn,(uint32_t)(uintptr_t)arg);
  return 1;
}
/* Returns only AFTER CPU1 is known to be done OR is forcibly held.
 * Caller may then rerender from its unmodified shadow on CPU0. */
static int br3_wait(void){
  if(!br3_inflight)return 0;
  uint32_t seq=br3_inflight;
  while(br3_mailbox.reply.done!=seq && br3_mailbox.reply.rejected==0u &&
      (uint32_t)(R32(TMR4)-br3_job_start_tick)<br3_job_deadline_ticks)BUS_SYNC();
  int done=br3_mailbox.reply.done==seq && br3_mailbox.reply.rejected==0;
  uint32_t took=(uint32_t)(R32(TMR4)-br3_job_start_tick);
  br3_blackbox.last_wait_ticks=took;
  if(took>br3_blackbox.max_wait_ticks)br3_blackbox.max_wait_ticks=took;
  if(!done){
    br3_timeouts++;
    br3_blackbox.job_timeouts++;
    br3_bb_event(0,br3_mailbox.reply.rejected?BR3_BB_BAD_JOB:BR3_BB_TIMEOUT,R32(TMR4),seq,took,br3_mailbox.reply.rejected);
    if(br3_mailbox.reply.rejected)br3_cache_faults++;
    /* Halt before caller touches CPU1's scratch; never race the fallback. */
    br3_hold();
    br3_fallback_jobs++;
    br3_blackbox.fallback_count++;
    br3_bb_event(0,BR3_BB_FALLBACK,R32(TMR4),seq,took,0);
  }else{
    br3_completed_jobs++;
    br3_blackbox.jobs_done++;
    if(BR3_TRACE_JOB(seq)) br3_bb_event(0,BR3_BB_WAIT_OK,R32(TMR4),seq,took,0);
    BUS_SYNC();
  }
  br3_inflight=0;
  return done;
}
void br3_cpu1_attach(void){
  BR3Executor ops={br3_submit,br3_wait};
  br3_set_executor(&ops);
}
void br3_cpu1_detach(void){
  if(br3_inflight)(void)br3_wait();
  /* Not owner? Do not halt an SDK-owned CPU1 while detaching an inert
     dispatcher. This was possible in the older native experiment. */
  if(br3_enabled) br3_hold();
  br3_set_executor(NULL);
}
