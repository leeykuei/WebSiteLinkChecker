. "$PSScriptRoot\common.ps1"
$paths = Get-FeaturePathsEnv
Write-Output "--- PATHS ---"
$paths | Format-List * -Force
Write-Output "--- Attempting New-Item for FEATURE_DIR ---"
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null
Write-Output "Created/Ensured FEATURE_DIR: $($paths.FEATURE_DIR)"
$template = Join-Path $paths.REPO_ROOT '.specify/templates/plan-template.md'
Write-Output "Template path: $template"
if (Test-Path $template) { Copy-Item $template $paths.IMPL_PLAN -Force; Write-Output "Copied plan template to $($paths.IMPL_PLAN)" } else { Write-Output "Template not found: $template" }
