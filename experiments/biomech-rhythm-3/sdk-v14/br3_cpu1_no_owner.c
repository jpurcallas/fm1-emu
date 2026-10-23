/* BIOMECH3 SDK V14 v0.4 emulator-only diagnostic adapter.
 * The stock SDK already controls CPU1's service lifetime. Our native 3+3
 * module has not acquired an exclusive lease in this application.
 * Return FALSE without reading, resetting or holding CPU1.
 * This explicit refusal is replaced ONLY after a verified early handoff.
 * With BR3_SDK_CPU1_PROBE_SERIAL, the complete unchanged musical engine
 * remains audible on CPU0, while R2TB/BLACK BOX describes the true gate.
 */
#ifndef BR3_SDK_CPU1_PROBE_SERIAL
#error "No-owner diagnostic may only be compiled for emulated serial probe"
#endif
int br3_cpu1_exclusive_ready(void){return 0;}
