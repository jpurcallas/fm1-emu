#ifndef BIOMECH_SDK_PROFILE_H
#define BIOMECH_SDK_PROFILE_H
/* Explicit FM1 V14 experiment: QUALITY profile, separate effect buffers.
 * Not an implicit reduction of the v0.4/reference engine.
 * This source is copied into app/biomech by sdk_overlay/apply_overlay.py,
 * where the FM1 builder picks it up without editing the SDK Build.ps1.
 */
#define BR_FM1_COMPACT_FX 1
#define BR_COMPACT_EXTERNAL_FX_STORAGE 1
#define BR_COMPACT_DELAY_DIV 2
#define BR_COMPACT_REVERB_DIV 4
#endif
