//! Native snapshot: direct RAM reads, no MMIO and no guest writes.
//! Disk I/O happens only on request, exit, or halt; capture pauses emulation.
use crate::Machine;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

pub fn quote(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c < ' ' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}
pub fn base64(bytes: &[u8]) -> String {
    const A: &[u8;64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut s = String::with_capacity((bytes.len()+2)/3*4);
    for b in bytes.chunks(3) {
        let n = ((b[0] as u32)<<16) | ((b.get(1).copied().unwrap_or(0) as u32)<<8) | b.get(2).copied().unwrap_or(0) as u32;
        s.push(A[((n>>18)&63) as usize] as char);
        s.push(A[((n>>12)&63) as usize] as char);
        s.push(if b.len()>1 { A[((n>>6)&63) as usize] as char } else { '=' });
        s.push(if b.len()>2 { A[(n&63) as usize] as char } else { '=' });
    }
    s
}
fn cpu(c: &fm1_core::Cpu) -> String {
    format!("{{\"pc\":{},\"sp\":{},\"ssp\":{},\"usp\":{},\"core_id\":{},\"user\":{},\"insn_count\":{},\"rets\":{},\"regs\":{:?},\"stuck_on\":{}}}",
        c.pc,c.sp,c.ssp,c.usp,c.core_id,c.user,c.insn_count,c.rets,c.regs,
        c.stuck_on.map(quote).unwrap_or_else(|| "null".into()))
}
pub fn directory() -> PathBuf {
    std::env::var_os("FM1_BLACKBOX_DIR").map(PathBuf::from).unwrap_or_else(|| {
        let mut p=std::env::var_os("HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("."));
        p.push("Desktop"); p.push("FM1_BLACKBOX"); p
    })
}
pub fn capture(m: &Machine, firmware: &str, trigger: &str, reason: Option<&str>, underruns: u64, dir: &Path) -> std::io::Result<PathBuf> {
    std::fs::create_dir_all(dir)?;
    let stamp=SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis();
    // Direct reads preserve pending IRQ/peripheral flags.
    let ram:Vec<u8>=(0..m.soc.ram.len()).map(|i|m.soc.ram.read8(i as u32)).collect();
    let encoded=base64(&ram);
    let c1=m.cpu1.as_ref().map(cpu).unwrap_or_else(||"null".into());
    let json=format!("{{\"format\":\"FM1-NATIVE-BLACKBOX-v1\",\"build\":{},\"firmwarePath\":{},\"capturedUnixMs\":{},\"clockMHz\":{},\"trigger\":{},\"capturePausesEmulation\":true,\"hostAudioUnderruns\":{},\"ram_base\":\"0x01c00000\",\"ram_encoding\":\"base64\",\"ram_bytes\":{},\"ram_base64\":{},\"emulator\":{{\"halted\":{},\"reason\":{},\"ms\":{},\"cycles\":{},\"audio_halves\":{},\"cpu0\":{},\"cpu1\":{}}}}}\n",
        quote(option_env!("FM1_LAB_BUILD").unwrap_or("local-build")),quote(firmware),stamp,
        m.soc.periph.hz/1_000_000,quote(trigger),underruns,ram.len(),quote(&encoded),
        reason.is_some(),quote(reason.unwrap_or("")),m.soc.periph.ms(),m.soc.periph.cycles,
        m.soc.periph.audio_halves,cpu(&m.cpu),c1);
    let access_events = m.soc.groove_mem_events.iter().map(|e| {
        format!(r#"{"cycle":{},"core":{},"pc":{},"addr":{},"width":{},"write":{}}"#,
            e.cycle, e.core, e.pc, e.addr, e.width, e.write)
    }).collect::<Vec<_>>().join(",");
    let access_report = format!(
        r#"{"enabled":{},"regionNames":["scratch","pattern","undo","fm1_fx_states"],"counts":{:?},"events":[{}]}"#,
        m.soc.groove_mem_watch, m.soc.groove_mem_counts, access_events
    );
    let mut json = json;
    if let Some(end) = json.rfind('}') {
        json.insert_str(end, &format!(r#","grooveMem":{}"#, access_report));
    }
    let stem=format!("FM1_BLACKBOX_{stamp}_{trigger}");
    let path=dir.join(format!("{stem}.json"));
    let temp=dir.join(format!("{stem}.tmp"));
    std::fs::write(&temp,json)?;
    std::fs::rename(temp,&path)?;
    Ok(path)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn base64_vectors() {
        for (raw,want) in [(b"".as_slice(),""),(b"f","Zg=="),(b"fo","Zm8="),(b"foo","Zm9v"),(b"foobar","Zm9vYmFy")] {
            assert_eq!(base64(raw),want);
        }
    }
    #[test] fn json_strings() {
        assert_eq!(quote("a\"\\\n\t\u{1}"), "\"a\\\"\\\\\\n\\t\\u0001\"");
        assert_eq!(quote("sí"), "\"sí\"");
    }

    #[test] fn capture_preserves_machine_and_exports_ram() {
        let mut m=crate::Machine {
            cpu:fm1_core::Cpu::new(0x01c00010),
            cpu1:Some(fm1_core::Cpu::new(0x01c00020)),
            soc:fm1_soc::Soc::new(64,vec![0;4]),
            skip_log:None,blocks:true,pending_tick:false,watch_call:None,watch_hits:0,
        };
        m.soc.ram.write32(0,0x12345678);
        let before=(m.cpu.pc,m.soc.periph.cycles,m.soc.ram.read32(0));
        let dir=std::env::temp_dir().join(format!("fm1-blackbox-test-{}",std::process::id()));
        let p=capture(&m,"test.fwsc","halt",Some("test reason"),7,&dir).unwrap();
        let json=std::fs::read_to_string(&p).unwrap();
        assert!(json.contains("\"halted\":true"));
        assert!(json.contains("\"hostAudioUnderruns\":7"));
        assert_eq!(before,(m.cpu.pc,m.soc.periph.cycles,m.soc.ram.read32(0)));
        if let Some(out)=std::env::var_os("FM1_BLACKBOX_TEST_OUTPUT") { std::fs::copy(&p,out).unwrap(); }
        std::fs::remove_dir_all(dir).unwrap();
    }
}
