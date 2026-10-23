#ifndef BR3_CPU1_RUNTIME_H
#define BR3_CPU1_RUNTIME_H
#include <stdint.h>
int br3_cpu1_start(void);
void br3_cpu1_attach(void);
void br3_cpu1_detach(void);
extern volatile uint32_t br3_completed_jobs, br3_timeouts;
extern volatile uint32_t br3_fallback_jobs, br3_cache_faults;
extern volatile uint32_t br3_cpu0_stage, br3_cpu1_stage;
#endif
