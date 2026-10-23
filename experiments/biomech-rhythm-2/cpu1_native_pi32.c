/* BIOMECH RHYTHM 2 CPU1 direct boot – EXPERIMENTAL source, NOT LINKED.
 * Conceptual register sequence drawn from public X0X hardware findings.
 * Must verify CPU1 entry assembly/stack, SDK startup ownership & linker before enabling.
 */
#include <stdint.h>
#include "biomech2_mailbox.h"
#include "biomech2_blackbox.h"
#define BR2_IO(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define BR2_C1_CON 0x01EEE004u
#define BR2_C1_CLK 0x00010008u
#define BR2_ENTRY_WORD 0x01C7FFF8u
#define BR2_C1_IRQ_BASE 0x01EEF300u
#define BR2_TIMER4 0x00010804u
#define BR2_TIMEOUT (24u * 1000u * 20u)
typedef struct { BR2Mailbox mailbox; BR2BlackBox blackbox; } BR2Lab;
extern void br2_cpu1_entry(void); /* assembly + dedicated stack not yet linked */
extern void br2_lab_init(BR2Lab *, uint32_t);
extern void br2_cpu1_enter(BR2Lab *);
extern void br2_cpu1_poll(BR2Lab *);
static BR2Lab br2_shared __attribute__((aligned(64)));
void br2_sync(void){__asm__ volatile("csync" ::: "memory");}
uint32_t br2_clock(void){return BR2_IO(BR2_TIMER4);}
BR2Lab *br2_native_lab(void){return &br2_shared;}
void __attribute__((section(".br2_cpu1_ram"),noreturn)) br2_cpu1_main(void){
 br2_cpu1_enter(&br2_shared);
 for(;;)br2_cpu1_poll(&br2_shared);
}
/* IMPORTANT: Existing BIOMECH v0.35 SDK starts CPU1 already.
 * Do not call this without replacing its startup in a throwaway firmware.
 * Valid PC bounds and top RAM access must be arranged beforehand. */
int br2_cpu1_start_native(uint32_t build_sha32){
 uint32_t saved,t0;
 BR2_IO(BR2_C1_CON)|=2u;
 BR2_IO(BR2_C1_CON)&=~8u; br2_sync();
 br2_lab_init(&br2_shared,build_sha32);
 for(unsigned i=0;i<32;i++)BR2_IO(BR2_C1_IRQ_BASE+i*4u)=0;
 BR2_IO(BR2_ENTRY_WORD)=(uint32_t)(uintptr_t)&br2_cpu1_entry;
 saved=BR2_IO(BR2_C1_CLK);
 BR2_IO(BR2_C1_CLK)=saved|8u; br2_sync();
 BR2_IO(BR2_C1_CON)|=8u;
 BR2_IO(BR2_C1_CON)&=~2u;
 t0=br2_clock();
 while(!br2_shared.mailbox.reply.alive &&
       (uint32_t)(br2_clock()-t0)<BR2_TIMEOUT)br2_sync();
 BR2_IO(BR2_C1_CLK)=saved;
 if(!br2_shared.mailbox.reply.alive){
  BR2_IO(BR2_C1_CON)|=2u;BR2_IO(BR2_C1_CON)&=~8u;
  br2_shared.blackbox.timeout_count++;
  br2_black_record(&br2_shared.blackbox,0,BR2_BB_TIMEOUT,br2_clock(),0,0,BR2_TIMEOUT);
  return -1;
 }
 return 0;
}
