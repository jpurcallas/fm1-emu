//! FM-1 SoC: memory map + peripherals.
//!
//! Memory map (recon + Felucca HAL headers + corpus literals):
//!   0x0200_0000  XIP flash (app window) — code runs from here
//!   0x01c0_0000  data RAM (≥512 KiB; BOOT_STATE at 0x01C7FD80 observed)
//!   0x5000_0-    GPIO ports A..H (0x40 stride: OUT+0, DIR+8, DIE+C, PU+10, PD+14)
//!   0x5100_|     IOMAP
//!   0x1000_-0x1002  clock
//!   0x1080_0/0x1090_0  TIMER4/TIMER5 (CNT reads = synthetic progress)
//!   0x11c0_0-    SPI0 = external NOR flash (model in spiflash.rs; CS = PD0)
//!   0x11d0_0-    SPI1 = LCD (ST7789-class 240×240, model in lcd.rs)
//!   0x1180_0-    USB
//!   0x1210_0-    UART1 (MIDI IN)
//!   0x1310_0-    ADC
//!   0x1eee000-   interrupt controller (0x1eee008 bit14 = ready, polled by the
//!                RAM early-init; the rest stored bits)
//!   0x1eee240    DBG_MSG debug box (console)
//!   0x01f0_0000  SRAM banks (256 KiB; cleared by the early init, config block at 0x1f28000)
//!   0x01c0xxxx 'negative' long-call targets are RAM-resident .data code
//!   (copied from flash 0x02084820 by the CRT), not a mask ROM
//!
//! Policy: unknown MMIO accesses are logged and return a benign default —
//! never silently swallowed. The access log is the reverse-engineering
//! roadmap.

use fm1_core::Bus;

pub mod script;
pub mod flaky;
pub mod fwsc;
mod lcd;
pub mod machine;
pub mod p33;
pub mod periph;
mod ram;
pub mod smk;
mod spiflash;

pub use lcd::{write_bmp, Lcd};
pub use periph::{Action, Periph, CPU_HZ, VEC_BASE};
pub use ram::Ram;
pub use spiflash::{SpiFlash, FLASH_SIZE};

pub const XIP_BASE: u32 = 0x0200_0000;
pub const RAM_BASE: u32 = 0x01c0_0000;
pub const OVL_BASE: u32 = 0x0400_0000;
pub const SRAM2_BASE: u32 = 0x01f0_0000;
/// The stock V13 firmware's .bd_base: what the BT baseband's window register 0x2FC44 reads
/// before a firmware writes it (each stock image writes its own .bd_base there: V13 this,
/// the SMK-37's v016 0x01C09A18).
pub const BT_WINDOW_BASE: u32 = 0x01c0_9e7c;
/// The flash offset behind XIP 0x02000000 (the stock layout: the app area starts at 0x4000).
pub const XIP_FLASH_OFFSET: usize = 0x4000;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnknownAccess {
    pub addr: u32,
    pub width: u8,
    pub is_write: bool,
    pub value: u32,
}

enum Region {
    Xip,
    Ram,
    Ovl,
    Gpio,
    Iomap,
    Clk,
    Timer,
    Spi0,
    Spi1,
    Usb,
    Uart1,
    Adc,
    Ana,
    /// The power domain's register port (p33.rs).
    P33,
    Bt,
    Spi2,
    Crc,
    Rand,
    XipFlash,
    Dbg,
    Irqc,
    /// Interrupt controller enable/priority words and software latch.
    Irqc2,
    /// ALNK0 I2S out.
    Alnk,
    Sram2,
    Unknown,
}

/// The SoC bus: XIP flash + data RAM + modeled peripherals + a logged stub.
/// A cheap hasher for register addresses (the SoC's register map): `std`'s SipHash cost the
/// SMK-37's stock firmware, which touches registers about a million times a second, a few
/// percent of its time.
#[derive(Default)]
pub struct AddrHasher(u64);

impl std::hash::Hasher for AddrHasher {
    fn finish(&self) -> u64 {
        self.0
    }
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.0 = (self.0 ^ b as u64).wrapping_mul(0x100_0000_01b3);
        }
    }
    fn write_u32(&mut self, v: u32) {
        self.0 = (v as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15);
    }
}

/// The board around the chip: the FM-1's panel, or the SMK-37's (SMK-37 Pro / Elite, MKE-P37
/// and Starrykey 37 Play share one: fm1-to-smk37 docs/01-hardware.md). Same chip, flash
/// layout, audio and update path; the panel's wiring differs (smk.rs).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum Board {
    #[default]
    Fm1,
    Smk37,
}

impl Board {
    /// The board a package is for, from its identity (`FM-1_015`, `SMK-37 Pro_016`, ...).
    pub fn of_identity(id: &str) -> Board {
        let u = id.to_ascii_uppercase();
        if ["SMK", "MKE", "STARRYKEY"].iter().any(|p| u.starts_with(p)) {
            Board::Smk37
        } else {
            Board::Fm1
        }
    }
}

