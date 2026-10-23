#ifndef RN_V12_DUALCORE_DISPATCH_H
#define RN_V12_DUALCORE_DISPATCH_H
#include "rn_v12_dualcore_kernel.h"
/* A CPU1-ownership-neutral interface. It NEVER assumes CPU1 is free.
 * submit=1 iff the remote job was accepted and owns its data; wait_done=1
 * iff CPU1 completed and shared memory is synchronized. On failure, the
 * caller must ensure CPU1 stopped touching this engine before recovery.
 * In FM-1 integration callbacks must implement bounded waits, cache coherency,
 * correct SDK ownership checks and BLACK BOX. No automatic fallback here.
 */
typedef struct {
 void *context;
 int (*submit)(void *context, void (*fn)(void *), void *arg, unsigned frames);
 int (*wait_done)(void *context);
 /* Optional preflight BEFORE DSP event/decoder state is changed.
  * Mandatory for adapters that may quarantine timed-out CPU1 memory. */
 int (*ready)(void *context);
} rn_dc_executor;
/* Return 0 on successful audio, 0 for flash guard silence, <0 on error.
 * -3 = CPU1 submit failure, -4 = wait failure; no DMA commit after failure.
 * job storage must be shared with the CPU1 worker and remain valid until
 * completion or an explicit safe CPU1 halt/quiescence.
 */
int rn_dc_render_dispatch(rn_v12_dsp *s,int32_t *out,unsigned frames,
                          rn_dc_job *job,const rn_dc_executor *executor);
#endif
