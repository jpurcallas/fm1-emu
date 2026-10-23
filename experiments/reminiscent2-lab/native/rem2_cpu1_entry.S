/* REminiSCENT 2 LAB: experimental native PI32v2 CPU1 entry.
 * Not linked to v3.0.23; not flashable. PI32 ISA from X0X/Clipper
 * hardware research; this file written independently.
 */
.section .text.r2_cpu1,"ax",@progbits
.balign 4
.globl r2_cpu1_entry
r2_cpu1_entry:
  cli
  icfg = 0
  usp = _r2_c1_ustack_top
  sp = _r2_c1_sstack_top
  ssp = _r2_c1_sstack_top
  reti = r2_cpu1_main
  rti

.section .bss.r2_c1_stack,"aw",@nobits
.balign 64
.globl _r2_c1_ustack
_r2_c1_ustack:
  .space 4096
_r2_c1_ustack_top:
  .space 256
.globl _r2_c1_sstack_top
_r2_c1_sstack_top:
