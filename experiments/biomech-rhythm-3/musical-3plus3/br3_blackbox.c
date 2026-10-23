/* BIOMECH RHYTHM 3 - fixed-size native CPU0/CPU1 BLACK BOX (SOLO EMULADOR). */
#include "br3_blackbox.h"
#include <string.h>
BR3BlackBox br3_blackbox __attribute__((aligned(64)));
void br3_bb_init(uint32_t build_tag){
  memset(&br3_blackbox,0,sizeof(br3_blackbox));
  memcpy(br3_blackbox.marker,"BR3BBX01",8);
  br3_blackbox.schema=BR3_BB_SCHEMA;
  br3_blackbox.build_tag=build_tag;
}
void br3_bb_event(uint32_t core,uint32_t stage,uint32_t tick,
                  uint32_t seq,uint32_t arg0,uint32_t arg1){
  BR3BlackBox *b=&br3_blackbox;
  core=core?1u:0u;
  uint32_t i=b->head[core]%BR3_BB_RING;
  b->ring[core][i]=(BR3BBEvent){tick,seq,core,stage,arg0,arg1};
  b->head[core]=i+1u;
  b->events_written[core]++;
  if(core==0){
    b->cpu0_last_stage=stage;b->cpu0_last_pc=arg0;
    b->last_tick=tick;b->last_job=seq;
  }else{b->cpu1_last_stage=stage;b->cpu1_last_pc=arg0;}
}
void br3_bb_dma(uint32_t success,uint32_t tick,uint32_t half,uint32_t block){
  if(success)br3_blackbox.dma_ok++;else br3_blackbox.dma_missed++;
  br3_bb_event(0,success?BR3_BB_DMA_OK:BR3_BB_DMA_MISSED,tick,block,half,0);
}
