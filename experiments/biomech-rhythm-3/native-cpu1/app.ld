/* BIOMECH RHYTHM 3: self-contained CPU1 probe, not instrument DSP. */
MEMORY {
  XIP (rx) : ORIGIN = 0x02000120, LENGTH = 0x8DFBC
  RAM (rwx): ORIGIN = 0x01C08000, LENGTH = 0x68000
}
SECTIONS {
  .text : { KEEP(*(.text.crt0)) *(.text*) *(.rodata*) . = ALIGN(4); } > XIP
  .data : { _data_start = .; *(.data*) *(.sdata*) . = ALIGN(4); _data_end = .; } > RAM AT > XIP
  _data_load = LOADADDR(.data);
  .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(.sbss*) *(COMMON) . = ALIGN(8); _bss_end = .; } > RAM
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}