# Open WebUI Startup Script for Windows
# This script checks dependencies and starts both backend and frontend servers

param(
    [int]$BackendPort = 8080,
    [int]$FrontendPort = 5173,
    [switch]$SkipChecks,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

# ANSI color codes for better output
$Colors = @{
    Green = "`e[32m"
    Red = "`e[31m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Reset = "`e[0m"
    Bold = "`e[1m"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "Reset"
    )
    Write-Host "$($Colors[$Color])$Message$($Colors.Reset)"
}

function Write-Header {
    param([string]$Title)
    Write-ColorOutput "`n$($Colors.Bold)=== $Title ===$($Colors.Reset)" "Blue"
}

function Write-Success { 
    param([string]$Message) 
    Write-ColorOutput "✓ $Message" "Green" 
}
function Write-Error { 
    param([string]$Message) 
    Write-ColorOutput "✗ $Message" "Red" 
}
function Write-Warning { 
    param([string]$Message) 
    Write-ColorOutput "⚠ $Message" "Yellow" 
}
function Write-Info { 
    param([string]$Message) 
    Write-ColorOutput "ℹ $Message" "Blue" 
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Header "Open WebUI Startup Script"
Write-Info "Script directory: $ScriptDir"
Write-Info "Backend port: $BackendPort"
Write-Info "Frontend port: $FrontendPort"

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = netstat -an | findstr ":$Port"
        return $connection -ne $null
    } catch {
        return $false
    }
}

# Function to kill process on a port
function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $process = netstat -ano | findstr ":$Port" | ForEach-Object { ($_ -split '\s+')[4] }
        if ($process) {
            Write-Warning "Killing process on port $Port (PID: $process)"
            taskkill /f /pid $process 2>$null
            Start-Sleep -Seconds 2
        }
    } catch {
        # Ignore errors
    }
}

if (-not $SkipChecks) {
    Write-Header "Checking Dependencies"
    
    # Check Python
    Write-Info "Checking Python..."
    try {
        $pythonVersion = py --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python found: $pythonVersion"
        } else {
            Write-Error "Python not found. Please install Python 3.11+ from python.org"
            exit 1
        }
    } catch {
        Write-Error "Python not found. Please install Python 3.11+ from python.org"
        exit 1
    }
    
    # Check Node.js
    Write-Info "Checking Node.js..."
    try {
        $nodeVersion = node --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Node.js found: $nodeVersion"
        } else {
            Write-Error "Node.js not found. Please install Node.js 18+ from nodejs.org"
            exit 1
        }
    } catch {
        Write-Error "Node.js not found. Please install Node.js 18+ from nodejs.org"
        exit 1
    }
    
    # Check npm
    Write-Info "Checking npm..."
    try {
        $npmVersion = npm --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "npm found: $npmVersion"
        } else {
            Write-Error "npm not found"
            exit 1
        }
    } catch {
        Write-Error "npm not found"
        exit 1
    }
    
    # Check if backend directory exists
    if (-not (Test-Path "backend")) {
        Write-Error "Backend directory not found. Are you in the correct Open WebUI directory?"
        exit 1
    }
    
    # Check if requirements.txt exists
    if (-not (Test-Path "backend\requirements.txt")) {
        Write-Error "Backend requirements.txt not found"
        exit 1
    }
    
    # Check if package.json exists
    if (-not (Test-Path "package.json")) {
        Write-Error "package.json not found. Are you in the correct Open WebUI directory?"
        exit 1
    }
}

Write-Header "Checking Port Availability"

# Check backend port
if (Test-Port $BackendPort) {
    Write-Warning "Port $BackendPort is already in use"
    $response = Read-Host "Do you want to kill the process using port $BackendPort? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Stop-ProcessOnPort $BackendPort
    } else {
        Write-Error "Cannot start backend. Port $BackendPort is in use."
        exit 1
    }
} else {
    Write-Success "Port $BackendPort is available"
}

