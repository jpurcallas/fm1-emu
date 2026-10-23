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
 BR2_BB_RENDER_BEGIN, BR2_BB_RENDER_END,
 BR2_BB_EXCEPTION, BR2_BB_DMA_DEADLINE, BR2_BB_LAST_VALID
};
#define BR2_BB_DEPTH 128u
#define BR2_BB_SCHEMA 0x42423202u /* BB2 v2 */
#define BR2_BB_FIRMWARE_TAG 0x42493232u /* BI22; exact git SHA supplied separately */
typedef struct {
 uint32_t schema, firmware_tag, build_sha32, boot_id;
 uint32_t block, job, valid_stage, exception_code;
 uint32_t exception_pc, exception_sp, exception_addr;
 uint32_t wait_ticks, deadline_ticks, dma_copy_ticks;
 uint32_t dma_late, snapshot_ready;
} BR2BlackMeta;
typedef struct { uint32_t tick,pc,sequence,detail; uint16_t event,core; } BR2BlackEvent;
typedef struct {
 volatile uint32_t next;
 BR2BlackEvent event[BR2_BB_DEPTH];
} BR2BlackRing;
typedef struct __attribute__((aligned(64))) {
 BR2BlackMeta meta;
 BR2BlackRing core[2];
 volatile uint32_t last_pc[2];
 volatile uint32_t boot_state[2];
 volatile uint32_t dma_misses;
 volatile uint32_t timeout_count;
} BR2BlackBox;
/* The reporter must stop both writers before reading a ring.
 * For a true power/reset crash dump this region must be linked to a verified
 * NOINIT/reserved RAM region, or mirrored by the emulator. Neither is done yet. */
static inline void br2_black_setup(BR2BlackBox *bb, uint32_t sha32, uint32_t boot_id) {
 bb->meta.schema=BR2_BB_SCHEMA; bb->meta.firmware_tag=BR2_BB_FIRMWARE_TAG;
 bb->meta.build_sha32=sha32; bb->meta.boot_id=boot_id;
}
static inline void br2_black_wait(BR2BlackBox *bb, uint32_t elapsed, uint32_t deadline) {
 bb->meta.wait_ticks=elapsed; bb->meta.deadline_ticks=deadline;
}
static inline void br2_black_dma(BR2BlackBox *bb, uint32_t copy_tick, uint32_t deadline) {
 bb->meta.dma_copy_ticks=copy_tick; bb->meta.deadline_ticks=deadline;
 bb->meta.dma_late=copy_tick>deadline;
 if(bb->meta.dma_late) bb->dma_misses++;
}
static inline void br2_black_exception(BR2BlackBox *bb, uint32_t code,
  uint32_t pc, uint32_t sp, uint32_t addr) {
 bb->meta.exception_code=code;bb->meta.exception_pc=pc;
 bb->meta.exception_sp=sp;bb->meta.exception_addr=addr;
}
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
