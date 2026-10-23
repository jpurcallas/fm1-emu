/* REminiSCENT 2 LAB CPU1 OWN BOOT -- EXPERIMENT ONLY, DO NOT FLASH.
 * Distinct native CPU1 handler, no SDK job service or sound-engine substitution.
 * Builds into PI32v2 .o; the SDK CPU1 start must be disabled BEFORE linking.
 * Registers verified against published X0X/Clipper hardware research.
 */
#include <stdint.h>
#include "rem2_trace.h"

#define R2_REG32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define R2_C1_CON R2_REG32(0x01EEE004u)
#define R2_C1_CLOCK R2_REG32(0x00010008u)
#define R2_TIMER4 R2_REG32(0x00010804u)
#define R2_ENTRY_WORD R2_REG32(0x01C7FFF8u)
#define R2_C1_IRQ(n) R2_REG32(0x01EEF300u+4u*(n))
#define R2_MAGIC 0x52324331u /* R2C1 */
#define R2_ALIVE 0x414C4956u
#define R2_KIND_HEARTBEAT 1u
#define R2_KIND_CHECKSUM 2u
#define R2_KIND_STALL_TEST 3u

/* 64-byte ownership-separated mailbox, CPU0 publishes req.seq last,
 * CPU1 publishes rep.done last. Validate coherency on emulated PI32v2.
 */
struct __attribute__((aligned(64))) r2_request {
 volatile uint32_t seq, kind, arg0, arg1, crc;
 uint32_t padding[11];
};
struct __attribute__((aligned(64))) r2_reply {
 volatile uint32_t alive, done, result, error, rejected;
 uint32_t padding[11];
};
struct __attribute__((aligned(64))) r2_shared {
 struct r2_request req;
 struct r2_reply rep;
};
static struct r2_shared r2_mailbox;
static rem2_blackbox r2_blackbox __attribute__((aligned(64)));
extern void r2_cpu1_entry(void);

/* No LIBC, no RTOS: fixed mixing iterations and permitted task IDs only. */
static uint32_t r2_hash(uint32_t x) {
 x^=x>>16; x*=0x7feb352du; x^=x>>15; x*=0x846ca68bu;
 return x^(x>>16);
}
static uint32_t r2_check(uint32_t seq,uint32_t kind,uint32_t a,uint32_t b) {
 return r2_hash(0x52324c42u ^ (seq*0x9e3779b9u) ^ (kind<<17) ^ (a*0x85ebca6bu) ^ b);
}
static uint32_t r2_work(uint32_t a,uint32_t b) {
 uint32_t v=a^(b*33u);
 for(uint32_t i=0;i<64u;i++) v=r2_hash(v+0x1234abcdu+i);
 return v;
}
static void __attribute__((section(".rem2_c1_ram"),noinline,used))
 r2_trace_event(uint32_t core,uint32_t event,uint32_t job,uint32_t reason) {
 rem2_fields f={0};
 f.cycle=R2_TIMER4; f.job=job; f.event=event; f.extra=reason;
 rem2_emit(&r2_blackbox,core,f);
}
void __attribute__((section(".rem2_c1_ram"),noreturn,used))
 r2_cpu1_main(void) {
 uint32_t seen=r2_mailbox.rep.done;
 r2_mailbox.rep.alive=R2_ALIVE;
 rem2_barrier();
 r2_trace_event(1,REM2_C1_ALIVE,0,0);
 for (;;) {
   uint32_t seq=r2_mailbox.req.seq;
   rem2_barrier();
   if(seq==seen)continue;
   uint32_t kind=r2_mailbox.req.kind,a=r2_mailbox.req.arg0,b=r2_mailbox.req.arg1;
   uint32_t crc=r2_mailbox.req.crc;
   uint32_t reason=0u;
   if(seq!=seen+1u)reason=1u;
   else if(crc!=r2_check(seq,kind,a,b))reason=2u;
   else if(kind<R2_KIND_HEARTBEAT||kind>R2_KIND_STALL_TEST)reason=3u;
   if(reason){
     r2_mailbox.rep.error=reason;
     r2_mailbox.rep.rejected++;
     r2_trace_event(1,REM2_BAD_MAILBOX,seq,reason);
     /* The same bad request is NOT executed or acknowledged. */
     for(;;)rem2_barrier();
   }
   r2_trace_event(1,REM2_JOB_BEGIN,seq,kind);
   if(kind==R2_KIND_STALL_TEST){for(;;)rem2_barrier();}
   uint32_t result=(kind==R2_KIND_HEARTBEAT)?R2_MAGIC:r2_work(a,b);
   r2_mailbox.rep.result=result;
   r2_trace_event(1,REM2_JOB_END,seq,result);
   rem2_barrier();
   r2_mailbox.rep.done=seq;
   rem2_barrier();
   seen=seq;
 }
}

