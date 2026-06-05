# Cria o atalho "Cortes CapCut" na Area de Trabalho apontando pro app (sem console)
$proj = $PSScriptRoot

# acha o pythonw.exe (sem console)
$pyw = ""
try { $pyw = (& py -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))").Trim() } catch {}
if (-not $pyw -or -not (Test-Path $pyw)) {
    $c = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($c) { $pyw = $c.Source }
}
if (-not $pyw -or -not (Test-Path $pyw)) {
    Write-Host "Nao achei o pythonw.exe; o atalho usara 'py'."
    $pyw = "py"
}

$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop "Cortes CapCut.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = $pyw
$sc.Arguments = '"' + (Join-Path $proj "exportador_gui.py") + '"'
$sc.WorkingDirectory = $proj
$ico = Join-Path $proj "icon.ico"
if (Test-Path $ico) { $sc.IconLocation = "$ico,0" }
$sc.Description = "Cortes CapCut - exporta, corta e organiza no Drive"
$sc.WindowStyle = 1
$sc.Save()
Write-Host "Atalho criado: $lnk"
