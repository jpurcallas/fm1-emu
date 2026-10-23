#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L
#include "biomech2_blackbox.h"
#include <stdio.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include <time.h>
#include <stdint.h>
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
int main(void){
 BR2BlackBox *b=mmap(0,sizeof(*b),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
 if(b==MAP_FAILED){perror("mmap");return 2;}
 br2_black_setup(b,0x3c7130cc,42);
 pid_t pid=fork();if(pid<0)return 2;
 if(pid==0){
  b->meta.block=190;b->meta.job=23;b->meta.valid_stage=BR2_BB_JOB_ACCEPTED;
  br2_black_record(b,0,BR2_BB_JOB_SENT,100,0xAB10,23,190);
  br2_black_record(b,1,BR2_BB_JOB_ACCEPTED,101,0xCD20,23,190);
  br2_black_wait(b,20,16);br2_black_dma(b,111,110);
  br2_black_exception(b,0x44,0xCD30,0xEF00,0xBEEF);
  br2_black_record(b,1,BR2_BB_EXCEPTION,112,0xCD30,23,0x44);
  _exit(99);
 }
 int st;waitpid(pid,&st,0);
 if(!WIFEXITED(st)||WEXITSTATUS(st)!=99||b->meta.schema!=BR2_BB_SCHEMA||
 b->meta.block!=190||b->meta.job!=23||b->meta.wait_ticks!=20||
 b->meta.dma_late!=1||b->dma_misses!=1||b->meta.exception_pc!=0xCD30||
 b->core[1].next!=2){puts("FAIL recovery");return 1;}
 BR2BlackBox bench={0};br2_black_setup(&bench,0x3c7130cc,43);
 const unsigned N=1000000;volatile unsigned sink=0;
 uint64_t t0=ns();for(unsigned i=0;i<N;i++)sink+=i&1;uint64_t t1=ns();
 for(unsigned i=0;i<N;i++){br2_black_record(&bench,0,BR2_BB_JOB_SENT,i,0xAB10,i,0);sink+=i&1;}
 uint64_t t2=ns();
 printf("PASS recovery after simulated crash; block=%u job=%u wait=%u deadline=%u dma_late=%u last_pc_cpu1=0x%x\n",b->meta.block,b->meta.job,b->meta.wait_ticks,b->meta.deadline_ticks,b->meta.dma_late,b->last_pc[1]);
 printf("HOST indicative: uninstrumented %.2f ns/iter, instrumented %.2f ns/iter, extra %.2f ns/iter (not PI32v2) sink=%u\n",(t1-t0)/(double)N,(t2-t1)/(double)N,((double)(t2-t1)-(double)(t1-t0))/N,sink);
 puts("LIMIT: mmap survives a child crash only while parent lives; does NOT prove FM-1 reset persistence or audio cost.");
 return 0;
}
