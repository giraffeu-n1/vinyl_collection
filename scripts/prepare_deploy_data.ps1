# Копирует локальную базу и media в deploy-data/ для деплоя через Git
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$deployData = Join-Path $root 'deploy-data'

New-Item -ItemType Directory -Force -Path $deployData | Out-Null

$db = Join-Path $root 'db.sqlite3'
if (-not (Test-Path $db)) {
    Write-Error "Не найден $db"
}
Copy-Item -Path $db -Destination (Join-Path $deployData 'db.sqlite3') -Force
Write-Host "OK: db.sqlite3"

$mediaSrc = Join-Path $root 'media'
$mediaDst = Join-Path $deployData 'media'
if (-not (Test-Path $mediaSrc)) {
    Write-Error "Не найден $mediaSrc"
}
if (Test-Path $mediaDst) {
    Remove-Item -Path $mediaDst -Recurse -Force
}
Copy-Item -Path $mediaSrc -Destination $mediaDst -Recurse -Force
$count = (Get-ChildItem $mediaDst -Recurse -File).Count
Write-Host "OK: media ($count files)"

Write-Host ''
Write-Host 'Дальше:'
Write-Host '  git add deploy-data'
Write-Host '  git commit -m "Update deploy data"'
Write-Host '  git push origin main'
