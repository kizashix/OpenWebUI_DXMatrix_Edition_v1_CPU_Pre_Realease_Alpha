# Open WebUI Startup Guide

This guide will help you get Open WebUI running on Windows without Docker, Linux, or WSL.

## Quick Start

### Option 1: PowerShell Script (Recommended)
```powershell
.\start-openwebui.ps1
```

### Option 2: Batch File
```cmd
start-openwebui.bat
```

### Option 3: Manual Commands
If you prefer to run commands manually:

1. **Start Backend:**
   ```cmd
   cd backend
   py -m uvicorn open_webui.main:app --host 127.0.0.1 --port 8080 --reload
   ```

2. **Start Frontend (in a new terminal):**
   ```cmd
   npm run dev -- --port 5173
   ```

3. **Open in Browser:**
   - Frontend: http://localhost:5173
   - Backend API: http://127.0.0.1:8080

## Prerequisites

Before running Open WebUI, make sure you have:

### Required Software
- **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
- **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
- **npm** - Usually comes with Node.js

### Installation Steps
1. **Install Python:**
   - Download Python 3.11+ from python.org
   - Make sure to check "Add Python to PATH" during installation
   - Verify: `py --version`

2. **Install Node.js:**
   - Download Node.js 18+ from nodejs.org
   - This will also install npm
   - Verify: `node --version` and `npm --version`

3. **Clone/Download Open WebUI:**
   - Make sure you're in the Open WebUI directory
   - Should contain `backend/`, `package.json`, etc.

## Script Options

### PowerShell Script Options
```powershell
# Use default ports (8080, 5173)
.\start-openwebui.ps1

# Use custom ports
.\start-openwebui.ps1 -BackendPort 8888 -FrontendPort 3000

# Run only backend
.\start-openwebui.ps1 -BackendOnly

# Run only frontend
.\start-openwebui.ps1 -FrontendOnly

# Skip dependency checks
.\start-openwebui.ps1 -SkipChecks
```

### Batch File Options
```cmd
# Use default ports (8080, 5173)
start-openwebui.bat

# Use custom ports
start-openwebui.bat 8888 3000
```

## What the Scripts Do

1. **Check Dependencies:**
   - Verify Python, Node.js, and npm are installed
   - Check if required files exist

2. **Port Management:**
   - Check if ports are available
   - Offer to kill processes using the ports

3. **Start Servers:**
   - Start backend server (FastAPI)
   - Start frontend server (Svelte/Vite)
   - Verify both servers are running

4. **Provide Status:**
   - Show URLs for both servers
   - Give troubleshooting tips

## Troubleshooting

### Common Issues

#### 1. "Python not found"
**Solution:** Install Python 3.11+ from python.org and make sure to check "Add Python to PATH"

#### 2. "Node.js not found"
**Solution:** Install Node.js 18+ from nodejs.org

#### 3. "Port already in use"
**Solution:** 
- Let the script kill the process automatically, or
- Use different ports: `.\start-openwebui.ps1 -BackendPort 8888 -FrontendPort 3000`

#### 4. "localhost refused to connect"
**Solutions:**
- Check if Windows Firewall is blocking connections
- Make sure both servers are running
- Try accessing http://127.0.0.1 instead of localhost

#### 5. "Backend Required" error
**Solution:** 
- Wait a few more seconds for the backend to fully start
- Refresh the page
- Check the backend terminal for any error messages

#### 6. "Incorrect API key provided"
**Solution:** This is normal if you haven't configured an API key. Open WebUI will work without one for basic functionality.

### Manual Troubleshooting

#### Check if servers are running:
```cmd
# Check backend
netstat -an | findstr :8080

# Check frontend
netstat -an | findstr :5173
```

#### Kill processes on ports:
```cmd
# Find process using port 8080
netstat -ano | findstr :8080

# Kill process (replace PID with actual process ID)
taskkill /f /pid PID
```

#### Check logs:
- Backend logs appear in the backend terminal window
- Frontend logs appear in the frontend terminal window
- Look for error messages in red

### Windows Firewall Issues

If you get connection refused errors:

1. **Allow Python through firewall:**
   - Windows Security → Firewall & network protection
   - Allow an app through firewall
   - Add Python and allow it on private networks

2. **Allow Node.js through firewall:**
   - Same process as above, but for Node.js

3. **Temporarily disable firewall for testing:**
   - Only for testing, not recommended for production

## Development Workflow

### Making Changes
1. **Backend changes:** The backend will auto-reload when you save files
2. **Frontend changes:** The frontend will auto-reload when you save files
3. **Both servers must be running** for the full application to work

### Stopping Servers
- **Close the terminal windows** where the servers are running
- Or press **Ctrl+C** in each terminal window

### Restarting Servers
- Run the startup script again
- Or manually start the servers using the commands above

## Advanced Configuration

### Environment Variables
You can set environment variables before running the scripts:

```cmd
set OPENAI_API_KEY=your_api_key_here
set OLLAMA_BASE_URL=http://localhost:11434
start-openwebui.bat
```

### Custom Backend Configuration
Edit `backend/open_webui/config.py` to customize backend settings.

### Custom Frontend Configuration
Edit `vite.config.ts` or `svelte.config.js` to customize frontend settings.

## Support

If you encounter issues:

1. **Check the logs** in both terminal windows
2. **Verify all prerequisites** are installed correctly
3. **Try different ports** if there are conflicts
4. **Check Windows Firewall** settings
5. **Restart your computer** if all else fails

## File Structure

```
open-webui-main/
├── start-openwebui.ps1      # PowerShell startup script
├── start-openwebui.bat      # Batch startup script
├── STARTUP-GUIDE.md         # This guide
├── backend/                 # Python backend
│   ├── open_webui/
│   └── requirements.txt
├── src/                     # Svelte frontend
├── package.json
└── ...
```

## Notes

- The scripts are designed for Windows only
- They work without Docker, Linux, or WSL
- Both servers must be running for the application to work
- The frontend connects to the backend automatically
- All data is stored locally in the `backend/data/` directory 