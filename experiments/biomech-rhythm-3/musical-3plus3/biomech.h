#ifndef BIOMECH_RHYTHM_H
#define BIOMECH_RHYTHM_H
#include "biomech_sdk_profile.h"
/* BIOMECH RHYTHM by Yeti Fingers — C99 native reference engine.
   This is NOT a flashable FM-1 firmware image. See docs/PARITY.md. */
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define BR_TRACKS 6
#define BR_STEPS 64
#define BR_POLYPHONY 64
#define BR_EVENTS 256
#define BR_SAMPLE_RATE 44100
#define BR_DELAY_MAX (BR_SAMPLE_RATE * 2)
#define BR_REVERB_MAX 16000
#define BR_RESONATOR_MAX 5200
/* Experimental FM-1 memory-limited effects. Audio is different from float32
   reference and must be auditioned. Deliberately NO resonator in this profile.
   Integer factors are from the 44100 Hz host render sample rate.
   BR_FM1_COMPACT_FX must be explicitly selected at compile time.
   Defaults: delay 11025 Hz, reverb 5512.5 Hz. */
#ifdef BR_FM1_COMPACT_FX
#ifndef BR_COMPACT_DELAY_DIV
#define BR_COMPACT_DELAY_DIV 4
#endif
#ifndef BR_COMPACT_REVERB_DIV
#define BR_COMPACT_REVERB_DIV 8
#endif
#if BR_COMPACT_DELAY_DIV < 1 || BR_COMPACT_DELAY_DIV > 16 || BR_COMPACT_REVERB_DIV < 1 || BR_COMPACT_REVERB_DIV > 16
#error "Invalid compact FX downsampling factor"
#endif
#ifndef BR_COMPACT_PCM_RANGE
#define BR_COMPACT_PCM_RANGE 8.0f
#endif
#define BR_COMPACT_DELAY_FRAMES ((BR_DELAY_MAX + BR_COMPACT_DELAY_DIV - 1) / BR_COMPACT_DELAY_DIV)
#define BR_COMPACT_R0 ((11183 + BR_COMPACT_REVERB_DIV - 1)/BR_COMPACT_REVERB_DIV)
#define BR_COMPACT_R1 ((12773 + BR_COMPACT_REVERB_DIV - 1)/BR_COMPACT_REVERB_DIV)
#define BR_COMPACT_R2 ((13937 + BR_COMPACT_REVERB_DIV - 1)/BR_COMPACT_REVERB_DIV)
#define BR_COMPACT_R3 ((15787 + BR_COMPACT_REVERB_DIV - 1)/BR_COMPACT_REVERB_DIV)
#define BR_COMPACT_REVERB_TOTAL (BR_COMPACT_R0 + BR_COMPACT_R1 + BR_COMPACT_R2 + BR_COMPACT_R3)
#endif
#define BR_MAX_PROJECT_BYTES 8192 /* v1 schema 7070 B; fail on growth, never truncate */
#if defined(BR_COMPACT_EXTERNAL_FX_STORAGE) && !defined(BR_FM1_COMPACT_FX)
#error "BR_COMPACT_EXTERNAL_FX_STORAGE requires BR_FM1_COMPACT_FX"
#endif
#if defined(BR_FM1_COMPACT_FX) && defined(BR_EXTERNAL_FX_STORAGE)
#error "Select only one FX-storage architecture"
#endif

typedef enum { BR_IMPACT,BR_RESONANCE,BR_FRACTURE,BR_ORGANIC,BR_MACHINE } BRFamily;
typedef enum { BR_AUTO,BR_SINE,BR_TRIANGLE,BR_SAW,BR_SQUARE } BRWave;
typedef enum { BR_PROBABILITY,BR_CONDITION } BRCondition;
typedef enum { BR_NORMAL,BR_ACCENT,BR_GHOST } BRAccent;
typedef enum { BR_NO_REL,BR_FOLLOW,BR_AVOID,BR_ECHO,BR_CHOKE } BRRelation;
typedef enum { BR_BOTH,BR_ADD,BR_REMOVE } BRDensityDirection;
typedef enum { BR_STRUCT_BOTH,BR_SIMPLIFY,BR_ELABORATE } BRStructureDirection;
typedef enum { BR_TUBE,BR_STRING } BRResonator;
typedef enum { BR_INTERNAL,BR_USB,BR_TRS,BR_BLE } BRClockSource;
typedef enum { BR_TIME,BR_DENSITY,BR_DYNAMICS,BR_TIMBRE,BR_RELATIONS,BR_STRUCTURE,BR_OCTAVE,BR_DIMENSIONS } BRFreedomAxis;
typedef enum { BR_LED_OFF,BR_LED_STEP_AMBER,BR_LED_PLAYHEAD_WHITE } BRLedState;

