# Open WebUI DXMatrix Edition - Windows Native Installation Script
# This script installs Open WebUI natively on Windows without Docker or WSL

param(
    [switch]$Force,
    [switch]$SkipPrerequisites,
    [switch]$Development,
    [string]$InstallPath = "C:\Program Files\OWUI-DXMatrix"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Script variables
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$AppDataPath = "$env:LOCALAPPDATA\owui-dxmatrix"
$LogPath = "$AppDataPath\logs"
$ConfigPath = "$ProjectRoot\config"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-ColorOutput "`n" $Blue
    Write-ColorOutput "=" * 50 $Blue
    Write-ColorOutput " $Title" $Blue
    Write-ColorOutput "=" * 50 $Blue
    Write-ColorOutput "`n" $Blue
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" $Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" $Red
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    
    $prerequisites = @{
        "Python 3.11+" = $false
        "Node.js 18.13.0+" = $false
        "Git" = $false
        "Visual Studio Build Tools" = $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.(1[1-9]|[2-9][0-9])") {
            $prerequisites["Python 3.11+"] = $true
            Write-Success "Python version: $pythonVersion"
        } else {
            Write-Warning "Python version: $pythonVersion (3.11+ required)"
        }
    } catch {
        Write-Error "Python not found"
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v(1[8-9]|[2-9][0-9])") {
            $prerequisites["Node.js 18.13.0+"] = $true
            Write-Success "Node.js version: $nodeVersion"
        } else {
            Write-Warning "Node.js version: $nodeVersion (18.13.0+ required)"
        }
    } catch {
        Write-Error "Node.js not found"
    }
    
    # Check Git
    try {
        $gitVersion = git --version 2>&1
        $prerequisites["Git"] = $true
        Write-Success "Git version: $gitVersion"
    } catch {
        Write-Error "Git not found"
    }
    
    # Check Visual Studio Build Tools (simplified check)
    $vsTools = Get-ChildItem "C:\Program Files (x86)\Microsoft Visual Studio" -ErrorAction SilentlyContinue
    if ($vsTools) {
        $prerequisites["Visual Studio Build Tools"] = $true
        Write-Success "Visual Studio Build Tools found"
    } else {
        Write-Warning "Visual Studio Build Tools not found (may be needed for Python packages)"
    }
    
    # Summary
    $missing = $prerequisites.Values | Where-Object { $_ -eq $false }
    if ($missing.Count -gt 0) {
        Write-Error "Missing prerequisites detected"
        Write-ColorOutput "`nPlease install the following:" $Yellow
        foreach ($prereq in $prerequisites.GetEnumerator()) {
            if (-not $prereq.Value) {
                Write-ColorOutput "  - $($prereq.Key)" $Yellow
            }
        }
        return $false
    }
    
    Write-Success "All prerequisites met!"
    return $true
}

function New-Directories {
    Write-Header "Creating Directories"
    
    $directories = @(
        $AppDataPath,
        "$AppDataPath\logs",
        "$AppDataPath\data",
        "$AppDataPath\cache",
        "$AppDataPath\sessions",
        $ConfigPath
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Created: $dir"
        } else {
            Write-ColorOutput "Exists: $dir" $Blue
        }
    }
}

function Install-PythonDependencies {
    Write-Header "Installing Python Dependencies"
    
    $requirementsFile = "$ProjectRoot\backend\requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Error "Requirements file not found: $requirementsFile"
        return $false
    }
    
    try {
        # Create virtual environment
        $venvPath = "$ProjectRoot\backend\venv"
        if (-not (Test-Path $venvPath)) {
            Write-ColorOutput "Creating Python virtual environment..." $Blue
            python -m venv $venvPath
        }
        
        # Activate virtual environment and install packages
        $activateScript = "$venvPath\Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            Write-ColorOutput "Installing Python packages..." $Blue
            & $activateScript
            pip install --upgrade pip
            pip install -r $requirementsFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Python dependencies installed successfully"
                return $true
            } else {
                Write-Error "Failed to install Python dependencies"
                return $false
            }
        } else {
            Write-Error "Virtual environment activation script not found"
            return $false
        }
    } catch {
        Write-Error "Error installing Python dependencies: $_"
        return $false
    }
}

function Install-NodeDependencies {
    Write-Header "Installing Node.js Dependencies"
    
    $packageJson = "$ProjectRoot\package.json"
    if (-not (Test-Path $packageJson)) {
        Write-Error "package.json not found: $packageJson"
        return $false
    }
    
    try {
        Set-Location $ProjectRoot
        Write-ColorOutput "Installing Node.js packages..." $Blue
        npm install
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Node.js dependencies installed successfully"
            return $true
        } else {
            Write-Error "Failed to install Node.js dependencies"
            return $false
        }
    } catch {
        Write-Error "Error installing Node.js dependencies: $_"
        return $false
    }
}

function New-ConfigurationFiles {
    Write-Header "Creating Configuration Files"
    
    # Create .env file
    $envFile = "$ConfigPath\.env"
    $envContent = @"
# Open WebUI DXMatrix Edition Configuration

# Database
DATABASE_URL=sqlite:///$($AppDataPath.Replace('\', '/'))/data/owui-dxmatrix.db

# WebUI Settings
WEBUI_AUTH=False
WEBUI_NAME="Open WebUI DXMatrix"
WEBUI_HOSTNAME=localhost
WEBUI_PORT=8080

# Disable Redis-dependent features
ENABLE_REDIS=False
REDIS_URL=

# Ollama (if installed)
OLLAMA_BASE_URL=http://localhost:11434

# Windows Service
SERVICE_NAME=OWUI-DXMatrix
SERVICE_DISPLAY_NAME="Open WebUI DXMatrix Edition"
SERVICE_DESCRIPTION="Open WebUI DXMatrix Edition - Windows Native AI Platform"

# Logging
LOG_LEVEL=INFO
LOG_FILE=$LogPath\owui-dxmatrix.log

# Security
ENABLE_WINDOWS_AUTH=False
ENABLE_SSL=False
SSL_CERT_PATH=
SSL_KEY_PATH=

# Performance
WORKER_PROCESSES=1
MAX_CONNECTIONS=1000
TIMEOUT=300
"@
    
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Success "Created configuration file: $envFile"
    
    # Create Windows Firewall rules
    try {
        Write-ColorOutput "Configuring Windows Firewall..." $Blue
        New-NetFirewallRule -DisplayName "Open WebUI DXMatrix" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -ErrorAction SilentlyContinue
        Write-Success "Windows Firewall rule created"
    } catch {
        Write-Warning "Could not create Windows Firewall rule (run as Administrator)"
    }
}

function Build-Frontend {
    Write-Header "Building Frontend"
    
    try {
        Set-Location $ProjectRoot
        Write-ColorOutput "Building frontend application..." $Blue
        npm run build
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend built successfully"
            return $true
        } else {
            Write-Error "Failed to build frontend"
            return $false
        }
    } catch {
        Write-Error "Error building frontend: $_"
        return $false
    }
}

function New-StartupScripts {
    Write-Header "Creating Startup Scripts"
    
    # Development startup script
    $devScript = "$ProjectRoot\scripts\start-dev.ps1"
    $devContent = @"
# Open WebUI DXMatrix Edition - Development Startup Script

`$ProjectRoot = Split-Path -Parent `$MyInvocation.MyCommand.Path
`$ConfigPath = "`$ProjectRoot\config"

# Load environment variables
if (Test-Path "`$ConfigPath\.env") {
    Get-Content "`$ConfigPath\.env" | ForEach-Object {
        if (`$_ -match '^([^#][^=]+)=(.*)$') {
            `$name = `$matches[1]
            `$value = `$matches[2]
            [Environment]::SetEnvironmentVariable(`$name, `$value, "Process")
        }
    }
}

Write-Host "Starting Open WebUI DXMatrix Edition in development mode..." -ForegroundColor Green

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `$ProjectRoot\backend; .\venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080"

# Start frontend (optional)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `$ProjectRoot; npm run dev"

Write-Host "Development servers started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
"@
    
    Set-Content -Path $devScript -Value $devContent -Encoding UTF8
    Write-Success "Created development startup script: $devScript"
    
    # Production startup script
    $prodScript = "$ProjectRoot\scripts\start-prod.ps1"
    $prodContent = @"
# Open WebUI DXMatrix Edition - Production Startup Script

`$ProjectRoot = Split-Path -Parent `$MyInvocation.MyCommand.Path
`$ConfigPath = "`$ProjectRoot\config"

# Load environment variables
if (Test-Path "`$ConfigPath\.env") {
    Get-Content "`$ConfigPath\.env" | ForEach-Object {
        if (`$_ -match '^([^#][^=]+)=(.*)$') {
            `$name = `$matches[1]
            `$value = `$matches[2]
            [Environment]::SetEnvironmentVariable(`$name, `$value, "Process")
        }
    }
}

Write-Host "Starting Open WebUI DXMatrix Edition in production mode..." -ForegroundColor Green

# Start backend
cd `$ProjectRoot\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8080
"@
    
    Set-Content -Path $prodScript -Value $prodContent -Encoding UTF8
    Write-Success "Created production startup script: $prodScript"
}

function Test-Installation {
    Write-Header "Testing Installation"
    
    try {
        # Test Python environment
        $venvPath = "$ProjectRoot\backend\venv\Scripts\python.exe"
        if (Test-Path $venvPath) {
            Write-Success "Python virtual environment verified"
        } else {
            Write-Error "Python virtual environment not found"
            return $false
        }
        
        # Test Node.js build
        $buildPath = "$ProjectRoot\build"
        if (Test-Path $buildPath) {
            Write-Success "Frontend build verified"
        } else {
            Write-Warning "Frontend build not found (run build step)"
        }
        
        # Test configuration
        $configFile = "$ConfigPath\.env"
        if (Test-Path $configFile) {
            Write-Success "Configuration file verified"
        } else {
            Write-Error "Configuration file not found"
            return $false
        }
        
        Write-Success "Installation test completed successfully!"
        return $true
    } catch {
        Write-Error "Installation test failed: $_"
        return $false
    }
}

# Main installation process
function Start-Installation {
    Write-Header "Open WebUI DXMatrix Edition - Windows Native Installation"
    
    # Check if running as administrator (for some operations)
    if (-not (Test-Administrator)) {
        Write-Warning "Some operations may require Administrator privileges"
    }
    
    # Check prerequisites
    if (-not $SkipPrerequisites) {
        if (-not (Test-Prerequisites)) {
            Write-Error "Prerequisites check failed. Please install required software."
            exit 1
        }
    }
    
    # Create directories
    New-Directories
    
    # Install dependencies
    if (-not (Install-PythonDependencies)) {
        Write-Error "Python dependencies installation failed"
        exit 1
    }
    
    if (-not (Install-NodeDependencies)) {
        Write-Error "Node.js dependencies installation failed"
        exit 1
    }
    
    # Build frontend
    if (-not (Build-Frontend)) {
        Write-Error "Frontend build failed"
        exit 1
    }
    
    # Create configuration files
    New-ConfigurationFiles
    
    # Create startup scripts
    New-StartupScripts
    
    # Test installation
    if (-not (Test-Installation)) {
        Write-Error "Installation test failed"
        exit 1
    }
    
    Write-Header "Installation Complete!"
    Write-Success "Open WebUI DXMatrix Edition has been installed successfully!"
    Write-ColorOutput "`nNext steps:" $Blue
    Write-ColorOutput "1. Start development mode: .\scripts\start-dev.ps1" $Cyan
    Write-ColorOutput "2. Start production mode: .\scripts\start-prod.ps1" $Cyan
    Write-ColorOutput "3. Install as Windows service: .\scripts\install-service.ps1" $Cyan
    Write-ColorOutput "4. Access the application: http://localhost:8080" $Cyan
    Write-ColorOutput "`nConfiguration files are located in: $ConfigPath" $Blue
    Write-ColorOutput "Application data is located in: $AppDataPath" $Blue
}

# Run installation
Start-Installation 