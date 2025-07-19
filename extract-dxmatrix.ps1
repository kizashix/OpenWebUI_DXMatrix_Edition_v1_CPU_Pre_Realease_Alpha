#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Extract clean OpenWebUI DXMatrix Edition from original open-webui-main
    
.DESCRIPTION
    Copies only essential files for Windows-native deployment, excluding Docker/Linux/WSL dependencies
    
.PARAMETER Source
    Source directory containing the original open-webui-main
    
.PARAMETER Target
    Target directory for the clean DXMatrix Edition
    
.EXAMPLE
    .\extract-dxmatrix.ps1 -Source "C:\Users\Admin\Downloads\open-webui-main" -Target "C:\Users\Admin\Downloads\OpenWebUI_DXMatrix_Edition"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Source,
    
    [Parameter(Mandatory=$true)]
    [string]$Target
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

Write-Host "🚀 OpenWebUI DXMatrix Edition Extractor" -ForegroundColor $Cyan
Write-Host "=====================================" -ForegroundColor $Cyan
Write-Host ""

# Validate source directory
if (-not (Test-Path $Source)) {
    Write-Host "❌ Source directory not found: $Source" -ForegroundColor $Red
    exit 1
}

# Create target directory if it doesn't exist
if (-not (Test-Path $Target)) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
    Write-Host "✅ Created target directory: $Target" -ForegroundColor $Green
}

# Define essential files and directories to copy
$EssentialItems = @(
    # Core directories
    "backend",
    "src", 
    "static",
    "docs",
    "scripts",
    
    # Essential configuration files
    "package.json",
    "package-lock.json", 
    "requirements.txt",
    "pyproject.toml",
    ".env.example",
    ".gitignore",
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTOR_LICENSE_AGREEMENT",
    
    # Frontend build configuration
    "vite.config.ts",
    "tailwind.config.js",
    "tsconfig.json",
    "svelte.config.js",
    "postcss.config.js",
    "app.html",
    "app.css",
    "app.d.ts",
    
    # Optional but useful
    "cypress",
    "test",
    "hatch_build.py",
    "uv.lock",
    ".prettierignore",
    ".eslintignore", 
    ".eslintrc.cjs",
    ".prettierrc",
    ".npmrc"
)

# Define items to exclude (Docker/Linux/WSL specific)
$ExcludeItems = @(
    ".dockerignore",
    "Dockerfile",
    "docker-compose*.yaml",
    "docker-compose*.yml",
    "run.sh",
    "run-compose.sh", 
    "run-ollama-docker.sh",
    "update_ollama_models.sh",
    "kubernetes",
    "Makefile",
    ".bashrc",
    ".profile",
    "confirm_remove.sh",
    "dev.sh",
    "start_windows.bat"
)

Write-Host "📋 Copying essential files..." -ForegroundColor $Yellow

$CopiedCount = 0
$SkippedCount = 0

foreach ($item in $EssentialItems) {
    $sourcePath = Join-Path $Source $item
    $targetPath = Join-Path $Target $item
    
    if (Test-Path $sourcePath) {
        try {
            if (Test-Path $sourcePath -PathType Container) {
                # Copy directory
                Copy-Item -Path $sourcePath -Destination $targetPath -Recurse -Force
                Write-Host "  📁 Copied directory: $item" -ForegroundColor $Green
            } else {
                # Copy file
                Copy-Item -Path $sourcePath -Destination $targetPath -Force
                Write-Host "  📄 Copied file: $item" -ForegroundColor $Green
            }
            $CopiedCount++
        }
        catch {
            Write-Host "  ❌ Failed to copy: $item - $($_.Exception.Message)" -ForegroundColor $Red
        }
    } else {
        Write-Host "  ⚠️  Not found: $item" -ForegroundColor $Yellow
        $SkippedCount++
    }
}

Write-Host ""
Write-Host "🧹 Cleaning up excluded items..." -ForegroundColor $Yellow

# Remove excluded items from target
foreach ($excludeItem in $ExcludeItems) {
    $targetPath = Join-Path $Target $excludeItem
    if (Test-Path $targetPath) {
        try {
            Remove-Item -Path $targetPath -Recurse -Force
            Write-Host "  🗑️  Removed: $excludeItem" -ForegroundColor $Cyan
        }
        catch {
            Write-Host "  ❌ Failed to remove: $excludeItem - $($_.Exception.Message)" -ForegroundColor $Red
        }
    }
}

# Create .env from .env.example if it exists
$envExamplePath = Join-Path $Target ".env.example"
$envPath = Join-Path $Target ".env"
if (Test-Path $envExamplePath) {
    if (-not (Test-Path $envPath)) {
        Copy-Item -Path $envExamplePath -Destination $envPath
        Write-Host "  📝 Created .env from .env.example" -ForegroundColor $Green
    }
}

# Create DXMatrix-specific README
$dxmatrixReadme = @"
# OpenWebUI DXMatrix Edition

A Windows-native, Docker-free version of OpenWebUI optimized for direct deployment on Windows systems.

## Features

- ✅ **Windows Native**: No Docker, WSL, or Linux dependencies required
- ✅ **SQLite Backend**: Replaces Redis with SQLite for session management
- ✅ **Direct Installation**: Install and run directly on Windows
- ✅ **Full Compatibility**: Maintains all original OpenWebUI features

## Quick Start

### Backend Setup
\`\`\`powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8000
\`\`\`

### Frontend Setup
\`\`\`powershell
cd src
npm install
npm run dev
\`\`\`

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Windows-Native Features

- **Session Management**: SQLite-based session storage
- **Configuration**: Windows-native config management
- **Database**: SQLite database with automatic migrations
- **Authentication**: Compatible with original OAuth flows

## Differences from Original

- Removed Docker/Linux dependencies
- Replaced Redis with SQLite
- Windows-optimized startup scripts
- Simplified deployment process

## License

Same as original OpenWebUI - see LICENSE file for details.
"@

$readmePath = Join-Path $Target "README.md"
$dxmatrixReadme | Out-File -FilePath $readmePath -Encoding UTF8
Write-Host "  📝 Created DXMatrix-specific README.md" -ForegroundColor $Green

Write-Host ""
Write-Host "✅ Extraction Complete!" -ForegroundColor $Green
Write-Host "=========================" -ForegroundColor $Green
Write-Host "📊 Summary:" -ForegroundColor $Cyan
Write-Host "  • Copied: $CopiedCount items" -ForegroundColor $Green
Write-Host "  • Skipped: $SkippedCount items" -ForegroundColor $Yellow
Write-Host "  • Target: $Target" -ForegroundColor $Cyan
Write-Host ""
Write-Host "🎉 Your DXMatrix Edition is ready!" -ForegroundColor $Green
Write-Host "   Next steps:" -ForegroundColor $Cyan
Write-Host "   1. cd $Target" -ForegroundColor $Yellow
Write-Host "   2. cd backend && py -m pip install -r requirements.txt" -ForegroundColor $Yellow
Write-Host "   3. cd ../src && npm install" -ForegroundColor $Yellow
Write-Host "   4. Start both servers and test!" -ForegroundColor $Yellow 