# Open WebUI DXMatrix Edition - Windows Native

## Overview

Open WebUI DXMatrix Edition is a fully native Windows implementation of Open WebUI, eliminating all dependencies on Docker, WSL, or Linux components. This edition provides Windows users with a streamlined installation and operation experience using only native Windows technologies.

## Key Features

- ✅ **100% Windows Native** - No Docker, no WSL, no Linux dependencies
- ✅ **SQLite Database** - Lightweight, file-based database
- ✅ **Windows Service Integration** - Runs as native Windows service
- ✅ **Windows Security Integration** - Firewall, authentication, certificates
- ✅ **Performance Optimized** - Windows-specific optimizations
- ✅ **Easy Installation** - PowerShell-based installation scripts
- ✅ **Comprehensive Logging** - Windows Event Log integration

## Quick Start

### Prerequisites

- Windows 10/11 (64-bit)
- Python 3.11+
- Node.js 18.13.0+
- Git for Windows
- Visual Studio Build Tools (for Python packages)

### Installation

```powershell
# Clone the repository
git clone https://github.com/your-repo/OWUI_DXMatrix_Edition.git
cd OWUI_DXMatrix_Edition

# Run the installation script
.\scripts\install.ps1
```

### Running

```powershell
# Development mode
.\scripts\start-dev.ps1

# Production mode
.\scripts\start-prod.ps1

# Install as Windows service
.\scripts\install-service.ps1
```

## Project Structure

```
OWUI_DXMatrix_Edition/
├── backend/              # Python backend (FastAPI)
├── src/                  # Frontend source (SvelteKit)
├── config/               # Configuration files
├── scripts/              # PowerShell installation scripts
├── tools/                # Windows-specific tools
├── docs/                 # Documentation
└── README.md            # This file
```

## Features

### Core AI Capabilities
- Multi-model support (Ollama, OpenAI, Azure, Google)
- RAG (Retrieval Augmented Generation)
- Document processing (20+ formats)
- Image generation
- Audio processing (STT/TTS)

### Windows Integration
- Native Windows service
- Windows Event Log integration
- Windows Firewall configuration
- Windows authentication support
- Performance monitoring

### Security
- Windows certificate store integration
- User permission management
- Antivirus exclusion guidance
- Secure configuration management

## Configuration

### Environment Variables

Create `config\.env`:
```env
# Database
DATABASE_URL=sqlite:///C:/Users/%USERNAME%/AppData/Local/owui-dxmatrix/data.db

# WebUI Settings
WEBUI_AUTH=False
WEBUI_NAME="Open WebUI DXMatrix"
WEBUI_HOSTNAME=localhost
WEBUI_PORT=8080

# Ollama (if installed)
OLLAMA_BASE_URL=http://localhost:11434

# Windows Service
SERVICE_NAME=OWUI-DXMatrix
SERVICE_DISPLAY_NAME="Open WebUI DXMatrix Edition"
```

## Troubleshooting

### Common Issues

1. **Python package installation errors**
   - Install Visual Studio Build Tools
   - Use: `pip install --only-binary=all -r requirements.txt`

2. **Port conflicts**
   - Check: `netstat -ano | findstr :8080`
   - Kill process: `taskkill /PID [PID] /F`

3. **Permission errors**
   - Run PowerShell as Administrator
   - Check Windows Firewall settings

### Logs

- **Application logs**: `C:\Users\%USERNAME%\AppData\Local\owui-dxmatrix\logs\`
- **Windows Event Log**: Event Viewer → Windows Logs → Application
- **Service logs**: `C:\Users\%USERNAME%\AppData\Local\owui-dxmatrix\service.log`

## Development

### Building from Source

```powershell
# Setup development environment
.\scripts\setup-dev.ps1

# Build frontend
npm run build

# Run backend in development mode
python -m uvicorn backend.main:app --reload
```

### Testing

```powershell
# Run tests
.\scripts\test.ps1

# Run specific test suite
.\scripts\test-backend.ps1
.\scripts\test-frontend.ps1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the Open WebUI License (revised BSD-3-Clause).

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## Roadmap

- [ ] Windows Service Manager integration
- [ ] Advanced Windows security features
- [ ] Performance monitoring dashboard
- [ ] Automated backup system
- [ ] Update management system 