/// Emulator-only passive memory transition watcher. Off by default.
#[derive(Default)]
pub struct KeyVoiceWatch {
    pub checks: u64,
    prev: Option<(u8,u8,u8)>,
    transitions: Vec<(u64,u64,u64,u8,u8,u8,bool)>,
}
impl KeyVoiceWatch {
    pub fn report(&self) -> String {
        let events = self.transitions.iter().map(|(cycle,ms,halves,key,voice,pitch,pending)|format!(
            r#"{{"cycle":{},"ms":{},"halves":{},"keyFlag":{},"voiceFlag":{},"pitch":{},"osTickPending":{}}}"#,
            cycle,ms,halves,key,voice,pitch,pending
        )).collect::<Vec<_>>().join(",");
        format!(r#"{{"checks":{},"transitions":[{}]}}"#,self.checks,events)
    }
}

/// A passive, optional transition sampler at CPU0/CPU1 scheduling boundaries.
/// The reported PC is AFTER the slice, never claimed to be the instruction
/// performing the write. This narrows which core and scheduling window changed
/// the voice-state byte; it does not alter any guest instruction or memory.
#[derive(Default)]
pub struct CoreWriterProbe {
    pub checks: u64,
    last: Option<(u8,u8,u8)>,
    events: Vec<(u64,u64,u64,u32,u32,u32,u8,u8,u8)>,
    irq_counts: std::collections::BTreeMap<u8,u64>,
    irq_recent: std::collections::VecDeque<(u64,u8,u32,u32)>,
    voice_irq_context: Vec<(u64,u8,u32,u32)>,
    exact_stores: Vec<(u64,u64,u32,u32,u8,u8,u8)>,
    irq11_snapshots: Vec<(u64,u64,u8,String,String,String,String)>,
    other_stores: Vec<(u64,u64,u32,u32,u8,u8,u8)>,
    schedule_events: Vec<(u64,u64,u8,u32,u32,u8,u8,u8)>,
    irq127_writes: Vec<(u64,u64,u32,u32,u8,u32,u32,u8,u8)>,
    // CPU0/CPU1 acknowledgement byte: exact guest store, not a slice-end inference.
    sync_ack_writes: Vec<(u64,u64,u8,u32,u32,u8,u8,u8,bool)>,
    sync_ack_dropped: u64,
}
impl CoreWriterProbe {
    pub fn report(&self) -> String {
        let events = self.events.iter().map(
            |(cycle,ms,halves,core,pc,irqdepth,key,voice,note)|format!(
                r#"{{"cycle":{},"ms":{},"halves":{},"stageCore":{},"pcAfterSlice":"0x{:08x}","irqDepth":{},"key":{},"voice":{},"note":{}}}"#,
                cycle,ms,halves,core,pc,irqdepth,key,voice,note
            )
        ).collect::<Vec<_>>().join(",");
        let counts=self.irq_counts.iter().map(|(irq,n)|format!(r#""{}":{}"#,irq,n)).collect::<Vec<_>>().join(",");
        let recent=self.irq_recent.iter().map(|(cycle,irq,handler,return_pc)|format!(
            r#"{{"cycle":{},"irq":{},"handler":"0x{:08x}","returnPc":"0x{:08x}"}}"#,
            cycle,irq,handler,return_pc
        )).collect::<Vec<_>>().join(",");
        let at_voice=self.voice_irq_context.iter().map(|(cycle,irq,handler,return_pc)|format!(
            r#"{{"cycle":{},"irq":{},"handler":"0x{:08x}","returnPc":"0x{:08x}"}}"#,
            cycle,irq,handler,return_pc
        )).collect::<Vec<_>>().join(",");
        let exact=self.exact_stores.iter().map(|(cycle,halves,pc,addr,width,before,after)|format!(
            r#"{{"cycle":{},"half":{},"exactPc":"0x{:08x}","addr":"0x{:08x}","width":{},"before":{},"after":{}}}"#,
            cycle,halves,pc,addr,width,before,after)).collect::<Vec<_>>().join(",");
        let snapshots=self.irq11_snapshots.iter().map(|(cycle,half,key,notes,keys,queues,aux)|format!(
            r#"{{"cycle":{},"half":{},"physicalKey":{},"notes":"{}","keys":"{}","queues":"{}","aux":"{}"}}"#,
            cycle,half,key,notes,keys,queues,aux
        )).collect::<Vec<_>>().join(",");
        let others=self.other_stores.iter().map(|(cycle,half,pc,addr,width,before,after)|format!(
            r#"{{"cycle":{},"half":{},"pc":"0x{:08x}","addr":"0x{:08x}","width":{},"before":{},"after":{}}}"#,
            cycle,half,pc,addr,width,before,after
        )).collect::<Vec<_>>().join(",");
        let schedule=self.schedule_events.iter().map(|(cycle,half,irq,handler,return_pc,panel,producer,voice)|format!(
            r#"{{"cycle":{},"half":{},"irq":{},"handler":"0x{:08x}","returnPc":"0x{:08x}","panel":{},"producer":{},"voice":{}}}"#,
            cycle,half,irq,handler,return_pc,panel,producer,voice
        )).collect::<Vec<_>>().join(",");
        let requests=self.irq127_writes.iter().map(|(cycle,half,pc,addr,width,value,ilat,panel,producer)|format!(
            r#"{{"cycle":{},"half":{},"pc":"0x{:08x}","addr":"0x{:08x}","width":{},"value":{},"ilatBefore":{},"panel":{},"producer":{}}}"#,
            cycle,half,pc,addr,width,value,ilat,panel,producer
        )).collect::<Vec<_>>().join(",");
        let acknowledgements=self.sync_ack_writes.iter().enumerate().map(
            |(seq,(cycle,half,core,pc,addr,width,before,after,jit))| format!(
                r#"{{"seq":{},"cycle":{},"half":{},"core":{},"pc":"0x{:08x}","addr":"0x{:08x}","width":{},"before":{},"after":{},"jitCallback":{}}}"#,
                seq,cycle,half,core,pc,addr,width,before,after,jit
            )
        ).collect::<Vec<_>>().join(",");
        format!(r#"{{"checks":{},"events":[{}],"irqCounts":{{{}}},"recentIrqs":[{}],"irqAtVoice":[{}],"exactStores":[{}],"irq11Snapshots":[{}],"otherStores":[{}],"schedule":[{}],"irq127Writes":[{}],"syncAckWrites":[{}],"syncAckDropped":{}}}"#,
            self.checks,events,counts,recent,at_voice,exact,snapshots,others,schedule,requests,
            acknowledgements,self.sync_ack_dropped)
    }
}

pub struct Soc {
    pub board: Board,
    /// The BT baseband's window base (0x2FC44), as the firmware set it.
    bt_window: u32,
    pub xip: Vec<u8>,
    pub ram: Ram,
    pub lcd: Lcd,
    /// SPI0 + the external NOR flash (1 MiB; `--flash` image loaded at 0).
    pub flash: SpiFlash,
    /// Console bytes written through DBG_MSG / UART-style debug boxes.
    pub console: Vec<u8>,
    /// Overlay RAM (second bank, 0x04000000), written by the app CRT.
    pub ovl: Ram,
    /// SRAM banks at 0x01f00000 (cleared by the RAM early init).
    pub sram2: Ram,
    /// monotonic "time" for peripheral counters
    pub ticks: u64,
    /// Timers, audio DMA, ADC, interrupt controller and the front panel.
    pub periph: Periph,
    /// Opt-in read-only guest RAM watch for key release; disabled normally.
    pub keyvoice_watch: Option<KeyVoiceWatch>,
    pub writer_probe: Option<CoreWriterProbe>,
    current_instruction_pc: u32,
    current_instruction_core: u8,
    // Suppress the duplicate bus notification following a JIT guest-store callback.
    pending_sync_jit_store: Option<(u8,u32,u32,u8,u32)>,
    sfr: std::collections::HashMap<u32, u32, std::hash::BuildHasherDefault<AddrHasher>>,
    /// Core 0 / 1 paused by the other (C0_CON / C1_CON bit 2 pulses, bit 3 resumes).
    paused: [bool; 2],
    /// The XIP window continues into the flash chip past the image (the stock layout, which
    /// the updater gives every firmware: April OS keeps its samples at flash 0x74000, read
    /// through XIP 0x02070000, and waits at boot until it finds them or a blank chip's 0xff).
    pub xip_flash: bool,
    /// cpu0 released core 1: 0x10008 bit 3 (the stock firmware), or the first `|= 8` (run) on
    /// core 1's CON register 0x1EEE004 (M-VAVE's FM1 Open, after the newer AC79 SDK); latched
    /// until the runner starts cpu1, as firmwares hold the bit only while they wait for core 1
    /// to report in.
    pub cpu1_release: bool,
    /// core 1 was released once: a later run on 0x1EEE004 is the stock IPC's resume after a
    /// pause, not a release.
    cpu1_released_once: bool,
    /// FM1_AUDIO_TRACE: log each audio half-buffer (debugging the DMA's pace).
    audio_trace: bool,
    /// The CRC-16 unit's register (0x13504).
    crc: u16,
    /// The random number generator's state (JL_RAND, 0x13B00: R64L / R64H).
    rand: u64,
    /// The cores' hardware lock (`lockset` / `lockclr`): which core holds it.
    lock_owner: Option<u32>,
    /// FM1_GPIO_TRACE: GPIO register writes by address (debugging port use).
    pub gpio_writes: Option<std::collections::BTreeMap<u32, u64>>,
    unknown_log: Vec<UnknownAccess>,
    /// `--flaky-core1`: core 1's RAM loads misread now and then (flaky.rs); None = a good unit.
    pub flaky_core1: Option<flaky::FlakyCore1>,
    /// The power domain's analog registers.
    pub p33: p33::P33,
}

fn dbg_line(addr: u32) -> &'static str {
    match addr & !3 {
        0x1eee240 => "wr_en",
        0x1eee244 => "msg",
        0x1eee248 => "msg_clr",
        _ => "dbg",
    }
}

impl Soc {
    /// After an erase or page program: the XIP window shows the flash chip, also where the
    /// window's contents come from the package (`xip`, the app area as installed). A booted
    /// package's window reaches flash 0x93000, and April OS writes its samples from 0x74000
    /// and reads them back through XIP.
    fn sync_xip(&mut self) {
        let Some((a, b)) = self.flash.changed.take() else { return };
        if !self.xip_flash {
            return;
        }
        for o in a.max(XIP_FLASH_OFFSET)..b {
            match self.xip.get_mut(o - XIP_FLASH_OFFSET) {
                Some(x) => *x = self.flash.mem[o],
                None => break,
            }
        }
    }