typedef struct {
  uint8_t on, active, anchor, ratchet, prob, cond_mode, cond_on, cond_every;
  int16_t micro_ms, pitch_semitones, midi_note; /* note -1 means use unpitched drum sound */
  uint8_t velocity, accent;
} BRStep;

typedef struct {
  char name[40];
  uint8_t family, waveform, lfo_target; /* lfo_target: 0 pitch, 1 amplitude */
  float body, attack, texture, decay;
  float env_attack_ms,env_decay_ms,env_sustain,env_release_ms;
  float lfo_rate_hz,lfo_depth,fine_cents,pitch_sweep;
  int8_t voice_octave,oct_low,oct_high;
  uint8_t bit_depth; float reduction_rate,bit_mix;
  float level, freedom,send_delay,send_reverb,send_resonator;
  uint8_t muted,solo,anchor,length,relationship,relation_source;
  BRStep steps[BR_STEPS];
} BRTrack;

typedef struct {
  float drive,delay_feedback,delay_wet,reverb_size,reverb_wet;
  float comp_threshold_db,comp_ratio;
  uint8_t delay_division,resonator_model;
  float resonator_tune,resonator_decay;
} BRFX;

typedef struct {
  char name[48];
  BRTrack track[BR_TRACKS];
  BRFX fx;
  float bpm,master,global_freedom,axis[BR_DIMENSIONS];
  uint8_t density_direction,structure_direction,freeze,roll_division;
  uint8_t selected_track,selected_page;
  uint32_t random_seed;
} BRProject;

typedef struct {
  uint8_t active,track,held,choke,accent;
  int16_t midi_note,midi_key;
  float phase,lfo_phase,noise_state;
  float frequency,pitch_start,pitch_end,pitch_sweep_time;
  float velocity,timbre,peak,duration,osc_gain,noise_gain;
  float elapsed,release_time,release_level,release_start;
  float bp_low,bp_band,bit_phase,bit_hold;
  /* Cached band-pass coefficients; regenerated on live TEXTURE edits. */
  float bp_last_texture,bp_f,bp_damp;
  uint8_t bp_ready;
} BRPlayingVoice;

typedef struct {uint64_t sample;uint8_t track,accent,choke,velocity;int16_t note,pitch;float timbre;} BREvent;

typedef struct {
  float data[BR_REVERB_MAX];uint32_t write,length;
  float lp;
} BRReverbLine;

/* These persistent float delay networks are kept separate from the real-time
   state so a board SDK may place them in a verified external RAM region.
   No reduction in buffer length/precision or change in the DSP algorithm. */
typedef struct {
  float delay[BR_DELAY_MAX];
  BRReverbLine reverb[4];
  float resonator[3][BR_RESONATOR_MAX];
} BRFXBuffers;

#ifdef BR_FM1_COMPACT_FX
/* Single mono tape-style delay plus four mono comb lines; each stored as
   signed 16-bit samples in one contiguous allocation. Delay is given more
   memory than reverb. Fixed point conversion permits instantaneous <=2.0
   amplitude before saturation, tracked in compact_clip_count. */
typedef struct {
  int16_t delay[BR_COMPACT_DELAY_FRAMES];
  int16_t reverb[BR_COMPACT_REVERB_TOTAL];
} BRCompactFXBuffers;
#endif

