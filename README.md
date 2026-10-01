J.A.R.V.I.S. OMEGA

J.A.R.V.I.S. OMEGA is a Windows desktop AI assistant project built with Python and Tkinter.

Project Files

stark_center_english.py — main J.A.R.V.I.S. HUD, AI/voice logic and system interaction layer.

jarvis_gui.py — Control Center with terminal, system monitor, files, themes, settings and logs.

README.md — project documentation.

Features

J.A.R.V.I.S. HUD

Futuristic animated HUD interface

System status display

Interactive central J.A.R.V.I.S. control

Text command input

Voice interaction support

File upload support

Drag-and-drop support when optional dependencies are installed

Code display panel

Clipboard support

Optional weather and camera integrations

Control Center

Interactive Windows terminal

Quick terminal commands

Command history

Live system performance monitoring

File/project tools

Theme and mode selection

API/settings panel

Command and event logs

Terminal output export

Themes

Standard JARVIS

Combat / Red Alert

Stealth

Hacker / Matrix

Requirements

Recommended:

Windows 10 or Windows 11

Python 3.10+

Internet connection for AI/cloud features

Install the common dependencies:

pip install openai psutil requests pillow edge-tts pygame SpeechRecognition

Some optional features may require additional packages.

API Configuration

Never publish API keys on GitHub.

Set your Groq API key as an environment variable.

PowerShell

$env:GROQ_API_KEY="YOUR_API_KEY"

CMD

set GROQ_API_KEY=YOUR_API_KEY

Keep local configuration files and secrets out of the repository.

Running J.A.R.V.I.S.

From the project directory:

python jarvis_gizli_.py

The HUD starts first. The Control Center can be opened from the HUD.

Project Structure

JARVIS-OMEGA/
│
├── jarvis_gizli_.py
├── jarvis_gui.py
└── README.md

Optional local assets and configuration files can be kept in the same directory.

Terminal

The Control Center provides a Windows command terminal.

Example commands:

ipconfig
ping google.com -n 4
dir
systeminfo
tasklist

Internal commands include:

cls
clear
cd <directory>

Terminal commands are executed with the permissions of the current Windows user.

AI Actions

Depending on the configured version, the AI layer can interpret supported action tags such as:

[AC: application]
[KAPAT: process]
[WEB: search query]
[KOD_OLUSTUR: filename | code]
[CMD: command]

Review AI-generated actions before allowing them to execute.

Security

This project can execute operating-system commands and interact with local files.

Do not commit:

API keys

Passwords

Access tokens

Local configuration files

Generated logs

Temporary voice files

Recommended .gitignore:

__pycache__/
*.pyc
.env
config.json
*.log
jarvis_voice.mp3

GitHub

After placing the three project files in a repository:

git init
git add .
git commit -m "Initial JARVIS OMEGA release"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main

Disclaimer

This is an independent personal project provided for development and educational purposes.

System commands, application launching, file operations and AI-generated actions can affect the local computer. Use the project responsibly and review commands before execution.

License

No license is included by default. If you want others to reuse, modify or distribute the project, add a license such as MIT after deciding on the terms you want.