    /// `ram_size` in bytes; `xip` = the app binary mapped at XIP_BASE.
    pub fn new(ram_size: usize, xip: Vec<u8>) -> Self {
        Self {
            board: Board::Fm1,
            bt_window: BT_WINDOW_BASE,
            xip,
            ram: Ram::new(ram_size),
            ovl: Ram::new(512 * 1024),
            sram2: Ram::new(256 * 1024),
            lcd: Lcd::new(),
            flash: SpiFlash::new(),
            console: Vec::new(),
            ticks: 0,
            periph: Periph::default(),
            keyvoice_watch: None,
            writer_probe: None,
            current_instruction_pc: 0,
            current_instruction_core: 0,
            pending_sync_jit_store: None,
            sfr: Default::default(),
            paused: [false; 2],
            lock_owner: None,
            crc: 0,
            rand: 0x9e37_79b9_7f4a_7c15,
            cpu1_release: false,
            cpu1_released_once: false,
            audio_trace: std::env::var_os("FM1_AUDIO_TRACE").is_some(),
            xip_flash: true,
            gpio_writes: std::env::var("FM1_GPIO_TRACE").ok().map(|_| Default::default()),
            unknown_log: Vec::new(),
            flaky_core1: None,
            p33: Default::default(),
        }
    }

    /// A load by core 1: what `read32` returns, unless a flaky core 1 misreads it (RAM only).
    pub fn core1_read32(&mut self, addr: u32) -> u32 {
        let v = self.read32(addr);
        self.core1_misread(addr, 4, v)
    }

    pub fn core1_read16(&mut self, addr: u32) -> u16 {
        let v = self.read16(addr);
        self.core1_misread(addr, 2, v as u32) as u16
    }

    pub fn core1_read8(&mut self, addr: u32) -> u8 {
        let v = self.read8(addr);
        self.core1_misread(addr, 1, v as u32) as u8
    }

    #[inline]
    fn core1_misread(&mut self, addr: u32, size: u32, v: u32) -> u32 {
        match self.flaky_core1.as_mut() {
            Some(f) if (addr.wrapping_sub(RAM_BASE) as usize) < self.ram.len() => f.load(addr, size, v),
            _ => v,
        }
    }

    /// Wire the chip into `board`'s panel (and its flash chip's id).
    pub fn set_board(&mut self, board: Board) {
        self.board = board;
        self.periph.board = board;
        if board == Board::Smk37 {
            self.flash.jedec = [0xeb, 0x60, 0x14];
        }
    }

    /// All unknown accesses so far — the peripheral bring-up TODO list.
    /// Advance the peripheral clock by `n` CPU cycles, moving any finished
    /// audio half out of RAM (int32 L/R holding a 24-bit sample in the low
    /// bits — Felucca writes Q15 << 7, audio.c OUT_SHIFT — so >> 8 to i16).
    pub fn advance(&mut self, n: u64) {
        let due = self.periph.advance(n);
        if let Some((at, b)) = due.uart_rx {
            self.write8(at, b);
        }
        if let Some((adr, words)) = due.audio_half {
            if self.audio_trace {
                eprintln!("half {} ms {}", self.periph.ms(), self.periph.cycles);
            }
            for i in 0..words {
                let w = self.read32(adr.wrapping_add(i * 4)) as i32;
                self.periph.audio.push((w >> 8).clamp(-32768, 32767) as i16);
            }
        }
        // Passive observation: no new guest writes, no clock or timing changes.
        if let Some(probe) = self.keyvoice_watch.as_mut() {
            let ms = self.periph.ms();
            if (1350..=1550).contains(&ms) {
                probe.checks += 1;
                let values = (self.ram.read8(0x48f0b),
                              self.ram.read8(0x1993f),
                              self.ram.read8(0x19941));
                if probe.prev != Some(values) && probe.transitions.len() < 128 {
                    probe.prev = Some(values);
                    let pending = self.periph.read(0x1eef0ec).unwrap_or(0) & 0x80 != 0;
                    probe.transitions.push((self.periph.cycles, ms,
                        self.periph.audio_halves, values.0, values.1, values.2, pending));
                }
            }
        }
    }

    /// Current guest instruction, not a scheduling-slice end PC.
    /// CPU1 calls this through Core1Bus, including its interpreted instructions.
    pub fn trace_core_instruction(&mut self, core: u8, pc: u32) {
        if self.writer_probe.is_some() {
            self.current_instruction_core=core;
            self.current_instruction_pc=pc;
            self.pending_sync_jit_store=None;
        }
    }

    /// JIT emits this callback before its inline RAM store; the reported PC
    /// is the guest instruction's PC, even when Rust's Bus::write* is bypassed.
    pub fn trace_core_store(&mut self, core: u8, pc: u32, addr: u32, width: u8, value: u32) {
        if self.writer_probe.is_none() { return; }
        self.current_instruction_core=core;
        self.current_instruction_pc=pc;
        self.observe_target_store(core,pc,addr,width,value,true);
    }

