#ifndef RAM_ATTR_H
#define RAM_ATTR_H
/* Restore v0.35/v0.37 real-time SRAM placement ONLY when the native
   FM1 V14 SDK integration is explicitly selected. The isolated PI32v2
   XIP selftest still uses regular .text, avoiding orphan-section loads.
   This does not change any DSP formula or enable a shorter sound path. */
#if defined(BR3_SDK_NATIVE_AUDIO) && (defined(__GCC_PI32V2__) || defined(BR3_PI32V2))
#define BR_RAMCODE __attribute__((section(".volatile_ram_code"),noinline,used))
#define BR_RAMCONST __attribute__((section(".volatile_ram"),used))
#else
#define BR_RAMCODE
#define BR_RAMCONST
#endif
#endif
