#include "rn_v12_dualcore_dispatch.h"
int rn_dc_render_dispatch(rn_v12_dsp *s,int32_t *out,unsigned frames,
                          rn_dc_job *job,const rn_dc_executor *executor){
 if(!executor||!executor->submit||!executor->wait_done)return -1;
 /* If a previous job may still be running, do not even prepare the next
  * block: preparation mutates shared DSP state and voice ownership. */
 if(executor->ready && !executor->ready(executor->context))return -5;
 int prep=rn_dc_prepare(s,out,frames,job);
 if(prep!=0)return prep==1?0:prep;
 /* CPU0 may continue only if CPU1 accepted immutable, published work. */
 if(!executor->submit(executor->context,rn_dc_cpu1_part34,job,frames))return -3;
 rn_dc_render_range(job,0,2);
 /* Completion implies the worker is NO LONGER mutating PARTS 3/4,
  * and that the target's memory barriers/cache operations are complete. */
 if(!executor->wait_done(executor->context))return -4;
 return rn_dc_finalize(s,out,frames);
}