    #[inline]
    fn observe_target_store(&mut self, core: u8, pc: u32, addr: u32, width: u8, value: u32, from_jit: bool) {
        const TARGET: u32 = 0x01c1_993f;
        const ACK: u32 = 0x01c1_0984;
        if self.writer_probe.is_none() || width == 0 { return; }
        // Time is emulated device time. The 1343..1346 ms CPU0 wait is inside
        // this narrow window; other key-up probes retain their original window.
        let ack_hit = (1330..=1360).contains(&self.periph.ms())
            && addr <= ACK && ACK-addr < width as u32;
        if from_jit && ack_hit {
            self.pending_sync_jit_store=Some((core,pc,addr,width,value));
        } else if !from_jit {
            // h_guest_store is followed by h_write on the JIT slow path.
            // The helper must not create a second fictitious guest write.
            let duplicate=self.pending_sync_jit_store.take()==Some((core,pc,addr,width,value));
            if duplicate && ack_hit { return; }
        }
        if ack_hit {
            let before=self.ram.read8(ACK-RAM_BASE);
            let after=((value >> (8*(ACK-addr))) & 255) as u8;
            if let Some(p)=self.writer_probe.as_mut() {
                if p.sync_ack_writes.len()<8192 {
                    p.sync_ack_writes.push((self.periph.cycles,self.periph.audio_halves,
                        core,pc,addr,width,before,after,from_jit));
                } else {
                    p.sync_ack_dropped+=1;
                }
            }
        }
        if !(1380..=1540).contains(&self.periph.ms()) { return; }
        // IRQ 120..127 are software interrupts in the ILAT write register.
        // Capture the request/acknowledgement guest store PC through both the
        // interpreter and inline JIT paths, without reading or writing guest IO.
        if addr==0x1eef_1a0 || addr==0x1eef_1a4 {
            if value & (1<<7) != 0 {
                let row=(self.periph.cycles,self.periph.audio_halves,pc,addr,
                    width,value,self.periph.ilat,
                    self.ram.read8(0x48f0b),self.ram.read8(0x48ee9));
                if let Some(p)=self.writer_probe.as_mut() {
                    if p.irq127_writes.len()<384 { p.irq127_writes.push(row); }
                }
            }
        }
        let targets=[TARGET,0x01c4_8ee0,0x01c4_8ee9,0x01c4_8eea,
                     0x01c4_8f0b,0x01c4_8f22,0x01c2_b93b,0x01c6_a070];
        for &target in &targets {
            if addr>target || target-addr>=width as u32 { continue; }
            let shift=8*(target-addr);
            let after=((value>>shift)&0xff) as u8;
            let before=self.ram.read8(target-RAM_BASE);
            if before==after { continue; }
            if let Some(p)=self.writer_probe.as_mut() {
                let ev=(self.periph.cycles,self.periph.audio_halves,pc,addr,width,before,after);
                if target==TARGET {
                    if p.exact_stores.len()<40 { p.exact_stores.push(ev); }
                } else if p.other_stores.len()<250 { p.other_stores.push(ev); }
            }
        }
    }

    /// Observe only after an unmodified CPU scheduling slice; no emulated writes
    /// and no profile-on instrumentation. Disabled by default.
    pub fn observe_writer(&mut self, core: u32, pc: u32, irq_depth: u32) {
        if !(1380..=1540).contains(&self.periph.ms()) || self.writer_probe.is_none() {
            return;
        }
        let values=(self.ram.read8(0x48f0b),
                    self.ram.read8(0x1993f),
                    self.ram.read8(0x19941));
        if let Some(probe)=self.writer_probe.as_mut() {
            probe.checks+=1;
            if probe.last != Some(values) {
                if values.1 == 1 && probe.last.map(|x|x.1)!=Some(1) {
                    probe.voice_irq_context=probe.irq_recent.iter().copied().collect();
                }
                probe.last=Some(values);
                if probe.events.len()<64 {
                    probe.events.push((
                        self.periph.cycles,self.periph.ms(),self.periph.audio_halves,
                        core,pc,irq_depth,values.0,values.1,values.2
                    ));
                }
            }
        }
    }

    /// Record CPU0 IRQ entry at its existing interrupt dispatch point; no
    /// peripheral action and no change to interrupt timing.
    pub fn observe_irq_entry(&mut self, irq: u8, handler: u32, return_pc: u32) {
        if !(1380..=1540).contains(&self.periph.ms()) { return; }
        // RAM snapshot at IRQ11 entry, before the firmware receives the interrupt.
        if irq==11 && self.writer_probe.is_some() && (1400..=1510).contains(&self.periph.ms()) {
            fn dump(r:&Ram, start:u32, count:u32) -> String {
                use std::fmt::Write;
                let mut h=String::with_capacity(count as usize*2);
                for i in 0..count { let _=write!(h,"{:02x}",r.read8(start+i)); }
                h
            }
            let row=(self.periph.cycles,self.periph.audio_halves,
                self.periph.keys_down[21] as u8,
                dump(&self.ram,0x19900,0x80),dump(&self.ram,0x48ee0,0x90),
                dump(&self.ram,0x2b900,0x80),dump(&self.ram,0x6a060,0x30));
            if let Some(p)=self.writer_probe.as_mut() {
                if p.irq11_snapshots.len()<64 { p.irq11_snapshots.push(row); }
            }
        }
        if matches!(irq,3|5|11|127) && self.writer_probe.is_some()
          && (1395..=1505).contains(&self.periph.ms()) {
            // Read-only snapshot for task/IRQ correlation; no guest cycles.
            let row=(self.periph.cycles,self.periph.audio_halves,irq,handler,return_pc,
                     self.ram.read8(0x48f0b),self.ram.read8(0x48ee9),
                     self.ram.read8(0x1993f));
            if let Some(p)=self.writer_probe.as_mut() {
                if p.schedule_events.len()<1024 { p.schedule_events.push(row); }
            }
        }
        if let Some(p)=self.writer_probe.as_mut() {
            *p.irq_counts.entry(irq).or_default()+=1;
            if p.irq_recent.len()==64 { p.irq_recent.pop_front(); }
            p.irq_recent.push_back((self.periph.cycles,irq,handler,return_pc));
        }
    }

    /// The highest-priority enabled pending interrupt: (irq, prio).
    #[inline]
    pub fn pending_irq(&self) -> Option<(u8, u8)> {
        self.periph.pending_irq()
    }

    /// Core `core` (0, 1) is paused by the other through its CON register's bit 2
    /// (0x1EEE000 / 0x1EEE004): the stock firmware stops core 1 around flash work.
    pub fn core_paused(&self, core: u32) -> bool {
        core < 2 && self.paused[core as usize]
    }

    /// The highest-priority interrupt pending for core `core` (its own enable bank).
    pub fn pending_irq_for(&self, core: u32) -> Option<(u8, u8)> {
        self.periph.pending_irq_for(core)
    }

    pub fn unknown_accesses(&self) -> &[UnknownAccess] {
        &self.unknown_log
    }

    /// The debug console contents (DBG_MSG box writes).
    pub fn console_string(&self) -> String {
        String::from_utf8_lossy(&self.console).into_owned()
    }

    fn log_unknown(&mut self, addr: u32, width: u8, is_write: bool, value: u32) {
        self.unknown_log.push(UnknownAccess {
            addr,
            width,
            is_write,
            value,
        });
        // keep the last 8192..16384 (dropping one at a time shifted the whole log per access)
        if self.unknown_log.len() >= 16384 {
            self.unknown_log.drain(..8192);
        }
    }

