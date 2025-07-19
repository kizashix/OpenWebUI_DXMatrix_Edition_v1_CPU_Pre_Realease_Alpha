🚀 Open Web UI - DXMatrix v1.0.1 – CPU-only Windows Native Build (Latest Pre-release)

A lightweight, CPU-only, Windows 11 native build of Open WebUI, reimagined for DXMatrix-style workflows.

💡 What is DXMatrix Edition?
This is a zero-dependency, offline-first fork of Open WebUI designed for:

🖥️ Native Windows 11 execution

🧩 CPU-only inference (no CUDA/GPU required)

❌ No Docker / No WSL / No Linux

✅ Local model support via Ollama or LM Studio

🧬 Enhanced UI/UX for fast desktop agent dev

⚙️ Installation & Quick Start
🔐 Default Admin Login
Use the following credentials to log in:

Username: DXM@Matrix.com
Name: admin
Password: admin123
⚠️ Important: Change the default password after your first login for security.

🔗 Download the Latest ZIP Release
👉 Download DXMatrix-Win11-1.0.1_CPU.zip
🧾 SHA256: bd510853424976ec989117c8cc4130242ecb0a6001f618930eff5fc2bc01c62f
📦 Size: 773 MB

🚀 One-Click Launch (Recommended)
From the root folder:

bash
./start-both-servers.bat

This will:

✅ Launch the backend with Uvicorn

✅ Start the frontend via SvelteKit (Vite)

✅ Open two terminals for monitoring

Visit: http://localhost:8000

🧰 Manual Setup (Optional)
bash
# Extract the ZIP
cd .\DXMatrix-Win11-1.0.1_CPU

# Create & activate virtualenv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt

# Start backend
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
Open new terminal for frontend:

powershell
# From project root
npm install
npm run dev
Frontend runs at: http://localhost:5173

🧪 Feature Comparison (vs Upstream)
Feature	DXMatrix Edition
Native Windows support	✅
CPU-only (no GPU/CUDA)	✅
No Docker / No WSL	✅
Local Ollama / LM Studio	✅
Offline-first	✅
DXMatrix workflow optimized	✅

👥 Credits & Acknowledgments
Forked from @tjbck's Open WebUI. This edition is retooled for Windows-native, no-dependency, power users.

╔════════════════════════════════════╗
║        🧠 DXMatrix by @kizashix    ║
║ 💜 https://matrixlogiclabs.com     ║
║ 📩 ammar@ag38.me                   ║
║ 📩 ag@ag38.me                      ║
║ 📬 dxm.matrix@gmail.com            ║
║ 📬 dx.matrix@outlook.com           ║
╚════════════════════════════════════╝

Let's make AI personal, fast, and hacker-friendly again ⚡

📜 Full Changelog:
🔗 GitHub Commits

👥 Contributors:
@kizashix · @tjbck

