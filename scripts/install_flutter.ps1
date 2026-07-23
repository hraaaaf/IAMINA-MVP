# Install Flutter 3.41.7 for IAmina
$FLUTTER_VERSION = "3.41.7"
$ROOT = Get-Location
$FLUTTER_DIR = "$ROOT\flutter_sdk"
$FLUTTER_BIN = "$FLUTTER_DIR\flutter\bin"

Write-Host "==> IAmina Flutter Setup"
if (Test-Path "$FLUTTER_BIN\flutter.bat") {
    Write-Host "--> Flutter already installed at $FLUTTER_DIR"
    exit
}

Write-Host "--> Downloading Flutter $FLUTTER_VERSION..."
$zipFile = "$ROOT\flutter_windows.zip"
$url = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_$($FLUTTER_VERSION)-stable.zip"

# Use curl.exe with resume support (-C -) for maximum reliability on large files
Write-Host "--> Downloading Flutter $FLUTTER_VERSION (Resumable)..."
curl.exe -L -C - $url -o $zipFile

Write-Host "--> Extracting to $FLUTTER_DIR..."
if (-not (Test-Path $FLUTTER_DIR)) { New-Item -ItemType Directory -Path $FLUTTER_DIR }
Expand-Archive -Path $zipFile -DestinationPath $FLUTTER_DIR -Force

Write-Host "--> Cleaning up..."
Remove-Item $zipFile

Write-Host "--> Verifying installation..."
& "$FLUTTER_BIN\flutter.bat" --version

Write-Host ""
Write-Host "DONE! Flutter is installed in $FLUTTER_DIR"
Write-Host "To use it in your terminal, run:"
Write-Host "`$env:Path += ';$FLUTTER_BIN'"