    fn region(&self, addr: u32) -> Region {
        match addr {
            a if a >= XIP_BASE && (a - XIP_BASE) < self.xip.len() as u32 => Region::Xip,
            // past the loaded image the XIP window still shows the flash chip (the stock
            // firmware reads its USR preset area, which it writes over SPI, through XIP)
            a if self.xip_flash && a >= XIP_BASE && (a - XIP_BASE) as usize + XIP_FLASH_OFFSET < spiflash::FLASH_SIZE => Region::XipFlash,
            a if a >= RAM_BASE && (a - RAM_BASE) < self.ram.len() as u32 => Region::Ram,
            a if a >= OVL_BASE && (a - OVL_BASE) < self.ovl.len() as u32 => Region::Ovl,
            a if a >= SRAM2_BASE && (a - SRAM2_BASE) < self.sram2.len() as u32 => Region::Sram2,
            0x1eee000..=0x1eee0ff => Region::Irqc,
            0x1eef000..=0x1eef3ff => Region::Irqc2,
            0x12e00..=0x12e3f => Region::Alnk,
            0x50000..=0x501ff => Region::Gpio,
            0x51000..=0x5103f => Region::Iomap,
            0x10000..=0x1001f => Region::Clk,
            0x10400..=0x1091f => Region::Timer,
            0x11c00..=0x11c1f => Region::Spi0,
            0x11d00..=0x11d1f => Region::Spi1,
            0x11e00..=0x11e1f => Region::Spi2,
            0x11800..=0x1183f => Region::Usb,
            // the second USB PHY (the SMK-37's LED commons at 0x16A0C, its pads used as GPIO; its
            // stock firmware powers the PHY up at boot and waits for 0x16800 bit 4). The FM-1's
            // stock firmware touches the block too, as before: unknown.
            0x16800..=0x16a1f if self.board == Board::Smk37 => Region::Usb,
            0x12100..=0x1212f => Region::Uart1,
            0x13100..=0x1311f => Region::Adc,
            0x13500..=0x1350f => Region::Crc,
            0x13b00..=0x13b07 => Region::Rand,
            0x11900..=0x119ff => Region::Ana,
            0x13e08..=0x13e0f => Region::P33,
            0x20000..=0x2ffff => Region::Bt,
            0x1eee240..=0x1eee24f => Region::Dbg,
            _ => Region::Unknown,
        }
    }

    fn sfr_get(&mut self, addr: u32) -> u32 {
        *self.sfr.get(&addr).unwrap_or(&0)
    }

    fn sfr_set(&mut self, addr: u32, v: u32) {
        self.sfr.insert(addr, v);
    }

    /// SPI1/MMIO side effects on 32-bit writes.
    fn spi1_write(&mut self, addr: u32, value: u32) {
        match addr {
            0x11d00 => {
                // CON: bit14 clears the pending transfer-done (and its IRQ 16)
                if value & 0x4000 != 0 {
                    self.periph.spi1_pending = false;
                }
                let stored = self.sfr_get(addr);
                self.sfr_set(addr, (stored & !0x4000) | (value & !0x4000));
            }
            0x11d04 => self.sfr_set(addr, value), // BAUD
            0x11d08 => {
                // BUF: single byte, D/C = PC8 state (SMK-37: PB5; its group B is the pad LEDs)
                if let Some(dc) = self.lcd_dc() {
                    self.lcd.feed(value as u8, dc);
                }
                self.sfr_set(addr, value);
                self.spi1_done(1);
            }
            0x11d0c => self.sfr_set(addr, value), // ADR
            0x11d10 => {
                // CNT: DMA `value` bytes from RAM[ADR] through the panel
                let adr = self.sfr_get(0x11d0c);
                let n = value.min(0x40000);
                // the DMA source is a bus address (RAM, SRAM or XIP)
                let bytes: Vec<u8> = (0..n).map(|i| self.read8(adr.wrapping_add(i))).collect();
                match self.lcd_dc() {
                    Some(dc) => {
                        for b in bytes {
                            self.lcd.feed(b, dc);
                        }
                    }
                    None => self.periph.smk.pad_frame(&bytes),
                }
                self.sfr_set(addr, 0);
                self.spi1_done(n);
            }
            _ => self.sfr_set(addr, value),
        }
    }

    /// Where SPI1's bytes go: the LCD with its D/C pin's state (FM-1: PC8; SMK-37: PB5, while
    /// IOMAP_CON1 bit 4 picks pin group A), or None: the SMK-37's pad LEDs (group B).
    fn lcd_dc(&mut self) -> Option<bool> {
        match self.board {
            Board::Fm1 => Some(self.sfr_get(0x50080) & 0x100 != 0),
            Board::Smk37 => (self.sfr_get(0x51020) & 0x10 == 0).then(|| self.sfr_get(0x50040) & 0x20 != 0),
        }
    }

    /// SPI2 (0x11E00, CON/BAUD/BUF/ADR/CNT like SPI1): the stock firmware shifts the key
    /// matrix's column pattern into the two 74HC595s with it, one 2-byte DMA per column,
    /// driven by its IRQ 37 handler (which also reads the rows and pulses RCLK on PA1).
    fn spi2_write(&mut self, addr: u32, value: u32) {
        match addr {
            0x11e00 => {
                if value & 0x4000 != 0 {
                    self.periph.spi2_pending = false;
                }
                self.sfr_set(addr, value & !0xc000);
            }
            0x11e08 => {
                self.periph.sr_shift_byte(value as u8);
                self.sfr_set(addr, value);
                self.spi2_started(1);
            }
            0x11e10 => {
                let adr = self.sfr_get(0x11e0c);
                for i in 0..value.min(64) {
                    let b = self.read8(adr.wrapping_add(i));
                    self.periph.sr_shift_byte(b);
                }
                self.sfr_set(addr, 0);
                self.spi2_started(value);
            }
            _ => self.sfr_set(addr, value),
        }
    }

    fn spi2_started(&mut self, bytes: u32) {
        let con = self.sfr_get(0x11e00);
        let baud = self.sfr_get(0x11e04);
        self.periph.spi2_start(bytes, baud, con & 0x2000 != 0);
    }

    /// A SPI1 transfer finished (instantly here): with CON bit 13 (interrupt enable) that is
    /// IRQ 16, the stock LCD driver's DMA-done (its layer flush waits for the handler).
    /// (SMK-37: it takes the bytes' time on the wire, see `Periph::spi1_start`.)
    fn spi1_done(&mut self, bytes: u32) {
        let irq = self.sfr_get(0x11d00) & 0x2000 != 0;
        if self.board == Board::Smk37 {
            let baud = self.sfr_get(0x11d04);
            self.periph.spi1_start(bytes, baud, irq);
        } else if irq {
            self.periph.spi1_pending = true;
        }
    }

    fn timer_read(&mut self, addr: u32) -> u32 {
        // "time" base ticks so timeout/wait loops make progress; count
        // registers report a moving value, the rest stored bits.
        self.ticks = self.ticks.wrapping_add(1);
        if addr & 0xff == 0x04 {
            let t = (self.ticks * 7) as u32;
            return t;
        }
        self.sfr_get(addr)
    }
}

impl Bus for Soc {
    #[inline(always)]
    fn trace_instruction_pc(&mut self, pc: u32) {
        self.trace_core_instruction(0,pc);
    }
    #[inline(always)]
    fn trace_guest_store(&mut self, pc: u32, addr: u32, width: u8, value: u32) {
        self.trace_core_store(0,pc,addr,width,value);
    }
    fn irq_window(&mut self) {
        if self.periph.any_pending() {
            self.periph.next_due = 0;
        }
    }

