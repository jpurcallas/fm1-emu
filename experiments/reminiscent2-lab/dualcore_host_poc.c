/* REminiSCENT 2 LAB: independent CPU1 job dispatch, HOST PROOF ONLY.
 * NOT the instrument DSP. Demonstrates serial controls, 4 independent render
 * jobs, original order of sum and shared effect after rendezvous.
 * C99 + POSIX pthreads only for host simulation. No SDK used here.
 */
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sched.h>
#define PARTS 4
#define FRAMES 128
#define BLOCKS 256

typedef struct { uint32_t phase, increment, amplitude; int32_t samples[FRAMES]; } Part;
typedef struct { Part parts[PARTS]; volatile unsigned job, done, stop; } Lab;
static inline unsigned load(volatile unsigned *p) { return __atomic_load_n(p,__ATOMIC_ACQUIRE); }
static inline void store(volatile unsigned *p,unsigned x) { __atomic_store_n(p,x,__ATOMIC_RELEASE); }

static void prepare(Lab *s, unsigned block) { /* CPU0 only: serial event/parameter stage */
  for (unsigned p=0;p<PARTS;p++) {
    s->parts[p].increment=1193u+421u*p+(block%7)*31u;
    s->parts[p].amplitude=(block>=150u && block<160u) ? 0u : 1800u+(p*177u);
  }
}
static void render_one(Part *p) { /* stand-in kernel, NOT REminiSCENT DSP */
  uint32_t ph=p->phase;
  for (unsigned i=0;i<FRAMES;i++) {
    ph+=p->increment;
    p->samples[i]=(int32_t)(((int64_t)(int32_t)(ph>>18)*p->amplitude)>>13);
  }
  p->phase=ph;
}
static void fx_after_mix(int32_t *pcm) { /* generic post-mix stage, NOT REminiSCENT FX */
  for (unsigned i=1;i<FRAMES;i++) pcm[i]=(pcm[i]*7+pcm[i-1])/8;
}
static void mix_ordered(Lab *s,int32_t *out) { /* part sum order invariant */
  for (unsigned i=0;i<FRAMES;i++) {
    int64_t v=0;
    for (unsigned p=0;p<PARTS;p++) v+=s->parts[p].samples[i];
    out[i]=(int32_t)v;
  }
  fx_after_mix(out);
}
static void *cpu1(void *ptr) {
  Lab *s=(Lab*)ptr;
  unsigned seen=0;
  while (!load(&s->stop)) {
    unsigned issued=load(&s->job);
    if (issued==seen) {sched_yield();continue;}
    render_one(&s->parts[2]);
    render_one(&s->parts[3]);
    seen=issued;
    store(&s->done,seen);
  }
  return NULL;
}
int main(void) {
  Lab serial={0},parallel={0};
  pthread_t thread;
  int32_t a[FRAMES],b[FRAMES];
  if(pthread_create(&thread,NULL,cpu1,&parallel)!=0){perror("pthread_create");return 2;}
  for (unsigned block=0;block<BLOCKS;block++) {
    prepare(&serial,block); prepare(&parallel,block);
    for (unsigned p=0;p<PARTS;p++) render_one(&serial.parts[p]);
    mix_ordered(&serial,a);
    store(&parallel.job,block+1u);  /* publish immutable part params */
    render_one(&parallel.parts[0]);
    render_one(&parallel.parts[1]);
    while(load(&parallel.done)!=block+1u) sched_yield();
    mix_ordered(&parallel,b);
    if(memcmp(a,b,sizeof(a))!=0) {
      fprintf(stderr,"MISMATCH at block %u\n",block);
      store(&parallel.stop,1u);pthread_join(thread,NULL);return 1;
    }
  }
  store(&parallel.stop,1u); pthread_join(thread,NULL);
  puts("PASS 256 blocks, 4 parts, NOTE OFF-like gate, serial vs parallel PCM EXACT");
  puts("NOTE: host surrogate; NOT native PI32v2, NOT REminiSCENT DSP, NOT real-time proof");
  return 0;
}