void r2_cpu1_hold(void) {
 R2_C1_CON|=2u;
 R2_C1_CON&=~8u;
 rem2_barrier();
}
static int r2_wait_for(uint32_t *value,uint32_t expected,uint32_t ticks) {
 uint32_t start=R2_TIMER4;
 while(*value!=expected) {
   rem2_barrier();
   if((uint32_t)(R2_TIMER4-start)>ticks)return -1;
 }
 return 0;
}
/* PRECONDITIONS: SDK ownership of CPU1 disabled, guards opened for ROM,
 * writable entry word at top RAM, RAM code copied, C1 power ready.
 * No modifications to original firmwares. This is not wired to v3.0.23 yet.
 */
int r2_cpu1_boot_native(const char *version,const char *sha) {
 r2_cpu1_hold();
 rem2_init(&r2_blackbox,version,sha);
 r2_mailbox.req.seq=0;
 r2_mailbox.rep.done=0;
 r2_mailbox.rep.alive=0;
 r2_mailbox.rep.error=0;
 r2_mailbox.rep.rejected=0;
 r2_trace_event(0,REM2_BOOT0,0,0);
 for(unsigned i=0;i<32;i++)R2_C1_IRQ(i)=0u;
 R2_ENTRY_WORD=(uint32_t)(uintptr_t)&r2_cpu1_entry;
 uint32_t saved=R2_C1_CLOCK;
 R2_C1_CLOCK=saved|8u;
 rem2_barrier();
 R2_C1_CON|=8u;
 R2_C1_CON&=~2u;
 int ok=r2_wait_for((uint32_t*)&r2_mailbox.rep.alive,R2_ALIVE,480000u);
 R2_C1_CLOCK=saved;
 if(ok){r2_trace_event(0,REM2_TIMEOUT,0,1);r2_cpu1_hold();return -1;}
 r2_trace_event(0,REM2_C1_ALIVE,0,0);
 return 0;
}
int r2_cpu1_call(uint32_t kind,uint32_t a,uint32_t b,uint32_t deadline_ticks) {
 uint32_t n=r2_mailbox.req.seq;
 if(n!=r2_mailbox.rep.done)return -2;
 if(kind<R2_KIND_HEARTBEAT||kind>R2_KIND_STALL_TEST)return -3;
 n++;
 r2_mailbox.req.kind=kind;
 r2_mailbox.req.arg0=a;r2_mailbox.req.arg1=b;
 r2_mailbox.req.crc=r2_check(n,kind,a,b);
 rem2_barrier();
 r2_mailbox.req.seq=n;
 rem2_barrier();
 uint32_t start=R2_TIMER4;
 r2_trace_event(0,REM2_JOB_ISSUE,n,kind);
 int timeout=0;
 for(;;) {
   rem2_barrier();
   if(r2_mailbox.rep.error){timeout=2;break;}
   if(r2_mailbox.rep.done==n)break;
   if((uint32_t)(R2_TIMER4-start)>deadline_ticks){timeout=1;break;}
 }
 uint32_t elapsed=R2_TIMER4-start;
 if(timeout){
   r2_trace_event(0,REM2_TIMEOUT,n,timeout);
   r2_cpu1_hold(); /* No touching CPU1 buffers until the hold. */
   return -1;
 }
 rem2_fields f={0};f.cycle=R2_TIMER4;f.job=n;f.event=REM2_JOB_JOIN;f.wait_ticks=elapsed;
 rem2_emit(&r2_blackbox,0,f);
 return 0;
}
/* External emulator debugger must locate these symbols and dump RAM while
 * frozen. PC/SP and DMA fields are populated only when target hooks exist.
 */
void *r2_blackbox_ptr(void){return &r2_blackbox;}
unsigned r2_blackbox_size(void){return sizeof(r2_blackbox);}
