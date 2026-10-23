#ifndef RN_V12_CPU1_GUARD_H
#define RN_V12_CPU1_GUARD_H
#include "rn_v12_dualcore_dispatch.h"
#include <stdint.h>
/* Never boots or resets CPU1. Platform MUST attest exclusive lease and
 * shared-memory coherence. A failed in-flight job quarantines PART state
 * until the hardware/SDK externally proves CPU1 quiescent. */
typedef struct {
 void *ctx;
 int (*owns_cpu1)(void *ctx);
 int (*memory_coherent)(void *ctx);
 int (*send)(void *ctx,void(*fn)(void*),void *arg,unsigned frames,uint32_t sequence);
 int (*wait_complete)(void *ctx,uint32_t sequence,uint32_t absolute_deadline_ticks);
 int (*quiesced)(void *ctx);
} rn_dc_cpu1_platform;
typedef struct {
 rn_dc_cpu1_platform platform;
 uint32_t next_sequence,inflight,deadline_ticks;
 uint32_t accepted,completed,refused,poisoned_count;
 int poisoned,leased;
} rn_dc_cpu1_guard;
/* Attestation hooks are prerequisites, NOT implementation of SDK ownership. */
int rn_dc_cpu1_guard_arm(rn_dc_cpu1_guard *g,const rn_dc_cpu1_platform *p,uint32_t deadline_ticks);
rn_dc_executor rn_dc_cpu1_guard_executor(rn_dc_cpu1_guard *g);
int rn_dc_cpu1_guard_rearm(rn_dc_cpu1_guard *g);
#endif
