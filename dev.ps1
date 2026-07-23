# IAmina local dev
$ErrorActionPreference = "Continue" # Don't stop on non-critical errors (like missing flutter)
$ROOT = Get-Location

# Set console to UTF8 to avoid UnicodeEncodeErrors
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==> IAmina local dev setup"

# -- One-time setup ------------------------------------------------------------
if (-not (Test-Path "venv")) {
    Write-Host "--> Creating venv..."
    python -m venv venv
}

# Activate venv for the current script
& "$ROOT\venv\Scripts\Activate.ps1"

Write-Host "--> Syncing dependencies..."
pip install --quiet -r backend\requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "--> Creating .env..."
    Copy-Item ".env.example" ".env"
}

Write-Host "--> Running migrations and demo setup..."
Set-Location "$ROOT\backend"
python manage.py migrate --run-syncdb
python manage.py setup_demo
Set-Location $ROOT

# -- Check/Install Flutter -----------------------------------------------------
$FLUTTER_VERSION = "3.41.7"
$FLUTTER_DIR = "$ROOT\flutter_sdk"
$FLUTTER_BIN = "$FLUTTER_DIR\flutter\bin"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    if (Test-Path "$FLUTTER_BIN\flutter.bat") {
        Write-Host "--> Using local Flutter SDK at $FLUTTER_DIR"
        $env:Path += ";$FLUTTER_BIN"
    } else {
        Write-Host "--> Flutter not found. Installing version $FLUTTER_VERSION..."
        Write-Host "    This may take a few minutes (approx 1GB download)..."
        
        $zipFile = "$ROOT\flutter_windows.zip"
        $url = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_$($FLUTTER_VERSION)-stable.zip"
        
        if (-not (Test-Path $zipFile)) {
            Write-Host "    Downloading..."
            Invoke-WebRequest -Uri $url -OutFile $zipFile
        }
        
        Write-Host "    Extracting to $FLUTTER_DIR..."
        if (-not (Test-Path $FLUTTER_DIR)) { New-Item -ItemType Directory -Path $FLUTTER_DIR }
        Expand-Archive -Path $zipFile -DestinationPath $FLUTTER_DIR -Force
        
        Write-Host "    Cleaning up..."
        Remove-Item $zipFile
        
        $env:Path += ";$FLUTTER_BIN"
        flutter --version
    }
}

if (Get-Command flutter -ErrorAction SilentlyContinue) {
    Write-Host "--> Syncing frontend dependencies..."
    Set-Location "$ROOT\frontend"
    flutter pub get
    Set-Location $ROOT
}

# -- Kill stale backend processes on port 8001 ---------------------------------
$stale = (netstat -ano | Select-String ":8001\s.*LISTENING") |
    ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique
foreach ($pid in $stale) {
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -match "python|django") {
        Write-Host "--> Killing stale backend process (PID $pid)..."
        Stop-Process -Id $pid -Force
    }
}

# -- Start Redis (via Docker, best-effort) ------------------------------------
$redis = $null
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $redisRunning = docker ps --filter "name=iamina_redis" --format "{{.Names}}" 2>$null
    if (-not $redisRunning) {
        Write-Host "==> Starting Redis -> localhost:6379"
        $redis = Start-Process -PassThru -NoNewWindow docker -ArgumentList "run","--rm","--name","iamina_redis","-p","6379:6379","redis:7-alpine"
        Start-Sleep -Seconds 2
    } else {
        Write-Host "==> Redis already running (iamina_redis)"
    }
} else {
    Write-Host "[WARN] Docker not found — Redis unavailable (cache will degrade gracefully)"
}

# -- Start services ------------------------------------------------------------
Write-Host "==> Starting backend -> http://127.0.0.1:8001"
$backend = Start-Process -PassThru -NoNewWindow powershell -ArgumentList "-NoProfile", "-Command", "& '$ROOT\venv\Scripts\Activate.ps1'; cd '$ROOT\backend'; python manage.py runserver 8001"

if (Get-Command flutter -ErrorAction SilentlyContinue) {
    Write-Host "==> Starting frontend -> http://localhost:3000"
    try {
        Set-Location "$ROOT\frontend"
        flutter run -d web-server --web-port 3000 --web-hostname localhost --dart-define=API_BASE_URL=http://127.0.0.1:8001
    } finally {
        if ($backend) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
        if ($redis)   { Stop-Process -Id $redis.Id   -Force -ErrorAction SilentlyContinue }
    }
} else {
    Write-Host "==> Backend running at http://127.0.0.1:8001 — Ctrl-C to stop"
    try {
        while ($true) { Start-Sleep -Seconds 60 }
    } finally {
        if ($backend) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
        if ($redis)   { Stop-Process -Id $redis.Id   -Force -ErrorAction SilentlyContinue }
    }
}
