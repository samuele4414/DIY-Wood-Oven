param()
$ErrorActionPreference = 'Stop'
$output = Join-Path $PSScriptRoot 'output'
if (-not (Test-Path -LiteralPath (Join-Path $output 'index.html'))) { throw 'Generare prima build_study.py.' }
$browsers = @('C:\Program Files\Google\Chrome\Application\chrome.exe', 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
$browser = $browsers | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $browser) { throw 'Chrome/Edge non trovato.' }
$profile = Join-Path $env:LOCALAPPDATA ('Temp\opencode\forno-C03-browser-' + [guid]::NewGuid().ToString('N'))
$common = @('--headless=new', '--disable-gpu', '--disable-extensions', '--no-first-run', '--no-default-browser-check', '--disable-background-networking', "--user-data-dir=$profile", '--allow-file-access-from-files', '--virtual-time-budget=2200')
function Invoke-StudyBrowser([string[]]$ExtraArguments) {
    $quoted = (($common + $ExtraArguments) | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $process = Start-Process -FilePath $browser -ArgumentList $quoted -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Browser terminato con codice $($process.ExitCode)." }
}
$pdf = Join-Path $output 'Scheda_C03.pdf'
$uri = ([uri](Join-Path $output 'scheda_stampa.html')).AbsoluteUri
Invoke-StudyBrowser @('--no-pdf-header-footer', "--print-to-pdf=$pdf", $uri)
if (-not (Test-Path -LiteralPath $pdf)) { throw 'PDF non generato.' }
$views = @(
    @{Input='pianta_C03.svg'; Output='pianta_C03.png'; Size='1300,850'},
    @{Input='modulo_C03.svg'; Output='modulo_C03.png'; Size='1300,850'},
    @{Input='servizio_C03.svg'; Output='servizio_C03.png'; Size='1300,850'},
    @{Input='index.html'; Output='anteprima.png'; Size='1440,1000'}
)
foreach ($view in $views) {
    $uri = ([uri](Join-Path $output $view.Input)).AbsoluteUri
    $image = Join-Path $output $view.Output
    Invoke-StudyBrowser @('--hide-scrollbars', "--window-size=$($view.Size)", "--screenshot=$image", $uri)
    if (-not (Test-Path -LiteralPath $image)) { throw "PNG non generato: $image" }
}
& python -B (Join-Path $PSScriptRoot 'build_study.py') --record-export
if ($LASTEXITCODE -ne 0) { throw 'Verifica/provenienza esportazione fallita.' }
Write-Output "PDF/PNG C03 esportati: $output"
Write-Output "Profilo browser isolato: $profile"
