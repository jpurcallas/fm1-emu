/* REminiSCENT 2 LAB -- black box version 1. C99, no heap, no I/O, no SDK.
 * Research-only: does not hook into the v3.0.23 firmware yet.
 * Single writer per core, external passive reader of shared RAM.
 * SPDX-License-Identifier: MIT -- original diagnostic tool; no X0X code copied.
 */
#ifndef REM2_TRACE_H
#define REM2_TRACE_H
#include <stdint.h>
#include <stddef.h>
#define REM2_TRACE_MAGIC 0x52325442u /* R2TB */
#define REM2_TRACE_SCHEMA 1u
#ifndef REM2_TRACE_SLOTS
#define REM2_TRACE_SLOTS 32u
#endif
#define REM2_TRACE_CORE_COUNT 2u

enum rem2_event {
 REM2_BOOT0=1, REM2_C1_ENTRY, REM2_C1_ALIVE, REM2_JOB_ISSUE,
 REM2_JOB_BEGIN, REM2_JOB_END, REM2_JOB_JOIN, REM2_DMA_COPY,
 REM2_LAST_GOOD, REM2_BAD_MAILBOX, REM2_TIMEOUT, REM2_FAULT,
 REM2_PC_GUARD, REM2_PARKED, REM2_REBOOT, REM2_DMA_LATE
};

/* Fixed 64-byte record, no allocations or printf on the audio path. */
typedef struct rem2_record {
 volatile uint32_t commit;  /* odd: in progress, even: complete */
 uint32_t cycle;             /* timer or emulator cycle, host tests use us */
 uint32_t block;
 uint32_t job;
 uint32_t event;
 uint32_t pc;                /* sampled PC if available, else 0 */
 uint32_t sp;                /* sampled SP if available, else 0 */
 uint32_t wait_ticks;
 uint32_t dma_half;
 uint32_t dma_deadline;
 uint32_t dma_copy_tick;
 uint32_t audio_late;
 uint32_t last_valid_block;
 uint32_t fault_reason;      /* hardware trap flags if known */
 uint32_t payload_crc;
 uint32_t extra;             /* caller-defined state, such as mailbox check */
} rem2_record;
typedef char rem2_record_must_be_64_bytes[(sizeof(rem2_record)==64)?1:-1];

typedef struct rem2_ring {
 volatile uint32_t head;    /* single writer only */
 volatile uint32_t overflow;
 uint32_t pad[14];          /* next ring begins on a cacheline */
 rem2_record events[REM2_TRACE_SLOTS];
} rem2_ring;

typedef struct rem2_blackbox {
 uint32_t magic;
 uint32_t schema;
 uint32_t bytes;
 uint32_t enabled;
 char firmware[32];
 char build_sha256[65];
 uint8_t pad[15];
 rem2_ring cpu[REM2_TRACE_CORE_COUNT];
} rem2_blackbox;

typedef struct rem2_fields {
 uint32_t cycle, block, job, event, pc, sp, wait_ticks;
 uint32_t dma_half, dma_deadline, dma_copy_tick, audio_late;
 uint32_t last_valid_block, fault_reason, extra;
} rem2_fields;

static inline __attribute__((always_inline)) void rem2_barrier(void) {
#if defined(__GCC_PI32V2__)
 __asm__ volatile("csync" ::: "memory");
#elif defined(__GNUC__) || defined(__clang__)
 __sync_synchronize();
#endif
}
static inline __attribute__((always_inline)) uint32_t rem2_rot(uint32_t x) {return (x<<7)|(x>>25);}
static inline __attribute__((always_inline)) uint32_t rem2_crc(const rem2_record *r) {
 uint32_t h=0xA72D19E5u;
#define RMIX(v) (h=rem2_rot(h)^(v))
 RMIX(r->cycle);RMIX(r->block);RMIX(r->job);RMIX(r->event);
 RMIX(r->pc);RMIX(r->sp);RMIX(r->wait_ticks);RMIX(r->dma_half);
 RMIX(r->dma_deadline);RMIX(r->dma_copy_tick);RMIX(r->audio_late);
 RMIX(r->last_valid_block);RMIX(r->fault_reason);RMIX(r->extra);
#undef RMIX
 return h;
}
static inline void rem2_init(rem2_blackbox *b,const char *ver,const char *sha) {
 volatile uint8_t *p=(volatile uint8_t*)b;
 for(size_t i=0;i<sizeof(*b);i++) p[i]=0;
 b->magic=REM2_TRACE_MAGIC; b->schema=REM2_TRACE_SCHEMA;
 b->bytes=(uint32_t)sizeof(*b); b->enabled=1;
 for(unsigned i=0;i<sizeof(b->firmware)-1&&ver[i];i++) b->firmware[i]=ver[i];
 for(unsigned i=0;i<sizeof(b->build_sha256)-1&&sha[i];i++) b->build_sha256[i]=sha[i];
 rem2_barrier();
}
static inline void rem2_emit(rem2_blackbox *b,unsigned core,rem2_fields v) {
 if(!b->enabled||core>=REM2_TRACE_CORE_COUNT) return;
 rem2_ring *ring=&b->cpu[core];
 uint32_t pos=ring->head, token=(pos+1u)*2u;
 rem2_record *r=&ring->events[pos%REM2_TRACE_SLOTS];
 r->commit=token-1u; rem2_barrier();
 r->cycle=v.cycle; r->block=v.block; r->job=v.job; r->event=v.event;
 r->pc=v.pc; r->sp=v.sp; r->wait_ticks=v.wait_ticks;
 r->dma_half=v.dma_half; r->dma_deadline=v.dma_deadline;
 r->dma_copy_tick=v.dma_copy_tick; r->audio_late=v.audio_late;
 r->last_valid_block=v.last_valid_block; r->fault_reason=v.fault_reason;
 r->extra=v.extra;
 r->payload_crc=rem2_crc(r);
 rem2_barrier(); r->commit=token; rem2_barrier();
 ring->head=pos+1u;
 if(pos>=REM2_TRACE_SLOTS)ring->overflow=pos+1u-REM2_TRACE_SLOTS;
}
static inline int rem2_read_slot(const rem2_record *src,rem2_record *dst) {
 uint32_t before=src->commit; rem2_barrier();
 if(before==0||before&1u)return 0;
 const volatile uint8_t *inp=(const volatile uint8_t*)src;
 uint8_t *out=(uint8_t*)dst;
 for(unsigned i=0;i<sizeof(*dst);i++)out[i]=inp[i];
 rem2_barrier();
 uint32_t after=src->commit;
 return before==after&&!(after&1u)&&dst->payload_crc==rem2_crc(dst);
}
#endif
