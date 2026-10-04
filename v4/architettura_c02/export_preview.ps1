param()
$ErrorActionPreference = 'Stop'
$output = Join-Path $PSScriptRoot 'output'
if (-not (Test-Path -LiteralPath (Join-Path $output 'index.html'))) {
    throw 'Generare prima: python -B v4/architettura_c02/build_study.py'
}
$browsers = @(
    'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
)
$browser = $browsers | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $browser) { throw 'Chrome/Edge non trovato. Aprire scheda_stampa.html e usare Stampa > PDF, A4 orizzontale.' }
$profile = Join-Path $env:LOCALAPPDATA ('Temp\opencode\forno-C02-browser-' + [guid]::NewGuid().ToString('N'))
$common = @('--headless=new', '--disable-gpu', '--disable-extensions', '--no-first-run',
    '--no-default-browser-check', '--disable-background-networking', "--user-data-dir=$profile",
    '--allow-file-access-from-files', '--virtual-time-budget=1800')
function Invoke-StudyBrowser([string[]]$ExtraArguments) {
    $arguments = $common + $ExtraArguments
    $quoted = ($arguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $process = Start-Process -FilePath $browser -ArgumentList $quoted -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Browser terminato con codice $($process.ExitCode)." }
}
$pdf = Join-Path $output 'Scheda_C02.pdf'
$uri = ([uri](Join-Path $output 'scheda_stampa.html')).AbsoluteUri
Invoke-StudyBrowser @('--no-pdf-header-footer', "--print-to-pdf=$pdf", $uri)
if (-not (Test-Path -LiteralPath $pdf)) { throw 'PDF non generato.' }
$views = @(
    @{Input='pianta_moduli.svg'; Output='pianta_moduli.png'; Size='1400,950'},
    @{Input='modulo_disco.svg'; Output='modulo_disco.png'; Size='1400,950'},
    @{Input='schema_aria_fumi.svg'; Output='schema_aria_fumi.png'; Size='1400,950'},
    @{Input='collare_tiraggio.svg'; Output='collare_tiraggio.png'; Size='1400,950'},
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
Write-Output "PDF/PNG esportati in: $output"
Write-Output "Profilo browser temporaneo isolato: $profile"
