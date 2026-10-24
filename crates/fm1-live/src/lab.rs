//! Host-only controls and PCM recording. Never write files from the audio callback.
use std::io::{self, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::sync::mpsc::{self, SyncSender, TrySendError};
use std::thread::JoinHandle;
use std::time::{SystemTime, UNIX_EPOCH};

pub const BAR_H: usize = 100;
pub const CLOCKS: &[u64] = &[80, 100, 120, 160, 192, 200, 240, 320];
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Button { Open, ClockDown, ClockUp, ApplyClock, Json, Record, Folder }
pub fn hit(x: f32, y: f32) -> Option<Button> {
    if !(8.0..46.0).contains(&y) { return None; }
    [(12.0,182.0,Button::Open),(202.0,242.0,Button::ClockDown),
     (358.0,398.0,Button::ClockUp),(410.0,590.0,Button::ApplyClock),
     (602.0,796.0,Button::Json),(808.0,1040.0,Button::Record),
     (1052.0,1268.0,Button::Folder)].into_iter().find(|(a,b,_)| x>=*a && x<*b).map(|(_,_,b)| b)
}
pub fn next_clock(current: u64, up: bool) -> u64 {
    if up { CLOCKS.iter().copied().find(|&v|v>current).unwrap_or(current) }
    else { CLOCKS.iter().rev().copied().find(|&v|v<current).unwrap_or(current) }
}
#[derive(Clone)]
pub struct View {
    pub generation: u64,
    pub pot: u16,
    pub firmware: String,
    pub mhz: u64,
    pub recording: bool,
    pub message: String,
}
pub enum Command { Load(String,u64), Clock(u64), Snapshot, Record }

pub fn draw(buf: &mut [u32], v: &View, selected: u64) {
    use crate::panel::{canvas,rrect,text,W};
    canvas(W);
    buf[..W*BAR_H].fill(0x151c28);
    for (x,w,label,color) in [
        (12.,170.,"ABRIR FWSC",0x3260a0),
        (202.,40.,"-",0x38485e), (358.,40.,"+",0x38485e),
        (410.,180.,"APLICAR MHZ",0x38485e),
        (602.,194.,"EXPORTAR JSON",0x38665d),
        (808.,232.,if v.recording {"DETENER WAV"} else {"GRABAR WAV"},if v.recording {0xa03e4e} else {0x654a76}),
        (1052.,216.,"VER ARCHIVOS",0x38485e),
    ] {
        rrect(buf,x,8.,w,38.,7.,color,color);
        text(buf,x+w/2.,20.,label,2,0xf1f4fa);
    }
    text(buf,300.,20.,&format!("{selected}"),2,0xffd16d);
    let fw=std::path::Path::new(&v.firmware).file_name().unwrap_or_default().to_string_lossy();
    let fw:String=fw.chars().take(80).collect();
    text(buf,640.,55.,&format!("{} MHz / {}",v.mhz,fw),1,0xd4dfef);
    let msg:String=v.message.chars().take(190).collect();
    text(buf,640.,76.,&msg,1,0x9fbcce);
}

/// Platform picker, running off the UI thread. No shell interpolation of paths.
#[cfg(target_os="macos")]
pub fn pick_firmware() -> Result<Option<String>,String> {
    let out=std::process::Command::new("/usr/bin/osascript").args(["-e",
        "try\nreturn POSIX path of (choose file with prompt \"Elegí otro firmware .fwsc\")\non error number -128\nreturn \"\"\nend try"]).output().map_err(|e|e.to_string())?;
    if !out.status.success() { return Err(String::from_utf8_lossy(&out.stderr).into_owned()); }
    let path=String::from_utf8(out.stdout).map_err(|e|e.to_string())?;
    // osascript appends one newline; retain spaces in valid file paths.
    let path=path.strip_suffix('\n').unwrap_or(&path).to_owned();
    if path.is_empty() { Ok(None) } else { Ok(Some(path)) }
}
#[cfg(not(target_os="macos"))]
pub fn pick_firmware() -> Result<Option<String>,String> { Err("Selector disponible en macOS".into()) }
pub fn open_folder(path: &Path) -> io::Result<()> {
    std::fs::create_dir_all(path)?;
    #[cfg(target_os="macos")]
    { std::process::Command::new("/usr/bin/open").arg(path).spawn()?; }
    Ok(())
}

/// PCM16 stereo, 44100 Hz. Worker owns the WAV file and repairs its header on stop.
/// A bounded queue stops recording explicitly on disk backpressure (never drops PCM silently).
pub struct Recorder { tx: Option<SyncSender<Vec<i16>>>, worker: Option<JoinHandle<io::Result<u64>>>, pub path: PathBuf }
fn header(bytes: u32) -> [u8;44] {
    let mut h=[0;44];
    h[0..4].copy_from_slice(b"RIFF"); h[4..8].copy_from_slice(&(36+bytes).to_le_bytes());
    h[8..16].copy_from_slice(b"WAVEfmt "); h[16..20].copy_from_slice(&16u32.to_le_bytes());
    h[20..22].copy_from_slice(&1u16.to_le_bytes()); h[22..24].copy_from_slice(&2u16.to_le_bytes());
    h[24..28].copy_from_slice(&44100u32.to_le_bytes()); h[28..32].copy_from_slice(&176400u32.to_le_bytes());
    h[32..34].copy_from_slice(&4u16.to_le_bytes()); h[34..36].copy_from_slice(&16u16.to_le_bytes());
    h[36..40].copy_from_slice(b"data"); h[40..44].copy_from_slice(&bytes.to_le_bytes()); h
}
impl Recorder {
    pub fn start(dir: &Path) -> io::Result<Self> {
        std::fs::create_dir_all(dir)?;
        let n=SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_nanos();
        Self::at(dir.join(format!("FM1_AUDIO_{n}.wav")))
    }
    fn at(path: PathBuf) -> io::Result<Self> {
        let mut f=std::fs::OpenOptions::new().write(true).create_new(true).open(&path)?;
        f.write_all(&header(0))?;
        let (tx,rx)=mpsc::sync_channel::<Vec<i16>>(256);
        let worker=std::thread::spawn(move || {
            let mut total=0u32;
            let result=(|| -> io::Result<()> {
                let mut bytes=Vec::new();
                while let Ok(samples)=rx.recv() {
                    if samples.len()%2!=0 { return Err(io::Error::new(io::ErrorKind::InvalidData,"PCM stereo incompleto")); }
                    let count=u32::try_from(samples.len().saturating_mul(2)).map_err(|_|io::Error::other("WAV demasiado grande"))?;
                    let next=total.checked_add(count).filter(|&v|v<=u32::MAX-36).ok_or_else(||io::Error::other("Limite de 4 GB WAV alcanzado"))?;
                    bytes.clear();
                    bytes.extend(samples.iter().flat_map(|s|s.to_le_bytes()));
                    f.write_all(&bytes)?;
                    total=next;
                }
                Ok(())
            })();
            f.seek(SeekFrom::Start(0))?; f.write_all(&header(total))?; f.flush()?;
            result?; Ok(total as u64/4)
        });
        Ok(Self {tx:Some(tx),worker:Some(worker),path})
    }
    pub fn push(&self, samples: &[i16]) -> io::Result<()> {
        if samples.is_empty() { return Ok(()); }
        self.tx.as_ref().unwrap().try_send(samples.to_vec()).map_err(|e| match e {
            TrySendError::Full(_)=>io::Error::other("Disco lento: grabacion detenida sin omitir bloques"),
            TrySendError::Disconnected(_)=>io::Error::other("Error del escritor WAV"),
        })
    }
    pub fn stop(mut self) -> io::Result<(PathBuf,u64)> {
        self.tx.take();
        let frames=self.worker.take().unwrap().join().map_err(|_|io::Error::other("Fallo del escritor WAV"))??;
        Ok((self.path.clone(),frames))
    }
}
impl Drop for Recorder {
    fn drop(&mut self) {
        self.tx.take();
        if let Some(w)=self.worker.take() { let _=w.join(); }
    }
}
pub fn stop_recording(r: &mut Option<Recorder>, view: &std::sync::Mutex<View>) {
    if let Some(rec)=r.take() {
        let msg=match rec.stop() {
            Ok((path,frames))=>format!("WAV GUARDADO / {:.2} S / {}",frames as f64/44100.,path.file_name().unwrap_or_default().to_string_lossy()),
            Err(e)=>format!("ERROR WAV / {e}"),
        };
        eprintln!("{msg}");
        let mut v=view.lock().unwrap(); v.recording=false; v.message=msg;
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn wav_roundtrip_exact_and_finalized() {
        let p=std::env::temp_dir().join(format!("fm1-wav-test-{}.wav",std::process::id()));
        let _=std::fs::remove_file(&p);
        let r=Recorder::at(p.clone()).unwrap();
        r.push(&[i16::MIN,-1,0,i16::MAX]).unwrap(); r.push(&[123,-456]).unwrap();
        assert_eq!(r.stop().unwrap().1,3);
        let b=std::fs::read(&p).unwrap();
        assert_eq!(&b[..4],b"RIFF"); assert_eq!(&b[8..16],b"WAVEfmt ");
        assert_eq!(u32::from_le_bytes(b[4..8].try_into().unwrap()),48);
        assert_eq!(u32::from_le_bytes(b[40..44].try_into().unwrap()),12);
        let pcm:Vec<i16>=b[44..].chunks_exact(2).map(|b|i16::from_le_bytes([b[0],b[1]])).collect();
        assert_eq!(pcm,vec![i16::MIN,-1,0,i16::MAX,123,-456]);
        if let Some(out)=std::env::var_os("FM1_WAV_TEST_OUTPUT") { std::fs::copy(&p,out).unwrap(); }
        std::fs::remove_file(p).unwrap();
    }
    #[test] fn controls_do_not_hit_panel() {
        assert_eq!(hit(680.,25.),Some(Button::Json));
        assert_eq!(hit(680.,110.),None);
        assert_eq!(hit(900.,25.),Some(Button::Record));
        assert_eq!(next_clock(200,true),240); assert_eq!(next_clock(200,false),192);
    }
    #[test] fn recorder_refuses_overwrite() {
        let p=std::env::temp_dir().join(format!("fm1-existing-{}.wav",std::process::id()));
        std::fs::write(&p,b"keep").unwrap();
        assert!(Recorder::at(p.clone()).is_err());
        assert_eq!(std::fs::read(&p).unwrap(),b"keep"); std::fs::remove_file(p).unwrap();
    }
}
