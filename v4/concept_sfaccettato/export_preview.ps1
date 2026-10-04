param([switch]$IncludeViewer)
$ErrorActionPreference = 'Stop'
$output = Join-Path $PSScriptRoot 'output'
if (-not (Test-Path -LiteralPath (Join-Path $output 'index.html'))) {
    throw 'Generare prima lo studio: python -B build_study.py'
}
$browsers = @(
    'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
)
$browser = $browsers | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $browser) { throw 'Chrome o Edge non trovato. Aprire scheda_stampa.html e usare Stampa > PDF.' }
$profile = Join-Path $env:LOCALAPPDATA ('Temp\opencode\forno-C01-browser-' + [guid]::NewGuid().ToString('N'))
$common = @('--headless=new', '--disable-gpu', '--disable-extensions', '--no-first-run',
    '--no-default-browser-check', '--disable-background-networking', "--user-data-dir=$profile",
    '--allow-file-access-from-files', '--virtual-time-budget=1800')
function Invoke-StudyBrowser([string[]]$ExtraArguments) {
    # Windows GUI executables launched with '&' can return before writing files.
    # Wait for this isolated process, without touching existing browser sessions.
    $arguments = $common + $ExtraArguments
    $quoted = ($arguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $process = Start-Process -FilePath $browser -ArgumentList $quoted -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Browser terminato con codice $($process.ExitCode)." }
}
$pdf = Join-Path $output 'Scheda_C01.pdf'
$uri = ([uri](Join-Path $output 'scheda_stampa.html')).AbsoluteUri
Invoke-StudyBrowser @('--no-pdf-header-footer', "--print-to-pdf=$pdf", $uri)
if (-not (Test-Path -LiteralPath $pdf)) { throw 'Esportazione PDF fallita.' }
$views = @(
    @{Input='anteprima.html'; Output='assieme.png'; Size='1400,1050'},
    @{Input='pianta.svg'; Output='pianta.png'; Size='1400,1050'},
    @{Input='sezione_trasversale.svg'; Output='sezione_trasversale.png'; Size='1400,1050'},
    @{Input='sezione_longitudinale.svg'; Output='sezione_longitudinale.png'; Size='1400,1150'}
)
if ($IncludeViewer) { $views += @{Input='index.html'; Output='viewer.png'; Size='1440,1080'} }
foreach ($view in $views) {
    $uri = ([uri](Join-Path $output $view.Input)).AbsoluteUri
    $image = Join-Path $output $view.Output
    Invoke-StudyBrowser @('--hide-scrollbars', "--window-size=$($view.Size)", "--screenshot=$image", $uri)
    if (-not (Test-Path -LiteralPath $image)) { throw "Esportazione immagine fallita: $image" }
}
Write-Output "PDF e anteprime esportati in: $output"
Write-Output "Profilo browser temporaneo isolato: $profile"
