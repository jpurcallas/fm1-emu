/* Native executable test only. NO firmware update package. */
MEMORY {
 XIP (rx) : ORIGIN = 0x02000120, LENGTH = 0x8DFBC
 RAM (rwx) : ORIGIN = 0x01C08000, LENGTH = 0x6C000
}
SECTIONS {
 .text : {KEEP(*(.text.crt0)) *(.text*) *(.br3_cpu1_text*) *(.rodata*) . = ALIGN(4); } > XIP
 .data : { . = ALIGN(4); _data_start = .; *(.data*) *(.sdata*) . = ALIGN(4); _data_end = .; } > RAM AT > XIP
 _data_load = LOADADDR(.data);
 .bss (NOLOAD) : { . = ALIGN(64); _bss_start = .; *(.bss*) *(.sbss*) *(COMMON) . = ALIGN(64); _bss_end = .; } > RAM
 /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