    fn idle(&mut self, core: u32) {
        if core == 0 {
            self.periph.idle();
        }
    }

    fn hw_lock(&mut self, core: u32, set: bool) -> bool {
        match (set, self.lock_owner) {
            (true, Some(c)) if c != core => false,
            (true, _) => {
                self.lock_owner = Some(core);
                true
            }
            (false, Some(c)) if c == core => {
                self.lock_owner = None;
                true
            }
            (false, _) => true,
        }
    }

    #[inline(always)]
    fn tick(&mut self) -> bool {
        self.periph.tick()
    }
    #[inline(always)]
    fn irq_pending(&self) -> bool {
        self.periph.any_pending()
    }
    fn jit_mem(&mut self) -> Option<fm1_core::JitMem> {
        Some(fm1_core::JitMem {
            ram: self.ram.as_mut_ptr(),
            ram_base: RAM_BASE,
            ram_len: self.ram.len() as u32,
            ram_code: self.ram.code_ptr(),
            xip: self.xip.as_ptr(),
            xip_base: XIP_BASE,
            xip_len: self.xip.len() as u32,
        })
    }
    fn code_writes(&self) -> Option<u64> {
        Some(self.ram.code_writes)
    }
    fn code_mark(&mut self, lo: u32, hi: u32) {
        self.ram.mark_code(lo.wrapping_sub(RAM_BASE), hi.wrapping_sub(RAM_BASE));
    }
    #[inline]
    fn tick_room(&self) -> u64 {
        self.periph.tick_room()
    }
    #[inline]
    fn add_ticks(&mut self, n: u64) {
        self.periph.cycles += n;
    }
    #[inline]
    fn next_tick_due(&self) -> bool {
        self.periph.next_tick_due()
    }

    // RAM fast paths: same results as the region dispatch below (byte and
    // halfword accesses select within the aligned word), without walking it

    #[inline(always)]
    fn read8(&mut self, addr: u32) -> u8 {
        let o = addr.wrapping_sub(RAM_BASE);
        if (o as usize) < self.ram.len() {
            return self.ram.read8(o);
        }
        self.read32(addr & !3).to_le_bytes()[(addr & 3) as usize]
    }

    #[inline(always)]
    fn read16(&mut self, addr: u32) -> u16 {
        // halfwords sit at offsets 0 and 2 of the word (the old `>> 8` for
        // offset 2 returned bytes 1-2 and sheared every 16-bit pixel canvas)
        let v = self.read32(addr & !3);
        (v >> ((addr & 2) * 8)) as u16
    }

    #[inline(always)]
    fn read32(&mut self, addr: u32) -> u32 {
        let o = addr.wrapping_sub(RAM_BASE) as usize;
        if o + 4 <= self.ram.len() {
            return self.ram.read32(o as u32);
        }
        let x = addr.wrapping_sub(XIP_BASE) as usize;
        if x + 4 <= self.xip.len() {
            return u32::from_le_bytes([self.xip[x], self.xip[x + 1], self.xip[x + 2], self.xip[x + 3]]);
        }
        self.read32_slow(addr)
    }

    #[inline(always)]
    fn write8(&mut self, addr: u32, value: u8) {
        if self.writer_probe.is_some() { self.observe_target_store(self.current_instruction_core,self.current_instruction_pc,addr,1,value as u32,false); }
        let o = addr.wrapping_sub(RAM_BASE);
        if (o as usize) < self.ram.len() {
            return self.ram.write8(o, value);
        }
        self.write8_slow(addr, value)
    }

    #[inline(always)]
    fn write16(&mut self, addr: u32, value: u16) {
        if self.writer_probe.is_some() { self.observe_target_store(self.current_instruction_core,self.current_instruction_pc,addr,2,value as u32,false); }
        // merged at (addr & 2) within the aligned word, as the slow path does
        let o = (addr & !1).wrapping_sub(RAM_BASE) as usize;
        if o + 2 <= self.ram.len() && addr & 1 == 0 {
            return self.ram.write16(o as u32, value);
        }
        self.write16_slow(addr, value)
    }

    #[inline(always)]
    fn write32(&mut self, addr: u32, value: u32) {
        if self.writer_probe.is_some() { self.observe_target_store(self.current_instruction_core,self.current_instruction_pc,addr,4,value as u32,false); }
        let o = addr.wrapping_sub(RAM_BASE) as usize;
        if o + 4 <= self.ram.len() {
            return self.ram.write32(o as u32, value);
        }
        self.write32_slow(addr, value)
    }
}

impl Soc {
    #[inline(never)]
    fn read32_slow(&mut self, addr: u32) -> u32 {
        match self.region(addr) {
            Region::Xip => {
                let o = (addr - XIP_BASE) as usize;
                let g = |i: usize| self.xip.get(i).copied().unwrap_or(0);
                u32::from_le_bytes([g(o), g(o + 1), g(o + 2), g(o + 3)])
            }
            Region::Ram => self.ram.read32(addr - RAM_BASE),
            Region::XipFlash => {
                let o = (addr - XIP_BASE) as usize + XIP_FLASH_OFFSET;
                let g = |i: usize| self.flash.mem.get(i).copied().unwrap_or(0xff);
                u32::from_le_bytes([g(o), g(o + 1), g(o + 2), g(o + 3)])
            }
            Region::Ovl => self.ovl.read32(addr - OVL_BASE),
            Region::Sram2 => self.sram2.read32(addr - SRAM2_BASE),
            Region::Irqc => {
                // 0x1eee008 bit 14: controller ready (the early init spins on it);
                // 0x1eee000 / 0x1eee004 (C0_CON / C1_CON): see `core_paused`
                let v = self.sfr_get(addr);
                match addr {
                    0x1eee008 => v | 0x4000,
                    0x1eee000 | 0x1eee004 => {
                        let core = ((addr >> 2) & 1) as usize;
                        (v & !0x14) | if self.paused[core] { 0x10 } else { 0 }
                    }
                    _ => v,
                }
            }
            // (the second USB PHY ready: bit 4 of its control word, once it is powered up)
            Region::Usb if addr == 0x16800 => self.sfr_get(addr) | 0x10,
            Region::Iomap | Region::Usb | Region::Clk => self.sfr_get(addr),
            // JL_ANA (analog: WLA, DAC trim). 0x11978 is the DAC trim measurement after the
            // strobe at the same word: bit 5 = conversion done, bits 8-15 = the value (mid
            // scale here), bit 18 = "this trim step is right". With these the stock
            // firmware's audio_ana calibration finishes at once instead of polling forever
            // (a trim only nudges the DAC's DC offset).
            Region::Ana => {
                let v = self.sfr_get(addr);
                if addr == 0x11978 { (v & !0xff00) | 0x4_0000 | 0x8000 | 0x20 } else { v }
            }
            // the Bluetooth baseband (bsfr 0x20000; no radio here): reads 0, writes are
            // dropped (self-clearing requests like bt_clkn_compare_arm's capture at 0x2001C
            // must read done), except 0x2FC44, the base of the RAM window its buffers live in,
            // which the BT init writes (its .bd_base, which opens the BT bss, SDK
            // btctler_lib_bss.ld). The stock BT stack checks buffers against it: descriptors
            // within 2 KiB and below its own .bd_base + 1088, bulk buffers within 32 KiB; with
            // V13's base kept, the SMK-37 firmware's check failed and it reset.
            Region::Bt => {
                if addr == 0x2fc44 { self.bt_window } else { 0 }
            }
            Region::Gpio | Region::Adc | Region::Alnk | Region::Irqc2 | Region::Uart1 => {
                match self.periph.read(addr) {
                    Some(v) => v,
                    None => self.sfr_get(addr),
                }
            }
            Region::Timer => {
                match self.periph.read(addr) {
                    Some(v) => v,
                    None => self.timer_read(addr),
                }
            }
            Region::Spi0 => self.flash.read(addr),
            // SPI2: transfers finish at once (CON bit 15 reads done)
            Region::Spi2 => self.sfr_get(addr) | if addr == 0x11e00 { 0x8000 } else { 0 },
            Region::Spi1 => {
                if addr == 0x11d00 {
                    // CON: transfer-done (the FM-1: always, so polls finish; the SMK-37: once the
                    // bytes have gone out)
                    let busy = self.board == Board::Smk37 && self.periph.cycles < self.periph.spi1_done_at;
                    self.sfr_get(addr) | if busy { 0 } else { 0x8000 }
                } else if addr == 0x11d10 {
                    self.sfr_get(addr)
                } else {
                    self.sfr_get(addr)
                }
            }
            Region::Dbg => self.sfr_get(addr),
            Region::Crc => if addr == 0x13504 { self.crc as u32 } else { 0 },
            // JL_RAND (0x13B00 R64L, 0x13B04 R64H): a new number at every read, from a fixed
            // seed so runs repeat. Read as 0 it hung the stock firmware ~8 s after boot: a
            // routine in its audio driver parks the task when a random word equals a fixed
            // descrambled one, which real hardware never hits.
            Region::Rand => {
                let mut x = self.rand;
                x ^= x << 13;
                x ^= x >> 7;
                x ^= x << 17;
                self.rand = x;
                (if addr == 0x13b00 { x } else { x >> 32 }) as u32
            }
            Region::P33 => self.p33.read(addr),
            Region::Unknown => {
                self.log_unknown(addr, 4, false, 0);
                0
            }
        }
    }

