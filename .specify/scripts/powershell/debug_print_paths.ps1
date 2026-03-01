. "$PSScriptRoot\common.ps1"
$p = Get-FeaturePathsEnv
$p | Format-List * -Force
$p | ConvertTo-Json -Compress | Out-File -FilePath (Join-Path $env:TEMP 'spec_paths_debug.json') -Encoding utf8
Write-Output "WROTE_JSON_TO: $env:TEMP\spec_paths_debug.json"