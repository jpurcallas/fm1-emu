#ifndef BR3_BLACKBOX_H
#define BR3_BLACKBOX_H
#include <stdint.h>
/* Raw firmware-RAM diagnostic. The emulator's full RAM JSON already captures it;
   parse it using br3_extract_blackbox.py. This remains in guest RAM if the
   emulator halts, but is NOT promised to survive a hardware power loss. */
#define BR3_BB_SCHEMA 1u
#define BR3_BB_RING 32u
enum {
  BR3_BB_BOOT=1,BR3_BB_CPU1_ALIVE=2,BR3_BB_JOB_SEND=3,
  BR3_BB_JOB_ACCEPT=4,BR3_BB_JOB_DONE=5,BR3_BB_WAIT_OK=6,
  BR3_BB_TIMEOUT=7,BR3_BB_BAD_JOB=8,BR3_BB_FALLBACK=9,
  BR3_BB_DMA_OK=10,BR3_BB_DMA_MISSED=11,BR3_BB_EXCEPTION=12
};
typedef struct {
  uint32_t tick,seq,core,stage,arg0,arg1;
} BR3BBEvent;
typedef struct __attribute__((aligned(64))) {
  char marker[8];           /* literal "BR3BBX01", allows scan in RAM capture */
  uint32_t schema,build_tag;
  volatile uint32_t events_written[2],head[2];
  volatile uint32_t jobs_sent,jobs_done,jobs_bad,job_timeouts;
  volatile uint32_t fallback_count,dma_ok,dma_missed;
  volatile uint32_t cpu0_last_stage,cpu1_last_stage;
  volatile uint32_t cpu0_last_pc,cpu1_last_pc;
  volatile uint32_t last_job,last_tick,last_wait_ticks,max_wait_ticks;
  volatile uint32_t last_error;
  BR3BBEvent ring[2][BR3_BB_RING];
} BR3BlackBox;
extern BR3BlackBox br3_blackbox;
void br3_bb_init(uint32_t build_tag);
void br3_bb_event(uint32_t core,uint32_t stage,uint32_t tick,
                  uint32_t seq,uint32_t arg0,uint32_t arg1);
void br3_bb_dma(uint32_t success,uint32_t tick,uint32_t half,uint32_t block);
#endif