typedef struct {
  BRProject project;
  BRPlayingVoice active[BR_POLYPHONY];
  BREvent event_heap[BR_EVENTS];uint16_t events_used;
  uint32_t visits[BR_TRACKS][BR_STEPS];
  uint64_t sample_clock,next_step_sample,step_position,transport_start_sample,next_roll_sample,last_clock_sample;
  uint32_t rng,external_clock_pulses;float clock_interval_avg;
  double step_fraction;
  uint8_t playing,recording,jump_enabled,jump_step,sync_source,roll_held;
#ifdef BR_FM1_COMPACT_FX
#ifndef BR_COMPACT_EXTERNAL_FX_STORAGE
  BRCompactFXBuffers compact_fx_embedded;
#endif
  BRCompactFXBuffers *compact_fx;
  uint32_t compact_delay_write,compact_reverb_write[4];
  uint8_t compact_delay_phase,compact_reverb_phase;
  float compact_delay_lp1,compact_delay_lp2;
  float compact_reverb_lp1,compact_reverb_lp2;
  float compact_reverb_line_lp[4];
  float compact_delay_previous,compact_delay_current;
  float compact_reverb_previous,compact_reverb_current;
  float compact_delay_filter_alpha,compact_reverb_filter_alpha;
  float compact_feedback_alpha;
  uint64_t compact_clip_count,compact_limiter_count;
  float compact_write_peak_max;
#else
#ifndef BR_EXTERNAL_FX_STORAGE
  BRFXBuffers fx_embedded;
#endif
  BRFXBuffers *fx;
#endif
  uint32_t delay_write;
  float delay_lp,delay_feedback_smooth,delay_lp_coeff;
  float res_last_tune,res_last_decay,res_feedback[3],res_alpha[3];
  uint32_t res_period[3];uint8_t res_cache_valid;
  float drive_last,drive_denom;uint8_t drive_cache_valid;
  float comp_last_threshold,comp_last_ratio,comp_threshold,comp_inv_ratio,comp_makeup;
  uint8_t comp_cache_valid;
  /* Runtime-only lookup; env_sustain remains editable each sample. */
  float env_log_cache[BR_TRACKS],env_log_source[BR_TRACKS];
  uint8_t env_log_valid[BR_TRACKS];
  /* v31: tiny exact-argument memoization; no change to musical parameters. */
  float exp_cached_arg,exp_cached_result;
  float pow_cached_base,pow_cached_power,pow_cached_result;
  uint8_t exp_cached_valid,pow_cached_valid;
  float reverb_ap[2];
  float res_lp[3];uint32_t res_write[3];
  float compressor_envelope;
  uint64_t total_triggers,overflows,steps_generated;
  /* Separate counters: reaching 64 simultaneous note tails steals a voice;
     an event-heap overflow is a lost scheduled MIDI/audio trigger. */
  uint64_t voice_steals,event_overflows;
  void (*step_observer)(void *ctx,uint8_t track,uint8_t step,uint8_t fired);
  void *step_observer_ctx;
  /* Input parser; no dependencies on browser/OS. */
  uint8_t midi_status,midi_data[2],midi_index,midi_expected;
} BREngine;

void br_init(BREngine *e);
/* In BR_EXTERNAL_FX_STORAGE builds br_init_with_fx() with a valid, zeroable
   region must be used before rendering. Do not assign a fake SDRAM address. */
void br_init_with_fx(BREngine *e,BRFXBuffers *fx_memory);
#ifdef BR_FM1_COMPACT_FX
/* With BR_COMPACT_EXTERNAL_FX_STORAGE, caller MUST supply a REAL address in a
   linker-verified SRAM pool. NULL is deliberately silent, never a fake region.
   Otherwise NULL selects the engine's embedded workspace. */
void br_init_compact_with_fx(BREngine *e,BRCompactFXBuffers *workspace);
#endif
void br_new_project(BREngine *e);
void br_set_seed(BREngine *e,uint32_t seed);
void br_factory_preset(BRTrack *track,unsigned index); /* 0..19 */
const char *br_factory_name(unsigned index);
void br_init_sound(BRTrack *track);
void br_clear_track(BREngine *e,unsigned track);
void br_clear_all(BREngine *e);
void br_start(BREngine *e);
void br_stop(BREngine *e);
void br_note_on(BREngine *e,unsigned track,unsigned midi_note,unsigned velocity);
void br_note_off(BREngine *e,unsigned track,unsigned midi_note);
void br_trigger(BREngine *e,unsigned track,unsigned velocity,int midi_note);
void br_midi_byte(BREngine *e,uint8_t byte,BRClockSource source);
void br_set_sync(BREngine *e,BRClockSource source);
void br_step_once(BREngine *e);
void br_roll_hold(BREngine *e,int pressed);
void br_step_jump(BREngine *e,unsigned step,int pressed);
void br_record_note(BREngine *e,unsigned track,unsigned midi_note,unsigned velocity,unsigned quantize_division,float strength); /* deterministic testing and external scheduling */
#ifdef BR3_DUAL_CORE
/* async submit + join. wait must guarantee CPU1 is quiescent before returning.
   No nested render calls. BIOMECH 3 CPU1 HAL provides these callbacks. */
typedef struct {
  int (*submit)(void (*fn)(void *),void *arg,uint32_t frames);
  int (*wait)(void);
} BR3Executor;
void br3_set_executor(const BR3Executor *ops);
#endif
void br_render(BREngine *e,float *interleaved_stereo,size_t frames);
float br_midi_hz(float midi_note);
float br_effective_freedom(const BREngine *e,unsigned track,BRFreedomAxis axis);
BRLedState br_step_led(const BREngine *e,unsigned track,unsigned page,unsigned key);
size_t br_project_encode(const BRProject *p,uint8_t *dst,size_t capacity);
int br_project_decode(BRProject *p,const uint8_t *src,size_t length);
/* Target-safe decode variant: caller supplies a scratch project rather than
   requiring ~7 KiB of interrupt/task stack. */
int br_project_decode_workspace(BRProject *p,const uint8_t *src,size_t length,BRProject *scratch);
#ifdef __cplusplus
}
#endif
#endif
