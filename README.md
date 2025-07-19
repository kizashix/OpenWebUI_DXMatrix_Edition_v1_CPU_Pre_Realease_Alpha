🚀 **Open Web UI - DXMatrix v1.0.1 – CPU-only Windows Native Build** Pre-release

🚀 A lightweight, CPU-only, Windows 11 native build of Open WebUI, reimagined for DXMatrix-style workflows.

Latest Release

💡 What is DXMatrix Edition?
This is a zero-dependency, offline-first fork of Open WebUI designed for:

🖥️ Native Windows 11 execution
🧩 CPU-only inference (no CUDA/GPU required)
❌ No Docker / No WSL / No Linux
✅ Ollama or LM Studio local model support
🧬 Enhanced UI/UX for fast desktop agent dev
⚙️ Installation & Quick Start
🔐 Default Admin Login
After launching the app, log in using the following credentials:

Username: DXM@Matrix.com
Name: admin
Password: admin123

⚠️ Please change the default password after logging in for security reasons.

🔗 Download the latest ZIP release here

🛠 Requirements
Windows 11
Node.js 18+
Python 3.10+
PowerShell 7+
🚀 One-Click Launch (Recommended)
🎯 Run everything in one go!

./start-both-servers.bat

This script will:

✅ Launch the backend with Uvicorn

✅ Start the frontend (SvelteKit / Vite)

✅ Open two terminals so you can monitor both

Once both servers are running, visit:

http://localhost:8000
💡 This is the easiest way to get started — no Docker, no WSL, just native speed and control.

🧰 Manual Setup (Optional)

Extract the ZIP
cd .\DXMatrix-Win11-1.0.1_CPU

Create & activate Python virtual env
python -m venv venv
.\venv\Scripts\Activate.ps1

Install Python backend dependencies
pip install -r backend\requirements.txt

Start backend
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
Then, open a new terminal for frontend:

powershell

From root folder
npm install
npm run dev
Access the UI: http://localhost:3000

🧪 Features (Compared to Upstream)
Feature DXMatrix Edition ✅
Runs natively on Windows ✅
CPU-only (no GPU / CUDA) ✅
No Docker, no WSL ✅
Local Ollama / LM Studio support ✅
Offline-first ✅
Dev-focused tweaks (DXMatrix-ready) ✅

🔗 Credit
This fork is based on the brilliant Open WebUI project by @tjbck. All core functionality is preserved — this build simply retools the experience for Windows-native, no-dependency power users.

╔════════════════════════════════════╗
║ 🧠 DXMatrix by @kizashix ║
║ 💜 https://matrixlogiclabs.com ║
║ ║
║ ║
║ 📩 ammar@ag38.me ║
║ 📩 ag@ag38.me ║
║ 📬 dxm.matrix@gmail.com ║
║ 📬 dx.matrix@outlook.com ║
╚════════════════════════════════════╝

Let's make AI personal, fast, and hacker-friendly again ⚡

Let me know if you want a matching logo banner, dark/light mode badges, or if you'd like me to auto-

Full Changelog: https://github.com/kizashix/OpenWebUI_DXMatrix_Edition_v1_CPU_Pre_Realease_Alpha/commits/OpenWebUI_Windows_Native_Version
