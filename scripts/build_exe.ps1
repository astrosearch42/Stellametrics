$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv est requis pour construire Stellametrics. Installez-le depuis https://docs.astral.sh/uv/"
}

$requiredPaths = @(
    "Assets",
    "Library\distance_library.json",
    "Library\de421.bsp",
    "Library\fonts",
    "Preset",
    "src\stellametrics\ImageViewer.ui",
    "src\stellametrics\StyleSheets",
    "src\stellametrics\Stellametrics.py"
)

foreach ($relativePath in $requiredPaths) {
    if (-not (Test-Path (Join-Path $projectRoot $relativePath))) {
        throw "Ressource introuvable : $relativePath"
    }
}

Write-Host "Synchronisation de l'environnement uv..."
uv sync --group build
if ($LASTEXITCODE -ne 0) {
    throw "La synchronisation uv a échoué."
}

$pyinstallerArguments = @(
    "--clean",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", "Stellametrics",
    "--icon", "Assets\Icon\icon.ico",
    "--add-data", "Assets;Assets",
    "--add-data", "src\stellametrics\ImageViewer.ui;src\stellametrics",
    "--add-data", "src\stellametrics\StyleSheets;src\stellametrics\StyleSheets",
    "--add-data", "Library\distance_library.json;Library",
    "--add-data", "Library\de421.bsp;Library",
    "--add-data", "Library\fonts;Library\fonts",
    "--add-data", "Preset;Preset",
    "src\stellametrics\Stellametrics.py"
)

Write-Host "Construction de dist\Stellametrics.exe..."
uv run --group build pyinstaller @pyinstallerArguments
if ($LASTEXITCODE -ne 0) {
    throw "La compilation PyInstaller a échoué."
}

Write-Host "Executable créé : $projectRoot\dist\Stellametrics.exe"
