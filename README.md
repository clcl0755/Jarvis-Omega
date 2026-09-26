# 🧠 J.A.R.V.I.S. HUD - OMEGA EDITION

Inspired by Tony Stark's legendary AI assistant, this is a fully unchained autonomous system manager and assistant. Powered by Python, Tkinter, and the Qwen-27b (Groq API) infrastructure.

This is not a simple chatbot; it is an autonomous tool with **full authority** over your operating system (Windows). It can launch and close applications, search the web, generate entire software projects, manage Visual Studio Code, and directly command your PC via PowerShell and CMD.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Groq](https://img.shields.io/badge/API-Groq_Qwen_27b-orange.svg)
![License](https://img.shields.io/badge/License-Stark_Industries-success.svg)

---

## 🚀 Key Features

* **Limitless OS Authority (God Mode):** Thanks to the custom `[CMD: ...]` module, it autonomously executes terminal and PowerShell commands in the background for hardware control, network configurations, web scraping, or script execution.
* **3D Mechanical HUD Interface:** Clickable, 3D-shaded, and dynamically lit vector buttons (Microphone, Camera, Mute). Features a minimalist data display and live voice waveform animation.
* **Voice Communication & Auto-Read:** Speaks to you using Edge-TTS and Google Speech Recognition. When JARVIS is muted, it intelligently calculates your reading speed and keeps the text on the screen for the exact duration needed based on the response length.
* **Dynamic Application Scanner:** If it cannot find a requested program in the registry via the standard `[AC: ...]` command, it uses PowerShell to scan your drives for hidden or portable executable (.exe) software (such as emulators) and launches them instantly.
* **Autonomous Software Developer:** Writes the software or code you request via the `[KOD_OLUSTUR: ...]` command, creates a project folder on your desktop, and automatically opens the project using Visual Studio Code.
* **Live Peripherals:** Dynamic IP-based local weather tracking and an OpenCV-powered integrated live camera feed.

---

## 🛠️ Installation

Follow these steps to boot up the system in your lab (PC):

**1. Clone the Repository**
```bash
git clone [https://github.com/YOUR_USERNAME/JARVIS-HUD-Omega.git](https://github.com/YOUR_USERNAME/JARVIS-HUD-Omega.git)
cd JARVIS-HUD-Omega
2. Install Dependencies
Install the necessary neural networks and modules to run the system:

Bash
pip install -r requirements.txt
3. Insert Your API Key
Before running the code, open stark_merkez.py and insert your Groq API key (or OpenAI key) in the client configuration section:

Python
client = OpenAI(
    base_url="[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)",
    api_key="INSERT_YOUR_API_KEY_HERE",
)
4. Initialize the System

Bash
python stark_merkez.py
🎮 Controls & Interface
Wake System: Toggle the system between Active/Standby modes by clicking the red radar core right in the center of the screen.

Microphone Button: Toggles voice command listening on or off.

Camera Button: Controls the live camera feed in the top right corner.

Mute Button (🔊): Turns off JARVIS's voice feedback, switching the system to silent reading (text) mode.

Command Prompt: Right-click anywhere on the screen to open the hidden text input prompt, allowing you to type commands manually instead of using your voice.

Full Screen: Press F11 to enter full screen mode, and ESC to exit.

⚠️ Warning & Disclaimer
SECURITY WARNING: This AI has the absolute authority to autonomously execute root system commands (CMD/PowerShell). The user is solely responsible for any deleted files, modified registry settings, or downloaded software. Please be fully aware of the consequences of the commands you give to your assistant (especially destructive commands like "delete", "format", or "kill").

Stark Industries cannot be held responsible for lost data or a rogue AI taking over the world.

