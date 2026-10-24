$ErrorActionPreference = "Stop"
$out = Join-Path (Get-Location) "presentation_preview"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
$path = (Resolve-Path ".\CryptoGuard_HOD_Presentation.pptx").Path
$pres = $ppt.Presentations.Open($path, $true, $false, $false)
$dest = Join-Path $out "slide"
$pres.SaveAs($dest, 18)
$pres.Close()
$ppt.Quit()
Get-ChildItem $out | ForEach-Object { $_.Name }
