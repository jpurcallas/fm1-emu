#ifndef BIOMECH2_BLACKBOX_H
#define BIOMECH2_BLACKBOX_H
#include <stdint.h>
/* BIOMECH RHYTHM 2: fixed-size in-memory breadcrumbs. Experimental.
 * Single-writer-per-core rings prevent cross-core index contention.
 * Snapshot only after stopping/holding writers; no printing in audio ISR.
 * Cache visibility still requires PI32v2 validation. */
enum {
 BR2_BB_BOOT0=1, BR2_BB_BOOT1, BR2_BB_JOB_SENT,
 BR2_BB_JOB_ACCEPTED, BR2_BB_JOB_DONE, BR2_BB_WAIT_BEGIN,
 BR2_BB_WAIT_END, BR2_BB_TIMEOUT, BR2_BB_BAD_CHECK,
 BR2_BB_IRQ, BR2_BB_DMA_SUBMIT, BR2_BB_DMA_MISS,
 BR2_BB_RENDER_BEGIN, BR2_BB_RENDER_END
};
#define BR2_BB_DEPTH 128u
typedef struct { uint32_t tick,pc,sequence,detail; uint16_t event,core; } BR2BlackEvent;
typedef struct {
 volatile uint32_t next;
 BR2BlackEvent event[BR2_BB_DEPTH];
} BR2BlackRing;
typedef struct __attribute__((aligned(64))) {
 BR2BlackRing core[2];
 volatile uint32_t last_pc[2];
 volatile uint32_t boot_state[2];
 volatile uint32_t dma_misses;
 volatile uint32_t timeout_count;
} BR2BlackBox;
static inline void br2_black_record(BR2BlackBox *bb,unsigned core,
 uint16_t event,uint32_t tick,uint32_t pc,uint32_t seq,uint32_t detail) {
 if(core>1)return;
 BR2BlackRing *r=&bb->core[core];
 uint32_t i=r->next & (BR2_BB_DEPTH-1u);
 r->event[i]=(BR2BlackEvent){tick,pc,seq,detail,event,(uint16_t)core};
 __asm__ volatile("" ::: "memory");
 r->next++;
 bb->last_pc[core]=pc;
}
#endif
