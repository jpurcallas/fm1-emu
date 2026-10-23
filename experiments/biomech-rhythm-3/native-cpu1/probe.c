/* BIOMECH 3: independent native CPU1 handshake; EXPERIMENTAL, NO INSTALL.
 * This is a worker-launch proof, NOT the BIOMECH synthesizer.
 */
#include <stdint.h>
#define IO(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define C1_CON 0x01EEE004u
#define C1_CLK 0x00010008u
#define C1_ENTRY 0x01C7FFF8u
#define C1_IRQ 0x01EEF300u
#define SYNC() __asm__ volatile("csync" ::: "memory")
#define MAGIC 0x42523333u
#define SUCCESS 0xB3300003u
#define FAIL_START 0xB33E0001u
#define FAIL_TIMEOUT 0xB33E0002u
#define FAIL_RESULT 0xB33E0003u

typedef struct __attribute__((aligned(64))) {
    volatile uint32_t sequence,command,argument,check;
    uint32_t pad[12];
} Br3Request;
typedef struct __attribute__((aligned(64))) {
    volatile uint32_t alive,completed,value,errors;
    uint32_t pad[12];
} Br3Reply;
typedef struct __attribute__((aligned(64))) {
    Br3Request request;
    Br3Reply reply;
} Br3Mailbox;
volatile Br3Mailbox br3_mailbox;
volatile uint32_t br3_status;
volatile uint32_t br3_cpu0_trace;
volatile uint32_t br3_cpu1_trace;
volatile uint32_t br3_result_expected;
volatile uint32_t br3_result_observed;
extern void br3_cpu1_entry(void);
static uint32_t check(uint32_t seq,uint32_t op,uint32_t arg) {
    return MAGIC ^ (seq*0x9e3779b1u) ^ (op*0x85ebca6bu) ^ arg;
}
static uint32_t work(uint32_t x) {
    for(unsigned i=0;i<64;i++) x=x*1664525u+1013904223u;
    return x;
}
void __attribute__((noreturn)) br3_cpu1_main(void) {
    uint32_t done=0;
    br3_cpu1_trace=0xC1000001u;
    br3_mailbox.reply.alive=MAGIC;
    SYNC();
    for (;;) {
        uint32_t seq=br3_mailbox.request.sequence;
        SYNC();
        if(seq==done) continue;
        uint32_t op=br3_mailbox.request.command;
        uint32_t arg=br3_mailbox.request.argument;
        uint32_t c=br3_mailbox.request.check;
        if(seq!=done+1u || op!=1u || c!=check(seq,op,arg)) {
            br3_mailbox.reply.errors++;
            br3_cpu1_trace=0xC1BAD001u;
            done=seq;
            continue;
        }
        uint32_t value=work(arg);
        br3_mailbox.reply.value=value;
        SYNC();
        br3_mailbox.reply.completed=seq;
        SYNC();
        br3_cpu1_trace=0xC1000002u;
        done=seq;
    }
}
void __attribute__((noreturn)) br3_cpu0_main(void) {
    uint32_t saved;
    br3_mailbox.reply.alive=0;
    br3_mailbox.reply.completed=0;
    br3_mailbox.reply.errors=0;
    br3_mailbox.request.sequence=0;
    br3_status=0xB3300001u;
    br3_cpu0_trace=0xC0000001u;
    SYNC();
    IO(C1_CON)|=2u;
    IO(C1_CON)&=~8u;
    SYNC();
    for(unsigned i=0;i<32;i++) IO(C1_IRQ+i*4u)=0;
    IO(C1_ENTRY)=(uint32_t)(uintptr_t)&br3_cpu1_entry;
    saved=IO(C1_CLK);
    IO(C1_CLK)=saved|8u;
    SYNC();
    IO(C1_CON)|=8u;
    IO(C1_CON)&=~2u;
    for(volatile uint32_t wait=0;wait<3000000u && br3_mailbox.reply.alive!=MAGIC;wait++) SYNC();
    IO(C1_CLK)=saved;
    if(br3_mailbox.reply.alive!=MAGIC) {
        br3_status=FAIL_START;
        br3_cpu0_trace=0xC0BAD001u;
        goto parked;
    }
    br3_status=0xB3300002u;
    br3_cpu0_trace=0xC0000002u;
    const uint32_t arg=0x1234ABCDu;
    const uint32_t seq=1u;
    br3_result_expected=work(arg);
    br3_mailbox.request.command=1u;
    br3_mailbox.request.argument=arg;
    br3_mailbox.request.check=check(seq,1u,arg);
    SYNC();
    br3_mailbox.request.sequence=seq;
    SYNC();
    for(volatile uint32_t wait=0;wait<3000000u && br3_mailbox.reply.completed!=seq;wait++) SYNC();
    if(br3_mailbox.reply.completed!=seq) {
        br3_status=FAIL_TIMEOUT;
        br3_cpu0_trace=0xC0BAD002u;
        goto parked;
    }
    br3_result_observed=br3_mailbox.reply.value;
    if(br3_result_observed!=br3_result_expected || br3_mailbox.reply.errors) {
        br3_status=FAIL_RESULT;
        br3_cpu0_trace=0xC0BAD003u;
    } else {
        br3_status=SUCCESS;
        br3_cpu0_trace=0xC0000003u;
    }
parked:
    for(;;) SYNC();
}