    #[inline(never)]
    fn write8_slow(&mut self, addr: u32, value: u8) {
        let cur = self.read32(addr & !3);
        let shift = (addr & 3) * 8;
        let mask = !(0xffu32 << shift);
        let merged = (cur & mask) | ((value as u32) << shift);
        self.write32(addr & !3, merged);
    }

    #[inline(never)]
    fn write16_slow(&mut self, addr: u32, value: u16) {
        let cur = self.read32(addr & !3);
        let shift = (addr & 2) * 8;
        let mask = !(0xffffu32 << shift);
        let merged = (cur & mask) | ((value as u32) << shift);
        self.write32(addr & !3, merged);
    }

    #[inline(never)]
    fn write32_slow(&mut self, addr: u32, value: u32) {
        match self.region(addr) {
            Region::Xip | Region::XipFlash => self.log_unknown(addr, 4, true, value), // flash writes go via the ROM
            Region::Ram => self.ram.write32(addr - RAM_BASE, value),
            Region::Ovl => self.ovl.write32(addr - OVL_BASE, value),
            Region::Sram2 => self.sram2.write32(addr - SRAM2_BASE, value),
            Region::Irqc => {
                if addr == 0x1eee000 || addr == 0x1eee004 {
                    // C0_CON / C1_CON: writing bit 2 pauses that core (bit 4 reads "paused");
                    // a write with bit 3 and without bit 2 runs it again. Both are pulses:
                    // the stock IPC pauses with `|= 4` and resumes with `|= 8` on the same word.
                    let core = ((addr >> 2) & 1) as usize;
                    if value & 4 != 0 {
                        self.paused[core] = true;
                    } else if value & 8 != 0 {
                        self.paused[core] = false;
                        if core == 1 && !self.cpu1_released_once {
                            // M-VAVE's FM1 Open SDK releases core 1 here (C1_CON |= 8), not at 0x10008
                            // (once: the stock firmware's IPC resumes core 1 the same way)
                            self.cpu1_released_once = true;
                            self.cpu1_release = true;
                            self.periph.next_due = 0;
                        }
                    }
                    self.sfr_set(addr, value & !0x14);
                } else {
                    self.sfr_set(addr, value);
                }
            }
            Region::Gpio => {
                if let Some(h) = self.gpio_writes.as_mut() {
                    *h.entry(addr).or_insert(0) += 1;
                }
                // PD0 drives the flash chip select; PA1/PA3/PA4 clock the
                // key-matrix shift registers
                if addr == 0x500c0 {
                    self.flash.set_cs(value & 1 == 0);
                    self.sync_xip();
                }
                self.periph.write(addr, value);
                self.sfr_set(addr, value)
            }
            Region::Alnk | Region::Irqc2 => {
                if !self.periph.write(addr, value) {
                    self.sfr_set(addr, value);
                }
            }
            Region::Spi0 => {
                self.flash.write(addr, value);
                self.sync_xip();
            }
            Region::Iomap => self.sfr_set(addr, value),
            Region::Ana => self.sfr_set(addr, value),
            Region::P33 => self.p33.write(addr, value),
            Region::Bt => {
                if addr == 0x2fc44 {
                    self.bt_window = value;
                }
            }
            Region::Clk => {
                if addr == 0x10008 && value & 8 != 0 && self.sfr_get(addr) & 8 == 0 {
                    self.cpu1_released_once = true;
                    self.cpu1_release = true;
                    self.periph.next_due = 0; // the runner looks at it before the next instruction
                }
                self.sfr_set(addr, value)
            }
            Region::Usb => {
                if addr == 0x16a0c && self.board == Board::Smk37 {
                    self.periph.smk.commons = value;
                }
                self.sfr_set(addr, value)
            }
            Region::Uart1 => {
                if !self.periph.write(addr, value) {
                    self.sfr_set(addr, value);
                }
            }
            Region::Adc => {
                if !self.periph.write(addr, value) {
                    self.sfr_set(addr, value);
                }
            }
            Region::Timer => {
                if !self.periph.write(addr, value) {
                    self.sfr_set(addr, value);
                }
            }
            Region::Spi1 => self.spi1_write(addr, value),
            Region::Spi2 => self.spi2_write(addr, value),
            // the CRC-16 unit (chip_crc16): [+4] = the register (the SDK seeds it with 0),
            // each write to [+0] feeds one byte through CRC-16/CCITT (0x1021, MSB first).
            // The stock NOR file system checks every directory entry with it.
            Region::Rand => {}
            Region::Crc => match addr {
                0x13500 => {
                    let mut c = self.crc ^ ((value as u16 & 0xff) << 8);
                    for _ in 0..8 {
                        c = if c & 0x8000 != 0 { (c << 1) ^ 0x1021 } else { c << 1 };
                    }
                    self.crc = c;
                }
                0x13504 => self.crc = value as u16,
                _ => {}
            },
            Region::Dbg => {
                match dbg_line(addr) {
                    "msg" => {
                        self.console.extend_from_slice(&value.to_le_bytes());
                    }
                    _ => {}
                }
                self.sfr_set(addr, value);
            }
            Region::Unknown => self.log_unknown(addr, 4, true, value),
        }
    }
}

/// M-VAVE's stock firmware out of its update package: the XIP window's contents (the app
/// area, unscrambled), the whole flash (the image as written, grown to the chip's size, the
/// USR patch area given this emulator's default bank when blank and then an optional DX7
/// bank in slots 1-32) and the entry point.
pub struct Stock {
    pub xip: Vec<u8>,
    pub flash: Vec<u8>,
    pub entry: u32,
    /// The board the package is for (its identity), with its identity.
    pub board: Board,
    pub identity: String,
    /// FM-1 user bank, if this package has one.
    pub usr: Option<usize>,
}

pub fn stock_from_package(pkg: &[u8], syx: Option<&[u8]>) -> Result<Stock, String> {
    let u = fwsc::unpack(pkg)?;
    let board = Board::of_identity(&u.identity);
    let mut flash = fwsc::full_flash(&u.raw, FLASH_SIZE);
    if board == Board::Smk37 {
        // a unit's factory calibration record, with the stock defaults
        fwsc::smk_trim_fill_defaults(&mut flash);
    }
    if let Some(usr) = fwsc::usr_offset(&u).filter(|_| board == Board::Fm1) {
        fwsc::usr_fill_defaults(&mut flash, usr);
        if let Some(b) = syx {
            fwsc::usr_load_syx(&mut flash, usr, b, 0)?;
        }
    }
    let app = u.entry("app.bin").map(|h| h.offset).unwrap_or(0x120);
    let usr = fwsc::usr_offset(&u).filter(|_| board == Board::Fm1);
    Ok(Stock { xip: u.xip, flash, entry: XIP_BASE + app as u32, board, identity: u.identity, usr })
}

/// Ready a Soc for a package's firmware: its board, its flash chip, and the SPL's boot
/// parameters at `params`. Returns the value for r0.
pub fn stock_boot(soc: &mut Soc, flash: &[u8], params: u32, board: Board) -> u32 {
    soc.set_board(board);
    soc.flash.load(flash);
    soc.xip_flash = true;
    write_boot_info(soc, params, flash)
}

/// The boot-parameter block the SPL (uboot.boot) hands the stock app in r0, as the SDK's
/// `BOOT_DEVICE_INFO` (include_lib/system/boot.h) and the SPL's own code at 0x31B2..0x3200
/// build it: fs_info (-> the flash header copied right after the struct), sfc_base_addr (the
/// flash offset behind XIP 0x02000000: 0x4000), app_addr 0x02000000, chip_id, trim_value, an
/// 8-byte MAC, then the 32-byte flash header unmasked (CRC-16 keystream from 0xFFFF; its CRC
/// checks). The app copies parts of it to 0x01C7FD50 (boot_hwinfo_save) and its NOR file
/// system finds the flash from sfc_base_addr. Writes the block at `at` (RAM); returns `at`.
pub fn write_boot_info(soc: &mut Soc, at: u32, flash: &[u8]) -> u32 {
    let mut head = [0u8; 32];
    head.copy_from_slice(&flash[..32]);
    let mut key: u16 = 0xffff;
    for b in head.iter_mut() {
        *b ^= key as u8;
        key = (key << 1) ^ if key & 0x8000 != 0 { 0x1021 } else { 0 };
    }
    let words = [at + 24, 0x4000, XIP_BASE, 0, 0, 0];
    for (i, w) in words.iter().enumerate() {
        soc.write32(at + 4 * i as u32, *w);
    }
    for (i, b) in head.iter().enumerate() {
        soc.write8(at + 24 + i as u32, *b);
    }
    at
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sync_ack_catches_cpu0_cpu1_and_jit_without_double_counting() {
        const ACK: u32 = 0x01c1_0984;
        let mut soc=Soc::new(1<<20, vec![]);
        soc.periph.hz=200_000_000;
        soc.periph.cycles=soc.periph.cycle_of_ms(1343);
        soc.writer_probe=Some(CoreWriterProbe::default());

        soc.trace_core_instruction(0,0x01c0_b9fa);
        soc.write8(ACK,0);
        soc.trace_core_instruction(1,0x01c0_bd26);
        soc.write8(ACK,1);
        // Simulate the JIT pre-store callback plus the Rust slow-path write:
        // one actual guest instruction must yield exactly one event.
        soc.trace_core_store(1,0x01c0_bd30,ACK,1,0);
        soc.write8(ACK,0);
        // Inline JIT's direct RAM write bypasses Soc::write8 altogether.
        soc.trace_core_store(1,0x01c0_bd32,ACK,1,3);
        soc.ram.write8(ACK-RAM_BASE,3);

        let p=soc.writer_probe.as_ref().unwrap();
        assert_eq!(p.sync_ack_writes.len(),4);
        assert_eq!(p.sync_ack_dropped,0);
        assert_eq!((p.sync_ack_writes[0].2,p.sync_ack_writes[0].3), (0,0x01c0_b9fa));
        assert_eq!((p.sync_ack_writes[1].2,p.sync_ack_writes[1].3), (1,0x01c0_bd26));
        assert_eq!((p.sync_ack_writes[2].6,p.sync_ack_writes[2].7),(1,0));
        assert_eq!((p.sync_ack_writes[3].6,p.sync_ack_writes[3].7),(0,3));
        assert!(p.sync_ack_writes[3].8);
    }

    #[test]
    fn flash_writes_show_through_xip() {
        // a booted package's window (0x80000 bytes, flash 0x4000..0x84000): erasing the sector
        // at flash 0x74000 and programming two bytes there reads back through XIP 0x02070000,
        // as April OS's samples do
        let mut soc = Soc::new(1 << 16, vec![0xaa; 0x80000]);
        for cmd in [&[0x06][..], &[0x20, 0x07, 0x40, 0x00], &[0x06], &[0x02, 0x07, 0x40, 0x00, 0x12, 0x34]] {
            soc.write32(0x500c0, 0); // PD0 low: chip select
            for &b in cmd {
                soc.write32(spiflash::SPI0_BASE + 8, b as u32);
            }
            soc.write32(0x500c0, 1);
        }
        assert_eq!(soc.read32(0x0207_0000), 0xffff_3412);
        assert_eq!(soc.read32(0x0207_0ffc), 0xffff_ffff, "the rest of the sector erased");
        assert_eq!(soc.read32(0x0207_1000), 0xaaaa_aaaa, "the next sector as installed");
        assert_eq!(soc.flash.revision, 2, "erase and program persist even after XIP consumes changed");
        assert!(!soc.flash.busy());
    }
}
