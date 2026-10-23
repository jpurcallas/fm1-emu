# BIOMECH3 FWSC v0.4 research only. NO INSTALL, NO HARDWARE.
# Uses the original FM1 Open V14 Package.cs and boot resources without editing.
param(
 [Parameter(Mandatory=$true)][string]$SdkRoot,
 [Parameter(Mandatory=$true)][string]$Toolchain,
 [Parameter(Mandatory=$true)][string]$BuildRoot
)
$ErrorActionPreference="Stop"
$Elf=Join-Path $BuildRoot "sdk.elf"
$Bin=Join-Path $Toolchain "common/bin/objcopy"
if(-not (Test-Path $Elf)) {throw "Missing guest PI32 ELF"}
if(-not (Test-Path $Bin)) {throw "Missing original objcopy"}
$root=[IO.Path]::GetFullPath($BuildRoot)
[IO.Directory]::CreateDirectory($root)|Out-Null
$data=[IO.File]::ReadAllBytes($Elf)
if([BitConverter]::ToUInt32($data,24) -ne 0x02000120) {throw "Unexpected ELF entry point"}
$app = New-Object IO.MemoryStream
try {
 foreach($section in @("text","data","ram0_data","cache_ram_data")) {
   $dest=Join-Path $root ($section+".bin")
   & $Bin "-O" "binary" "-j" ("."+$section) $Elf $dest
   if($LASTEXITCODE -ne 0){throw "objcopy failed for $section"}
   $bytes=[IO.File]::ReadAllBytes($dest)
   Write-Host "BR3_PACKAGE_SECTION $section $($bytes.Length)"
   $app.Write($bytes,0,$bytes.Length)
 }
 $Version=Get-Content -Raw -LiteralPath (Join-Path $SdkRoot "app/version.h")
 $m=[regex]::Match($Version,'(?m)^#define FM1_UPDATE_PRODUCT "(FM-1_8\d{6})"')
 if(-not $m.Success){throw "Firmware product identity missing"}
 $out=Join-Path $root "BIOMECH3_v0.4_CPU1_PROBE_SOLO_EMULADOR.fwsc"
 Add-Type -Path (Join-Path $SdkRoot "sdk/Package.cs")
 $report=[FM1.Package]::Create($app.ToArray(),(Join-Path $SdkRoot "sdk/tools/pack"),$out,536576,$m.Groups[1].Value)
 if(-not (Test-Path $out)){throw "Package did not create fwsc"}
 Write-Host "BR3_PACKAGE_REPORT $($report|ConvertTo-Json -Compress)"
 Write-Host "BR3_FWSC_SOLO_EMULADOR $out bytes=$((Get-Item $out).Length)"
 Write-Host "DO NOT INSTALL THIS CPU1 DIAGNOSTIC FWSC IN FM-1 HARDWARE"
} finally{$app.Dispose()}
