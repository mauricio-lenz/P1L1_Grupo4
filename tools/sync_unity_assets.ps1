# Sync: results/export/*.json -> unity-viewer/Assets/StreamingAssets/json/
# Ejecutar despues de regenerar el modelo (python -m src.edificio).
$repo = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $repo 'results\export'
$dst  = Join-Path $repo 'unity-viewer\Assets\StreamingAssets\json'
if (-not (Test-Path $src))   { Write-Error "No existe $src"; exit 1 }
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item "$src\*.json" $dst -Force
Write-Host "JSON sincronizados a $dst"