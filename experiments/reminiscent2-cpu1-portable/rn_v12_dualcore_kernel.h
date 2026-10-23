#ifndef RN_V12_DUALCORE_KERNEL_H
#define RN_V12_DUALCORE_KERNEL_H
#include "rn_v12_dsp.h"
/* Fixed frame size, per-core stack scratch; send only after preparing. */
typedef struct {
 rn_v12_dsp *engine;
 uint8_t selected[4][RN_OSC_VOICES];
 uint8_t count[4];
 unsigned frames;
} rn_dc_job;
/* Return 0 for ready, 1 for flash guard (silence produced), negative on error. */
int rn_dc_prepare(rn_v12_dsp *s,int32_t *out,unsigned frames,rn_dc_job *job);
void rn_dc_render_range(rn_dc_job *job,unsigned first,unsigned last);
/* Call only after CPU1 is done AND memory is synchronized. */
int rn_dc_finalize(rn_v12_dsp *s,int32_t *out,unsigned frames);
/* Native target worker: pass the job pointer through owned CPU1 mailbox. */
void rn_dc_cpu1_part34(void *arg);
#endif
