
import { chromium } from "playwright";
const base=process.env.BB_SMOKE_URL||"http://127.0.0.1:8642";
const firmware=process.env.BB_SMOKE_FW||"fm1-sid/web/sidplayer.fwsc";
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN||"/usr/bin/google-chrome",args:["--no-sandbox","--autoplay-policy=no-user-gesture-required","--disable-dev-shm-usage"]});
try {
  const page=await browser.newPage({acceptDownloads:true});
  const errors=[],failed=[];
  page.on("pageerror",e=>errors.push(String(e)));
  page.on("console",m=>{if(m.type()==="error")errors.push("console: "+m.text())});
  page.on("requestfailed",r=>failed.push([r.url(),r.failure()?.errorText]));
  await page.goto(base+"/biomech-blackbox/",{waitUntil:"domcontentloaded",timeout:30000});
  await page.locator("#open").setInputFiles(firmware);
  await page.waitForTimeout(750);
  const selected=await page.locator("#status").innerText();
  await page.locator("#start").click();
  await page.waitForTimeout(5000);
  const status=await page.locator("#status").innerText();
  const chosen=await page.locator("#fw").inputValue();
  const bbstate=await page.locator("#bbstate").innerText();
  console.log(JSON.stringify({selected,chosen,status,bbstate,errors,failed},null,2));
  if(errors.length || /boot:|not an FM-1|could not|error/i.test(status)||!/Capture armed|BLACK BOX captured|CPU halted/.test(bbstate)) {
     throw new Error("Web page did not boot a real .fwsc and arm the BLACK BOX");
  }
  // Exercise a REAL browser encoder event, not an inert source-code assertion.
  await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(950);
  // A capture must produce a downloadable and parseable report, not merely a button.
  const [download]=await Promise.all([page.waitForEvent("download",{timeout:15000}), page.locator("#bbexport").click()]);
  const path=await download.path();
  const {readFileSync}=await import("node:fs");
  const obj=JSON.parse(readFileSync(path,"utf8"));
  console.log("BLACKBOX_EXPORT",{format:obj.format,ram_bytes:obj.ram_bytes,emulator:obj.emulator?.schema,firmware:obj.candidate,error:obj.error,note:obj.note});
  if(obj.ram_bytes!==1048576 || !obj.emulator?.cpu0 || !obj.ram_base64)throw new Error("BLACK BOX missing CPU0/RAM");
  console.log("PRESET_KNOB_DIAG",{events:obj.emulator.control_events?.slice(-4),
    branches:obj.emulator.cpu0_branches?.length,
    armed:obj.emulator.branch_trace_armed,jit:obj.emulator.cpu0_jit_enabled,
    timeout:obj.emulator.trace_until_ms});
  if(!obj.emulator?.control_events?.some(e=>e[0]===1 && e[2]!==0) ||
     !obj.emulator?.cpu0_branches?.length)
    throw new Error("BLACK BOX missing actual knob action / CPU0 branch trace");
  if(obj.emulator.branch_trace_armed || !obj.emulator.cpu0_jit_enabled ||
     obj.emulator.trace_until_ms !== null)
    throw new Error("CPU0 trace kept interpreter enabled after 250 ms; audio load may be contaminated");
  const audio=obj.audio_metrics;
  console.log("PCM_DIAGNOSTICS",{quanta:audio?.quanta,shortQuanta:audio?.shortQuanta,missingFrames:audio?.missingFrames,peak:audio?.peak,trace:audio?.quantumTrace?.length});
  if(!audio || audio.quanta<=0 || !audio.quantumTrace?.length || audio.availableWavFrames<=0)
    throw new Error("BLACK BOX missing audio underrun/PCM diagnostics");
  const [wavDownload]=await Promise.all([page.waitForEvent("download",{timeout:15000}),page.locator("#wavexport").click()]);
  const wav=readFileSync(await wavDownload.path());
  if(wav.length<=44 || wav.toString("ascii",0,4)!=="RIFF" ||
     wav.toString("ascii",8,12)!=="WAVE" || wav.readUInt16LE(22)!==2 ||
     wav.readUInt16LE(34)!==16 || wav.readUInt32LE(40)!==wav.length-44)
    throw new Error("WAV export invalid or empty");
  console.log("WAV_EXPORT",{bytes:wav.length,frames:(wav.length-44)/4,rate:wav.readUInt32LE(24)});
  // The user-approved eight-second recording MUST remain available, independent
  // of the rolling six-second diagnostic export.
  const [recording]=await Promise.all([
    page.waitForEvent("download",{timeout:55000}),
    page.locator("#record8").click()
  ]);
  const rec=readFileSync(await recording.path());
  const frames=(rec.length-44)/4;
  const sampleHz=rec.readUInt32LE(24);
  console.log("RECORD8_WAV",{bytes:rec.length,frames,sampleHz,seconds:frames/sampleHz});
  if(rec.toString("ascii",0,4)!=="RIFF" ||
     rec.toString("ascii",8,12)!=="WAVE" ||
     rec.readUInt32LE(40)!==rec.length-44 ||
     frames!==Math.round(sampleHz*8) ||
     (await page.locator("#record8").isDisabled()))
    throw new Error("Eight-second recording failed or was not re-enabled");
} finally {await browser.close();}
