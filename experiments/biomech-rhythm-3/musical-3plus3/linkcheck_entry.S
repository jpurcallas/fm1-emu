/* Standalone CPU0 test entry. Does not configure FM-1 DAC or UI. */
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
2:goto 2b
.section .bss.br3_cpu0_stack,"aw",@nobits
.balign 8
.space 4096
.globl _br3_cpu0_stack_top
_br3_cpu0_stack_top:
.space 256
.globl _br3_cpu0_sstack_top
_br3_cpu0_sstack_top:
