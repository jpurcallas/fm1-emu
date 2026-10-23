/* BIOMECH RHYTHM 2: experimental PI32v2 CPU1 entry. SOLO EMULADOR. */
/* Own stacks and a return-from-interrupt into C entry, reference structure
 * validated against X0X/Clipper publicly documented PI32v2 startup.
 * NOT wired to the stock firmware or its SDK startup yet. */
.section .text.br2_cpu1,"ax",@progbits
.balign 4
.globl br2_cpu1_entry
br2_cpu1_entry:
 cli
 icfg = 0
 usp = _br2_c1_ustack_top
 sp = _br2_c1_sstack_top
 ssp = _br2_c1_sstack_top
 reti = br2_cpu1_main
 rti
.section .bss.br2_c1_stack,"aw",@nobits
.balign 8
.globl _br2_c1_ustack
_br2_c1_ustack:
.space 4096
_br2_c1_ustack_top:
.space 256
.globl _br2_c1_sstack_top
_br2_c1_sstack_top:
