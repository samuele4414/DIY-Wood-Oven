param(
    [string]$Campaign = (Join-Path $PSScriptRoot 'campaign'),
    [ValidateSet('preheat', 'bake', 'all')][string]$Stage = 'all',
    [string]$Fds = '',
    [ValidateRange(1, 1024)][int]$Threads = 2,
    [string]$Python = 'python',
    [switch]$Execute
)
$ErrorActionPreference = 'Stop'
$runnerArguments = @((Join-Path $PSScriptRoot 'run_home.py'), '--campaign', $Campaign,
    '--stage', $Stage, '--threads', [string]$Threads)
if ($Fds) { $runnerArguments += @('--fds', $Fds) }
if ($Execute) { $runnerArguments += '--execute' }
& $Python @runnerArguments
exit $LASTEXITCODE
