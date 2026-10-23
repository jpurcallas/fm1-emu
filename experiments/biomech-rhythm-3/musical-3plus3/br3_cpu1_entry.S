/* BIOMECH 3 CPU1 private stack: source-only experimental PI32v2. */
.section .text.br3_cpu1_entry,"ax",@progbits
.balign 4
.globl br3_cpu1_entry
br3_cpu1_entry:
  cli
  icfg = 0
  usp = _br3_cpu1_ustack_top
  sp = _br3_cpu1_sstack_top
  ssp = _br3_cpu1_sstack_top
  reti = br3_cpu1_main
  rti
.section .bss.br3_cpu1_stack,"aw",@nobits
.balign 8
.globl _br3_cpu1_ustack
_br3_cpu1_ustack:
.space 4096
.globl _br3_cpu1_ustack_top
_br3_cpu1_ustack_top:
.space 256
.globl _br3_cpu1_sstack_top
_br3_cpu1_sstack_top:
