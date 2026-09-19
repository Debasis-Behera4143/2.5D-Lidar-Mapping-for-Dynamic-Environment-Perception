# Setup script to create a dedicated Python 3.11 virtual environment with Open3D and PyTorch using uv
Write-Host "Setting up LiDAR Adaptive Mapping environment with Python 3.11..." -ForegroundColor Cyan

$uvPath = "C:\Users\debas\AppData\Local\hermes\bin\uv.exe"
if (-not (Test-Path $uvPath)) {
    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCmd) {
        $uvPath = $uvCmd.Source
    } else {
        Write-Host "Error: uv is not installed or not in PATH." -ForegroundColor Red
        Exit 1
    }
}

Write-Host "Creating .venv with Python 3.11 using uv..." -ForegroundColor Green
& $uvPath venv .venv --python 3.11

Write-Host "Installing dependencies into .venv..." -ForegroundColor Green
& $uvPath pip install -r requirements.txt --python .venv\Scripts\python.exe
& $uvPath pip install open3d --python .venv\Scripts\python.exe

Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host "Activate via: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
