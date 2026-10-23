#ifndef BIOMECH2_MAILBOX_H
#define BIOMECH2_MAILBOX_H
#include <stdint.h>
/* BIOMECH RHYTHM 2: experimental, own protocol (NOT SDK ABI).
 * Cache-line ownership, bounded opcodes, no function pointer handoff.
 * Hardware barrier/cache coherence must be validated on PI32v2. */
#if defined(__GNUC__)
#define BR2_ALIGN __attribute__((aligned(64)))
#else
#define BR2_ALIGN
#endif
enum { BR2_NOP=0, BR2_SELFTEST=1, BR2_RENDER=2 };
enum { BR2_MAGIC=0x42493232u };
typedef struct BR2_ALIGN {
 volatile uint32_t magic, sequence, command, arg, check;
 uint32_t pad[11];
} BR2Request;
typedef struct BR2_ALIGN {
 volatile uint32_t alive, completed, result, errors;
 uint32_t pad[12];
} BR2Reply;
typedef struct BR2_ALIGN { BR2Request request; BR2Reply reply; } BR2Mailbox;
static inline uint32_t br2_check(uint32_t seq,uint32_t op,uint32_t arg){
 return BR2_MAGIC ^ (seq*0x9e3779b1u) ^ (op*0x85ebca6bu) ^ arg;
}
static inline uint32_t br2_selftest(uint32_t x){
 for(unsigned i=0;i<64;i++)x=x*1664525u+1013904223u;
 return x;
}
#endif
