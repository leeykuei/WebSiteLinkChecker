. "$PSScriptRoot\common.ps1"
$r = Get-RepoRoot
Write-Output "REPO_ROOT_RAW: '$r'"
if ($r -eq $null) { Write-Output 'REPO_ROOT is $null' } else { Write-Output "Length: $($r.Length)" }
Write-Output "Resolved via Resolve-Path?" 
try { $rp = Resolve-Path $r -ErrorAction Stop; Write-Output "Resolve-Path OK: $($rp.Path)" } catch { Write-Output "Resolve-Path failed: $($_.Exception.Message)" }
