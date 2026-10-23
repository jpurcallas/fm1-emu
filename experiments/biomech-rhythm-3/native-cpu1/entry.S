/* BIOMECH 3 native CPU1 probe; experimental, not a musical firmware. */
.section .text.crt0,"ax",@progbits
.balign 4
.globl _start
_start:
    goto 1f
    rts
1:
    cli
    sp = _br3_cpu0_stack_top
    ssp = _br3_cpu0_sstack_top
    call br3_cpu0_main
2:  goto 2b

.section .text.br3_cpu1,"ax",@progbits
.balign 4
.globl br3_cpu1_entry
br3_cpu1_entry:
    cli
    icfg = 0
    usp = _br3_cpu1_stack_top
    sp = _br3_cpu1_sstack_top
    ssp = _br3_cpu1_sstack_top
    reti = br3_cpu1_main
    rti

.section .bss.br3_stacks,"aw",@nobits
.balign 8
.space 4096
_br3_cpu0_stack_top:
.space 256
_br3_cpu0_sstack_top:
.space 4096
_br3_cpu1_stack_top:
.space 256
_br3_cpu1_sstack_top:
