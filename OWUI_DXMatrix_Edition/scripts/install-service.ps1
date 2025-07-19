# Open WebUI DXMatrix Edition - Windows Service Installation Script
# This script installs Open WebUI as a Windows service

param(
    [switch]$Remove,
    [switch]$Force,
    [string]$ServiceName = "OWUI-DXMatrix",
    [string]$DisplayName = "Open WebUI DXMatrix Edition",
    [string]$Description = "Open WebUI DXMatrix Edition - Windows Native AI Platform"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Script variables
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$AppDataPath = "$env:LOCALAPPDATA\owui-dxmatrix"
$LogPath = "$AppDataPath\logs"

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

function Test-ServiceExists {
    param([string]$ServiceName)
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    return $null -ne $service
}

function Remove-WindowsService {
    Write-Header "Removing Windows Service"
    
    if (-not (Test-Administrator)) {
        Write-Error "Administrator privileges required to remove Windows service"
        return $false
    }
    
    if (Test-ServiceExists $ServiceName) {
        try {
            # Stop service if running
            $service = Get-Service -Name $ServiceName
            if ($service.Status -eq "Running") {
                Write-ColorOutput "Stopping service..." $Blue
                Stop-Service -Name $ServiceName -Force
                Start-Sleep -Seconds 5
            }
            
            # Remove service
            Write-ColorOutput "Removing service..." $Blue
            $scPath = "$env:SystemRoot\System32\sc.exe"
            & $scPath delete $ServiceName
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Service removed successfully"
                return $true
            } else {
                Write-Error "Failed to remove service"
                return $false
            }
        } catch {
            Write-Error "Error removing service: $_"
            return $false
        }
    } else {
        Write-Warning "Service '$ServiceName' not found"
        return $true
    }
}

function Install-WindowsService {
    Write-Header "Installing Windows Service"
    
    if (-not (Test-Administrator)) {
        Write-Error "Administrator privileges required to install Windows service"
        return $false
    }
    
    # Check if service already exists
    if (Test-ServiceExists $ServiceName) {
        if ($Force) {
            Write-Warning "Service already exists. Removing existing service..."
            if (-not (Remove-WindowsService)) {
                return $false
            }
        } else {
            Write-Error "Service '$ServiceName' already exists. Use -Force to overwrite."
            return $false
        }
    }
    
    # Verify installation files
    $venvPath = "$ProjectRoot\backend\venv\Scripts\python.exe"
    $mainPath = "$ProjectRoot\backend\main.py"
    
    if (-not (Test-Path $venvPath)) {
        Write-Error "Python virtual environment not found: $venvPath"
        return $false
    }
    
    if (-not (Test-Path $mainPath)) {
        Write-Error "Main application file not found: $mainPath"
        return $false
    }
    
    try {
        # Create service wrapper script
        $wrapperScript = "$ProjectRoot\scripts\service-wrapper.ps1"
        $wrapperContent = @"
# Open WebUI DXMatrix Edition - Service Wrapper Script

`$ProjectRoot = "$ProjectRoot"
`$AppDataPath = "$AppDataPath"
`$LogPath = "$LogPath"

# Set working directory
Set-Location `$ProjectRoot

# Load environment variables
`$envFile = "`$ProjectRoot\config\.env"
if (Test-Path `$envFile) {
    Get-Content `$envFile | ForEach-Object {
        if (`$_ -match '^([^#][^=]+)=(.*)$') {
            `$name = `$matches[1]
            `$value = `$matches[2]
            [Environment]::SetEnvironmentVariable(`$name, `$value, "Process")
        }
    }
}

# Create log directory if it doesn't exist
if (-not (Test-Path `$LogPath)) {
    New-Item -ItemType Directory -Path `$LogPath -Force | Out-Null
}

# Start the application
`$logFile = "`$LogPath\service.log"
`$errorFile = "`$LogPath\service-error.log"

try {
    # Activate virtual environment and start application
    `$venvActivate = "`$ProjectRoot\backend\venv\Scripts\Activate.ps1"
    if (Test-Path `$venvActivate) {
        & `$venvActivate
        python -m uvicorn main:app --host 0.0.0.0 --port 8080 2>&1 | Tee-Object -FilePath `$logFile
    } else {
        throw "Virtual environment activation script not found"
    }
} catch {
    `$_.Exception.Message | Out-File -FilePath `$errorFile -Append
    throw
}
"@
        
        Set-Content -Path $wrapperScript -Value $wrapperContent -Encoding UTF8
        Write-Success "Created service wrapper script: $wrapperScript"
        
        # Create NSSM service (if available) or use sc.exe
        $nssmPath = "$ProjectRoot\tools\nssm.exe"
        
        if (Test-Path $nssmPath) {
            # Use NSSM for better service management
            Write-ColorOutput "Using NSSM for service installation..." $Blue
            
            # Install service with NSSM
            & $nssmPath install $ServiceName "powershell.exe" "-ExecutionPolicy Bypass -File `"$wrapperScript`""
            & $nssmPath set $ServiceName DisplayName $DisplayName
            & $nssmPath set $ServiceName Description $Description
            & $nssmPath set $ServiceName AppDirectory $ProjectRoot
            & $nssmPath set $ServiceName Start SERVICE_AUTO_START
            
            # Set recovery options
            & $nssmPath set $ServiceName AppRestartDelay 10000
            & $nssmPath set $ServiceName AppStopMethodSkip 0
            & $nssmPath set $ServiceName AppStopMethodConsole 1500
            & $nssmPath set $ServiceName AppStopMethodWindow 1500
            & $nssmPath set $ServiceName AppStopMethodThreads 1500
            
            # Set log options
            & $nssmPath set $ServiceName AppStdout "$LogPath\service-stdout.log"
            & $nssmPath set $ServiceName AppStderr "$LogPath\service-stderr.log"
            
        } else {
            # Use sc.exe as fallback
            Write-ColorOutput "Using sc.exe for service installation..." $Blue
            
            $scPath = "$env:SystemRoot\System32\sc.exe"
            $binPath = "powershell.exe -ExecutionPolicy Bypass -File `"$wrapperScript`""
            
            # Create service
            & $scPath create $ServiceName binPath= $binPath DisplayName= $DisplayName start= auto
            
            # Set description
            & $scPath description $ServiceName $Description
            
            # Set failure actions
            & $scPath failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/restart/60000
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Windows service installed successfully"
            
            # Start the service
            Write-ColorOutput "Starting service..." $Blue
            Start-Service -Name $ServiceName
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Service started successfully"
            } else {
                Write-Warning "Service installed but failed to start"
            }
            
            return $true
        } else {
            Write-Error "Failed to install Windows service"
            return $false
        }
        
    } catch {
        Write-Error "Error installing Windows service: $_"
        return $false
    }
}

function Test-ServiceInstallation {
    Write-Header "Testing Service Installation"
    
    try {
        if (Test-ServiceExists $ServiceName) {
            $service = Get-Service -Name $ServiceName
            Write-Success "Service found: $($service.DisplayName)"
            Write-ColorOutput "Status: $($service.Status)" $Blue
            Write-ColorOutput "Start Type: $($service.StartType)" $Blue
            
            # Test service health
            Start-Sleep -Seconds 10
            $service = Get-Service -Name $ServiceName
            if ($service.Status -eq "Running") {
                Write-Success "Service is running successfully"
                
                # Test HTTP endpoint
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 10 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        Write-Success "Application is responding to health checks"
                    } else {
                        Write-Warning "Application responded with status: $($response.StatusCode)"
                    }
                } catch {
                    Write-Warning "Could not reach application health endpoint: $_"
                }
                
                return $true
            } else {
                Write-Error "Service is not running. Status: $($service.Status)"
                return $false
            }
        } else {
            Write-Error "Service not found"
            return $false
        }
    } catch {
        Write-Error "Error testing service: $_"
        return $false
    }
}

function Show-ServiceInfo {
    Write-Header "Service Information"
    
    if (Test-ServiceExists $ServiceName) {
        $service = Get-Service -Name $ServiceName
        Write-ColorOutput "Service Name: $($service.Name)" $Blue
        Write-ColorOutput "Display Name: $($service.DisplayName)" $Blue
        Write-ColorOutput "Status: $($service.Status)" $Blue
        Write-ColorOutput "Start Type: $($service.StartType)" $Blue
        
        Write-ColorOutput "`nService Commands:" $Yellow
        Write-ColorOutput "  Start:   Start-Service -Name '$ServiceName'" $Cyan
        Write-ColorOutput "  Stop:    Stop-Service -Name '$ServiceName'" $Cyan
        Write-ColorOutput "  Restart: Restart-Service -Name '$ServiceName'" $Cyan
        Write-ColorOutput "  Status:  Get-Service -Name '$ServiceName'" $Cyan
        
        Write-ColorOutput "`nLog Files:" $Yellow
        Write-ColorOutput "  Service Log: $LogPath\service.log" $Cyan
        Write-ColorOutput "  Stdout Log: $LogPath\service-stdout.log" $Cyan
        Write-ColorOutput "  Stderr Log: $LogPath\service-stderr.log" $Cyan
        
        Write-ColorOutput "`nApplication URL: http://localhost:8080" $Green
    } else {
        Write-Warning "Service '$ServiceName' not found"
    }
}

# Main execution
if ($Remove) {
    if (Remove-WindowsService) {
        Write-Success "Service removal completed"
    } else {
        Write-Error "Service removal failed"
        exit 1
    }
} else {
    Write-Header "Open WebUI DXMatrix Edition - Windows Service Installation"
    
    if (Install-WindowsService) {
        if (Test-ServiceInstallation) {
            Write-Header "Installation Complete!"
            Write-Success "Windows service installed and running successfully!"
            Show-ServiceInfo
        } else {
            Write-Error "Service installation test failed"
            exit 1
        }
    } else {
        Write-Error "Service installation failed"
        exit 1
    }
} 