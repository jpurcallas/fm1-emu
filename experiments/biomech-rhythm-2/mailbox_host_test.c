#define _POSIX_C_SOURCE 200809L
#include "biomech2_mailbox.h"
#include <pthread.h>
#include <stdio.h>
#include <stdatomic.h>
static BR2Mailbox mb;
static atomic_uint stop_worker;
static pthread_t worker;
static void *cpu1(void *unused){
 (void)unused; uint32_t last=0; mb.reply.alive=1;
 while(!atomic_load_explicit(&stop_worker,memory_order_relaxed)){
  uint32_t seq=mb.request.sequence;
  if(seq==last)continue;
  atomic_thread_fence(memory_order_acquire);
  uint32_t op=mb.request.command,arg=mb.request.arg,ck=mb.request.check;
  if(seq!=last+1 || ck!=br2_check(seq,op,arg)){
   mb.reply.errors++; continue;
  }
  if(op!=BR2_SELFTEST){mb.reply.errors++;continue;}
  mb.reply.result=br2_selftest(arg);
  atomic_thread_fence(memory_order_release);
  mb.reply.completed=seq;last=seq;
 }return NULL;
}
static int wait_for(volatile uint32_t *p,uint32_t target,unsigned spins){
 for(unsigned i=0;i<spins;i++){
  atomic_thread_fence(memory_order_acquire);if(*p==target)return 1;
 }return 0;
}
int main(void){
 if(sizeof(BR2Request)!=64 || sizeof(BR2Reply)!=64){puts("FAIL layout");return 2;}
 if(pthread_create(&worker,NULL,cpu1,NULL)){puts("FAIL pthread");return 2;}
 if(!wait_for(&mb.reply.alive,1,100000000)){puts("FAIL boot");return 2;}
 for(uint32_t seq=1;seq<=1000;seq++){
  uint32_t arg=seq*51u;
  mb.request.magic=BR2_MAGIC;mb.request.arg=arg;
  mb.request.command=BR2_SELFTEST;
  mb.request.check=br2_check(seq,BR2_SELFTEST,arg);
  atomic_thread_fence(memory_order_release);mb.request.sequence=seq;
  if(!wait_for(&mb.reply.completed,seq,100000000)){printf("FAIL wait %u\n",seq);return 1;}
  if(mb.reply.result!=br2_selftest(arg)){printf("FAIL result %u\n",seq);return 1;}
 }
 atomic_store(&stop_worker,1);pthread_join(worker,NULL);
 if(mb.reply.errors){puts("FAIL errors");return 1;}
 puts("PASS 1000/1000 CPU0->CPU1->CPU0 selftest jobs");
 return 0;
}
