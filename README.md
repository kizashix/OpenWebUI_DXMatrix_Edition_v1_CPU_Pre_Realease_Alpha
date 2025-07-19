# DXMatrix Edition – Native Windows Build 💻🧠

> 🚀 A lightweight, **CPU-only**, **Windows 11 native build** of [Open WebUI](https://github.com/open-webui/open-webui), reimagined for DXMatrix-style workflows.

[![Latest Release](https://img.shields.io/github/v/release/kizashix/docs?label=Release)](https://github.com/kizashix/docs/releases)
[![Repo Size](https://img.shields.io/github/repo-size/kizashix/docs)](https://github.com/kizashix/docs)
[![Forked From](https://img.shields.io/badge/forked%20from-open--webui%2Fopen--webui-blue?logo=github)](https://github.com/open-webui/open-webui)

---

## 💡 What is DXMatrix Edition?

This is a **zero-dependency**, **offline-first** fork of Open WebUI designed for:

- 🖥️ Native Windows 11 execution  
- 🧩 CPU-only inference (no CUDA/GPU required)  
- ❌ No Docker / No WSL / No Linux  
- ✅ Ollama or LM Studio local model support  
- 🧬 Enhanced UI/UX for fast desktop agent dev  

---

## ⚙️ Installation & Quick Start

🔗 [**Download the latest ZIP release here**](https://github.com/kizashix/docs/releases/latest)

### 🛠 Requirements

- Windows 11  
- Node.js 18+  
- Python 3.10+  
- PowerShell 7+

---

### 🚀 One-Click Launch (Recommended)

> 🎯 **Run everything in one go!**

```bat
./start-both-servers.bat
This script will:

✅ Launch the backend with Uvicorn

✅ Start the frontend (SvelteKit / Vite)

✅ Open two terminals so you can monitor both

Once both servers are running, visit:

arduino
Copy
Edit
http://localhost:3000
💡 This is the easiest way to get started — no Docker, no WSL, just native speed and control.

🧰 Manual Setup (Optional)
powershell
Copy
Edit
# Extract the ZIP
cd .\DXMatrix-Win11-1.0.1_CPU

# Create & activate Python virtual env
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python backend dependencies
pip install -r backend\requirements.txt

# Start backend
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
Then, open a new terminal for frontend:

powershell
Copy
Edit
# From root folder
npm install
npm run dev
Access the UI: http://localhost:3000

🧪 Features (Compared to Upstream)
Feature	DXMatrix Edition ✅
Runs natively on Windows	✅
CPU-only (no GPU / CUDA)	✅
No Docker, no WSL	✅
Local Ollama / LM Studio support	✅
Offline-first	✅
Dev-focused tweaks (DXMatrix-ready)	✅

🔗 Credit
This fork is based on the brilliant Open WebUI project by @tjbck. All core functionality is preserved — this build simply retools the experience for Windows-native, no-dependency power users.

🧠 Author
Made with 💜 by @kizashix
🌐 https://matrixlogiclabs.com
📩 ammar@ag38.me