# Check frontend port
if (Test-Port $FrontendPort) {
    Write-Warning "Port $FrontendPort is already in use"
    $response = Read-Host "Do you want to kill the process using port $FrontendPort? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Stop-ProcessOnPort $FrontendPort
    } else {
        Write-Error "Cannot start frontend. Port $FrontendPort is in use."
        exit 1
    }
} else {
    Write-Success "Port $FrontendPort is available"
}

# Function to start backend
function Start-Backend {
    Write-Header "Starting Backend Server"
    Write-Info "Starting backend on port $BackendPort..."
    
    $backendScript = @"
cd backend
py -m uvicorn open_webui.main:app --host 127.0.0.1 --port $BackendPort --reload
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowStyle Normal
    Start-Sleep -Seconds 3
    
    # Test if backend is running
    $maxAttempts = 10
    $attempt = 0
    do {
        $attempt++
        Start-Sleep -Seconds 2
        try {
            $response = curl -s -o $null -w "%{http_code}" "http://127.0.0.1:$BackendPort" 2>$null
            if ($response -eq "404" -or $response -eq "200") {
                Write-Success "Backend server is running on http://127.0.0.1:$BackendPort"
                return $true
            }
        } catch {
            Write-Info "Waiting for backend to start... (attempt $attempt/$maxAttempts)"
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-Error "Backend failed to start after $maxAttempts attempts"
    return $false
}

# Function to start frontend
function Start-Frontend {
    Write-Header "Starting Frontend Server"
    Write-Info "Starting frontend on port $FrontendPort..."
    
    $frontendScript = @"
npm run dev -- --port $FrontendPort
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowStyle Normal
    Start-Sleep -Seconds 5
    
    # Test if frontend is running
    $maxAttempts = 10
    $attempt = 0
    do {
        $attempt++
        Start-Sleep -Seconds 2
        try {
            $response = curl -s -o $null -w "%{http_code}" "http://localhost:$FrontendPort" 2>$null
            if ($response -eq "200") {
                Write-Success "Frontend server is running on http://localhost:$FrontendPort"
                return $true
            }
        } catch {
            Write-Info "Waiting for frontend to start... (attempt $attempt/$maxAttempts)"
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-Error "Frontend failed to start after $maxAttempts attempts"
    return $false
}

# Start servers based on parameters
$backendStarted = $false
$frontendStarted = $false

if (-not $FrontendOnly) {
    $backendStarted = Start-Backend
    if (-not $backendStarted) {
        Write-Error "Failed to start backend. Exiting."
        exit 1
    }
}

if (-not $BackendOnly) {
    $frontendStarted = Start-Frontend
    if (-not $frontendStarted) {
        Write-Error "Failed to start frontend. Exiting."
        exit 1
    }
}

Write-Header "Open WebUI Status"
if ($backendStarted) {
    Write-Success "Backend: http://127.0.0.1:$BackendPort"
}
if ($frontendStarted) {
    Write-Success "Frontend: http://localhost:$FrontendPort"
}

Write-Header "Next Steps"
Write-Info "1. Open your browser and go to: http://localhost:$FrontendPort"
Write-Info "2. The frontend will automatically connect to the backend"
Write-Info "3. If you see 'Backend Required' error, wait a few more seconds for the backend to fully start"
Write-Info "4. To stop the servers, close the PowerShell windows or press Ctrl+C in each window"

Write-Header "Troubleshooting"
Write-Info "• If you get 'localhost refused to connect', check if Windows Firewall is blocking the connections"
Write-Info "• If you get 'Backend Required', the backend might still be starting up - wait a moment and refresh"
Write-Info "• If you get port conflicts, use different ports: .\start-openwebui.ps1 -BackendPort 8888 -FrontendPort 3000"
Write-Info "• To run only backend: .\start-openwebui.ps1 -BackendOnly"
Write-Info "• To run only frontend: .\start-openwebui.ps1 -FrontendOnly"

Write-ColorOutput "`n🎉 Open WebUI should now be running! 🎉" "Green" 