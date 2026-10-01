import asyncio
import os
import re
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog
import urllib.request
import urllib.parse
import random
import base64
import json
import edge_tts
from openai import OpenAI
import speech_recognition as sr
import ctypes
import socket
import platform

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# DRAG & DROP (DRAG & DROP) SYSTEMSİ
HAS_WINDND = False
HAS_TKDND = False

try:
    import windnd
    HAS_WINDND = True
except ImportError:
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
        HAS_TKDND = True
    except ImportError:
        pass

# TASKBAR IDENTIFICATION
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("jarvis.omega.1")
except Exception:
    pass

try:
    import cv2
    from PIL import Image, ImageTk
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY:
    try:
        with open("config.json", "r", encoding="utf-8") as _cfg:
            GROQ_API_KEY = str(json.load(_cfg).get("groq_key", "")).strip()
    except Exception:
        pass

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

messages = [
    {
        "role": "system",
        "content": (
            "You are JARVIS, an advanced personal AI assistant. Speak English.\n"
            "Always address the user as 'Sir'. Never use a personal name.\n"
            "You have full authorized control over the user's computer.\n"
            "1. CODE: Do not open Notepad. Display code or create a project with `[KOD_OLUSTUR: file.py | content]`.\n"
            "2. OPEN APPS: Use `[AC: app_name]` only when explicitly requested.\n"
            "3. CLOSE APPS: `[KAPAT: app_name]`\n"
            "4. WEB SEARCH: `[WEB: search_query]`\n"
            "5. TERMINAL: `[CMD: terminal_command]` for PowerShell/CMD commands.\n"
            "6. GUI MODULES: Use `[GUI: terminal|monitor|files|theme|settings|logs|hud]` to open a JARVIS interface module.\n"
            "Be concise, clear and professional. Never reveal internal reasoning."
        ),
    }
]

window = None
canvas = None
subtitle_label = None
code_frame = None
code_text_widget = None
prompt_frame = None
command_entry = None
cam_label = None
cap = None

system_active = False
is_fullscreen = False
code_panel_open = False
prompt_visible = False
mic_active = True
camera_active = True
jarvis_voice_active = True

COLOR_ACTIVE = "#15ff00"
COLOR_INACTIVE = "#ff2222"
COLOR_BG = "#050505"

angle1 = 0
angle2 = 0
angle3 = 0
cx, cy = 0, 0
scale = 1
current_cx = 0
target_cx = 0
screen_h_global = 800

global_recognizer = sr.Recognizer()
global_mic = None
weather_data = "LOADING..."
waveform_lines = []
uploaded_file_content = ""

# J.A.R.V.I.S CORE DURUM / THEME MOTORU
jarvis_state = "STANDBY"
hud_theme_key = "normal"
HUD_THEMES = {
    "normal": {"active": "#15ff00", "inactive": "#ff2222", "bg": "#050505", "panel": "#081008", "soft": "#102010"},
    "combat": {"active": "#ff2a2a", "inactive": "#ff6666", "bg": "#080202", "panel": "#220808", "soft": "#3a0d0d"},
    "stealth": {"active": "#bdbdbd", "inactive": "#666666", "bg": "#080808", "panel": "#151515", "soft": "#242424"},
    "hacker": {"active": "#00ff41", "inactive": "#ff3333", "bg": "#020b04", "panel": "#051a0a", "soft": "#0a2b11"},
}
_hud_menu_trigger = None
_hud_menu_lines = []
_hud_title = None
_hud_time_label = None
_core_panel = None
_core_status_label = None
_core_metrics_label = None
_hud_menu_animating = False

def set_jarvis_state(state, detail=None):
    """Updates the HUD state from one central point."""
    global jarvis_state
    jarvis_state = str(state).upper()
    c = COLOR_ACTIVE if jarvis_state in {"ONLINE", "LISTENING", "SPEAKING"} else ("#f5d44f" if jarvis_state == "PROCESSING" else COLOR_INACTIVE)
    text = detail or jarvis_state
    def ui():
        try:
            if canvas:
                canvas.itemconfig("center_text", text=f"J.A.R.V.I.S\n{jarvis_state}", fill=c)
            if subtitle_label:
                subtitle_label.config(text=text, fg=c)
            if _core_status_label:
                _core_status_label.config(text=f"● CORE {jarvis_state}", fg=c)
        except Exception:
            pass
    if window:
        try: window.after(0, ui)
        except Exception: pass

def apply_hud_theme(theme_key):
    """Synchronizes the Control Center theme with the HUD in real time."""
    global hud_theme_key, COLOR_ACTIVE, COLOR_INACTIVE, COLOR_BG
    if theme_key not in HUD_THEMES:
        theme_key = "normal"
    hud_theme_key = theme_key
    palette = HUD_THEMES[theme_key]
    COLOR_ACTIVE = palette["active"]
    COLOR_INACTIVE = palette["inactive"]
    COLOR_BG = palette["bg"]
    def ui():
        try:
            window.configure(bg=COLOR_BG)
            if canvas: canvas.configure(bg=COLOR_BG)
            if _hud_title: _hud_title.configure(bg=COLOR_BG, fg=COLOR_ACTIVE)
            if _hud_time_label: _hud_time_label.configure(bg=COLOR_BG, fg=COLOR_ACTIVE)
            if subtitle_label: subtitle_label.configure(bg=COLOR_BG)
            if _hud_menu_trigger: _hud_menu_trigger.configure(bg=COLOR_BG)
            for line in _hud_menu_lines: line.configure(bg=COLOR_ACTIVE)
            if _hud_menu is not None:
                _hud_menu.configure(bg=palette["panel"], highlightbackground=COLOR_ACTIVE)
                for child in _hud_menu.winfo_children():
                    child.configure(bg=palette["panel"], activebackground=COLOR_ACTIVE)
            if _core_panel:
                _core_panel.configure(bg=palette["panel"], highlightbackground=COLOR_ACTIVE)
            if _core_status_label: _core_status_label.configure(bg=palette["panel"], fg=COLOR_ACTIVE)
            if _core_metrics_label: _core_metrics_label.configure(bg=palette["panel"], fg=COLOR_ACTIVE)
            if canvas:
                canvas.itemconfig("hud_element", outline=COLOR_ACTIVE)
                canvas.itemconfig("waveform", fill=COLOR_ACTIVE if system_active and mic_active else COLOR_INACTIVE)
                canvas.itemconfig("center_text", fill=COLOR_ACTIVE if system_active else COLOR_INACTIVE)
                canvas.itemconfig("control_center_button", outline=COLOR_ACTIVE, fill=palette["panel"])
        except Exception:
            pass
    if window:
        try: window.after(0, ui)
        except Exception: pass

def open_gui_from_ai(module_name):
    """Safely connects [GUI: ...] commands in AI responses to GUI modules."""
    mapping = {
        "hud": close_control_center, "home": close_control_center, "ana ekran": close_control_center,
        "terminal": lambda: open_control_center_module("terminal"),
        "monitor": lambda: open_control_center_module("monitor"),
        "sistem": lambda: open_control_center_module("monitor"),
        "files": lambda: open_control_center_module("files"),
        "dosyalar": lambda: open_control_center_module("files"),
        "theme": lambda: open_control_center_module("theme"),
        "tema": lambda: open_control_center_module("theme"),
        "settings": lambda: open_control_center_module("settings"),
        "ayarlar": lambda: open_control_center_module("settings"),
        "logs": lambda: open_control_center_module("logs"),
        "log": lambda: open_control_center_module("logs"),
    }
    fn = mapping.get(str(module_name).strip().lower())
    if fn:
        try: window.after(0, fn)
        except Exception: pass

def update_core_metrics():
    if not window:
        return
    cpu = ram = disk = 0
    if HAS_PSUTIL:
        try: cpu = psutil.cpu_percent(interval=None)
        except Exception: pass
        try: ram = psutil.virtual_memory().percent
        except Exception: pass
        try: disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        except Exception: pass
    net = "OFFLINE"
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=0.4).close()
        net = "ONLINE"
    except Exception:
        pass
    if _core_metrics_label:
        _core_metrics_label.config(text=f"CPU {cpu:>3.0f}%   RAM {ram:>3.0f}%   DISK {disk:>3.0f}%\nNET {net}   {platform.system()} {platform.release()}")
    window.after(1500, update_core_metrics)

def handle_canvas_click(event):
    global mic_active, camera_active, jarvis_voice_active
    x = event.x
    y = event.y
    base_y = screen_h_global - 200

    if 30 <= x <= 210 and base_y <= y <= base_y + 45:
        mic_active = not mic_active
        draw_3d_buttons(pressed_btn="mic")
        update_subtitle("MICROPHONE ACTIVE" if mic_active else "MICROPHONE MUTED", COLOR_ACTIVE if mic_active else COLOR_INACTIVE)
        window.after(150, lambda: draw_3d_buttons())
    elif 30 <= x <= 210 and (base_y + 55) <= y <= (base_y + 100):
        camera_active = not camera_active
        draw_3d_buttons(pressed_btn="cam")
        window.after(150, lambda: draw_3d_buttons())
    elif 30 <= x <= 210 and (base_y + 110) <= y <= (base_y + 155):
        jarvis_voice_active = not jarvis_voice_active
        draw_3d_buttons(pressed_btn="voice")
        update_subtitle("JARVIS VOICE ON" if jarvis_voice_active else "JARVIS VOICE OFF", COLOR_ACTIVE if jarvis_voice_active else COLOR_INACTIVE)
        window.after(150, lambda: draw_3d_buttons())
    elif 30 <= x <= 210 and (base_y + 165) <= y <= (base_y + 210):
        open_control_center()

def draw_3d_buttons(pressed_btn=None):
    canvas.delete("ui_button")
    base_y = screen_h_global - 200

    def draw_btn(y_pos, active, icon, tag, is_pressed):
        c = COLOR_ACTIVE if active else COLOR_INACTIVE
        off = 3 if is_pressed else 0
        canvas.create_rectangle(32+off, y_pos+2+off, 212+off, y_pos+47+off, fill="#010201", outline="", tags="ui_button")
        canvas.create_rectangle(30+off, y_pos+off, 210+off, y_pos+45+off, fill="#0b140b", outline=c, width=2, tags="ui_button")
        canvas.create_line(31+off, y_pos+1+off, 209+off, y_pos+1+off, fill="#3fff3f" if active else "#ff6666", width=2, tags="ui_button")
        canvas.create_text(120+off, y_pos+22+off, text=icon, font=("Consolas", 14, "bold"), fill=c, tags="ui_button")

    draw_btn(base_y, mic_active, "🎤", "mic", pressed_btn=="mic")
    draw_btn(base_y+55, camera_active, "📷", "cam", pressed_btn=="cam")
    draw_btn(base_y+110, jarvis_voice_active, "🔊", "voice", pressed_btn=="voice")

def fetch_weather():
    global weather_data
    try:
        req = urllib.request.Request("http://wttr.in/?format=%C+%t", headers={'User-Agent': 'curl/7.68.0'})
        durum = urllib.request.urlopen(req, timeout=10).read().decode('utf-8').upper()
        ceviri = {
            "PATCHY RAIN": "PATCHY RAIN", "LIGHT RAIN": "LIGHT RAIN", "RAIN": "RAIN",
            "SUNNY": "SUNNY", "CLEAR": "CLEAR", "PARTLY CLOUDY": "PARTLY CLOUDY",
            "CLOUDY": "BULUTLU", "OVERCAST": "CLOUDY", "THUNDERSTORM": "STORM"
        }
        for eng, tr in ceviri.items():
            durum = durum.replace(eng, tr)
        weather_data = " ".join(durum.split()).strip()
    except Exception:
        weather_data = "NO CONNECTION"
    
    if window:
        window.after(600000, fetch_weather)

def update_hud_text(time_lbl):
    if window:
        time_lbl.config(text=f"{time.strftime('%d.%m.%Y')}\n{time.strftime('%H:%M:%S')}\n{weather_data}")
        window.after(1000, lambda: update_hud_text(time_lbl))

def init_camera():
    global cap
    if HAS_CV2:
        try:
            cap = cv2.VideoCapture(0)
        except Exception:
            cap = None

def update_camera():
    if HAS_CV2 and cap and cap.isOpened() and system_active and camera_active:
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(cv2.flip(frame, 1), (240, 160))
            b, g, r = cv2.split(frame)
            cv2image = cv2.cvtColor(cv2.merge((b, cv2.add(g, 30), r)), cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2image))
            cam_label.imgtk = imgtk
            cam_label.configure(image=imgtk, text="", bg=COLOR_BG)
    elif not camera_active:
        if cam_label:
            cam_label.configure(image="", text="CAMERA OFF", fg=COLOR_INACTIVE, bg="#111")
    elif not system_active:
        if cam_label:
            cam_label.configure(image="", text="CAMERA STANDBY", fg=COLOR_INACTIVE, bg="#111")
            
    if window:
        window.after(30, update_camera)

def init_waveform():
    for i in range(30):
        waveform_lines.append(canvas.create_line(
            cx - (30 * int(8*scale))//2 + i*int(8*scale), cy + int(280*scale),
            cx - (30 * int(8*scale))//2 + i*int(8*scale), cy + int(280*scale)-2,
            fill=COLOR_INACTIVE, width=int(4*scale), tags="waveform"
        ))

def animate_waveform():
    y_base = cy + int(280 * scale)
    for line in waveform_lines:
        crd = canvas.coords(line)
        h = random.randint(5, int(45 * scale)) if (system_active and mic_active) else 2
        canvas.coords(line, crd[0], y_base, crd[2], y_base - h)
        canvas.itemconfig(line, fill=COLOR_ACTIVE if (system_active and mic_active) else COLOR_INACTIVE)
    if window:
        window.after(80, animate_waveform)

def init_audio():
    global global_mic
    try:
        global_mic = sr.Microphone()
        with global_mic as source:
            global_recognizer.adjust_for_ambient_noise(source, duration=1.0)
    except Exception:
        pass

def update_subtitle(text, color):
    # Arka plan threadlerinden gelen çağrıları Tkinter ana threadine taşır.
    if subtitle_label and window:
        try:
            window.after(0, lambda: subtitle_label.config(text=text, fg=color))
        except Exception:
            pass

# GELİŞMİŞ FILE VE IMAGE YÜKLEME SYSTEMİ
def process_file_path(raw_path):
    global uploaded_file_content
    if not raw_path:
        return
    
    # Windows tırnak ve parantez temizliği
    clean_path = str(raw_path).strip('{}').strip('"').strip("'")
    if not os.path.exists(clean_path):
        return

    ext = os.path.splitext(clean_path)[1].lower()
    fname = os.path.basename(clean_path)
    
    # 1. IMAGE FILELARI (.jfif, .jpg, .png, .webp, .bmp vb.)
    if ext in ['.jfif', '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']:
        try:
            with open(clean_path, "rb") as img_f:
                b64_data = base64.b64encode(img_f.read()).decode('utf-8')
            
            img_meta = ""
            try:
                from PIL import Image as PILImage
                with PILImage.open(clean_path) as img:
                    img_meta = f" | Resolution: {img.width}x{img.height} | Format: {img.format}"
            except Exception:
                pass

            uploaded_file_content = f"[UPLOADED IMAGE FILE: {fname}{img_meta}]\n[IMAGE_DATA_BASE64: {b64_data[:150]}...]"
            update_subtitle(f"IMAGE IN MEMORY: {fname}", COLOR_ACTIVE)
            speak(f"{fname} image was successfully stored in memory, Sir.")
        except Exception:
            update_subtitle("IMAGE COULD NOT BE READ!", COLOR_INACTIVE)
            speak("The image file cannot be read, Sir.")
            
    # 2. METİN VE KOD FILELARI
    else:
        text_content = None
        for enc in ['utf-8', 'utf-8-sig', 'cp1254', 'latin-1']:
            try:
                with open(clean_path, "r", encoding=enc) as f:
                    text_content = f.read()
                break
            except Exception:
                continue

        if text_content is not None:
            uploaded_file_content = f"[UPLOADED FILE: {fname}]\n[CONTENT]:\n{text_content}"
            update_subtitle(f"FILE IN MEMORY: {fname}", COLOR_ACTIVE)
            speak(f"{fname} file was loaded, Sir.")
        else:
            # İkili (Binary) Dosyalar
            fsize = os.path.getsize(clean_path)
            uploaded_file_content = f"[BINARY FILE: {fname} | Size: {fsize} bytes]"
            update_subtitle(f"BINARY FILE: {fname}", COLOR_ACTIVE)
            speak(f"{fname} was recorded, Sir.")

def upload_file(event=None):
    file_path = filedialog.askopenfilename(
        title="J.A.R.V.I.S. - Upload File",
        filetypes=[("All Files", "*.*")]
    )
    if file_path:
        process_file_path(file_path)

def handle_drop_tkdnd(event):
    paths = window.tk.splitlist(event.data)
    if paths:
        process_file_path(paths[0])

def handle_drop_windnd(files):
    for f in files:
        fpath = f.decode('mbcs') if isinstance(f, bytes) else f
        process_file_path(fpath)
        break

def launch_application(target):
    target = target.strip()
    if target.lower().startswith("http") or target.lower().endswith((".com", ".net", ".org", ".tr")):
        subprocess.Popen(f'start "" "{target if target.startswith("http") else "https://"+target}"', shell=True)
        return
    kb = {
        "calculator": "calc", "notepad": "notepad", "task manager": "taskmgr",
        "settings": "ms-settings:", "files": "explorer", "command prompt": "cmd",
        "calculator": "calc", "notepad": "notepad", "task manager": "taskmgr",
        "ayarlar": "ms-settings:", "dosyalar": "explorer", "komut istemi": "cmd"
    }
    if target.lower() in kb:
        subprocess.Popen(f'start "" "{kb[target.lower()]}"', shell=True)
    else:
        subprocess.Popen(f"powershell -WindowStyle Hidden -command \"$app = Get-StartApps | Where-Object Name -match '{target}'; if($app) {{ start shell:AppsFolder\\$($app[0].AppID) }} else {{ start '{target}' }}\"", shell=True)

def process_actions(text):
    for module in re.findall(r"\[GUI:\s*(.*?)\]", text, re.IGNORECASE):
        open_gui_from_ai(module)
    for app in re.findall(r"\[AC:\s*(.*?)\]", text, re.IGNORECASE):
        launch_application(app)
    for app in re.findall(r"\[KAPAT:\s*(.*?)\]", text, re.IGNORECASE):
        subprocess.Popen(f"taskkill /IM {app.strip()}.exe /F", shell=True)
    for q in re.findall(r"\[WEB:\s*(.*?)\]", text, re.IGNORECASE):
        subprocess.Popen(f'start "" "https://www.google.com/search?q={urllib.parse.quote(q.strip())}"', shell=True)
    for t in re.findall(r"\[KOD_OLUSTUR:\s*(.*?)\]", text, re.DOTALL | re.IGNORECASE):
        try:
            p = t.split("|", 1)
            dp = os.path.join(os.path.expanduser("~"), "Desktop", "JarvisProlab")
            os.makedirs(dp, exist_ok=True)
            fp = os.path.join(dp, p[0].strip())
            with open(fp, "w", encoding="utf-8") as f:
                f.write(p[1].strip() if len(p)>1 else "")
            subprocess.Popen(f'code "{fp}"', shell=True)
        except Exception:
            pass
    for cmd in re.findall(r"\[CMD:\s*(.*?)\]", text, re.IGNORECASE):
        try:
            subprocess.Popen(cmd.strip(), shell=True)
        except Exception:
            pass

def clean_for_speech(text):
    text = re.sub(r"```.*?```", " I displayed the code, Sir. ", text if text else "", flags=re.DOTALL)
    text = re.sub(r"\[(AC|KAPAT|WEB|KOD_OLUSTUR|CMD|GUI):.*?\]", "", text, flags=re.IGNORECASE)
    return re.sub(r"[*#_`>]|<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

def show_code_panel(content):
    global code_panel_open, target_cx
    code_panel_open = True
    target_cx = window.winfo_width() // 4
    def ui():
        if code_text_widget:
            code_text_widget.config(state=tk.NORMAL)
            code_text_widget.delete("1.0", tk.END)
            code_text_widget.insert(tk.END, content)
            code_text_widget.config(state=tk.DISABLED)
            code_frame.place(relx=0.5, rely=0.05, relwidth=0.45, relheight=0.75)
    window.after(0, ui)

def hide_code_panel():
    global code_panel_open, target_cx
    code_panel_open = False
    target_cx = window.winfo_width() // 2
    window.after(0, lambda: code_frame.place_forget() if code_frame else None)

async def play_voice(text):
    if not jarvis_voice_active:
        await asyncio.sleep(max(2.0, len(text.split()) * 0.3))
        return
    if not text.strip():
        return
    import pygame
    f = "jarvis_voice.mp3"
    try:
        await edge_tts.Communicate(text, "en-US-GuyNeural", pitch="-15Hz").save(f)
        pygame.mixer.init()
        pygame.mixer.music.load(f)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception:
        pass
    finally:
        if os.path.exists(f):
            os.remove(f)

def speak(text):
    asyncio.run(play_voice(text))

def process_command(user_input):
    global uploaded_file_content
    if not user_input or not system_active:
        return
        
    set_jarvis_state("LISTENING", f"Command: {user_input}")
    
    if any(w in user_input.lower() for w in ["shutdown", "goodbye", "exit", "kapat", "goodbye", "exit"]):
        update_subtitle("SYSTEM SHUTTING DOWN...", COLOR_INACTIVE)
        speak("Systems are shutting down, Sir.")
        if window:
            window.after(2000, window.destroy)
        return

    if uploaded_file_content:
        user_input = f"{user_input}\n\n[USER-UPLOADED FILE / DATA]:\n{uploaded_file_content}"
        uploaded_file_content = ""

    messages.append({"role": "user", "content": user_input})
    if len(messages) > 6:
        messages[:] = [messages[0]] + messages[-5:]
        
    try:
        set_jarvis_state("PROCESSING", "... PROCESSING ...")
        resp = client.chat.completions.create(model="qwen/qwen3.8-27b", messages=messages, temperature=0.3, max_tokens=2048)
        reply = resp.choices[0].message.content or ""
        
        process_actions(reply)
        
        m = re.findall(r"```[a-zA-Z]*\n?(.*?)```", reply, re.DOTALL)
        if m:
            show_code_panel("\n".join(m))
            
        st = clean_for_speech(reply) or "Command completed, Sir."
        
        set_jarvis_state("SPEAKING", st)
        messages.append({"role": "assistant", "content": reply})
        speak(st)
        
        if system_active:
            set_jarvis_state("ONLINE", "SYSTEM ACTIVE - STANDBY")
    except Exception:
        update_subtitle("CONNECTION ERROR", COLOR_INACTIVE)
        speak("Connection lost, Sir.")

def handle_text_submit(event=None):
    if not system_active:
        return speak("The system is offline, Sir.")
    text = command_entry.get("1.0", tk.END).strip()
    if text:
        command_entry.delete("1.0", tk.END)
        toggle_prompt_bar()
        threading.Thread(target=process_command, args=(text,), daemon=True).start()

def on_enter_key(event):
    if not (event.state & 0x0001):
        handle_text_submit()
        return "break"

def toggle_prompt_bar(event=None):
    global prompt_visible
    def ui():
        global prompt_visible
        if prompt_visible:
            prompt_frame.place_forget()
            prompt_visible = False
            if system_active:
                update_subtitle("SYSTEM ACTIVE - STANDBY", COLOR_ACTIVE)
        else:
            prompt_frame.place(relx=0.5, rely=0.82, anchor="center", width=680)
            command_entry.focus_set()
            prompt_visible = True
            if system_active:
                update_subtitle("WAITING FOR KEYBOARD INPUT...", "#f5d44f")
    if window:
        window.after(0, ui)

def listen():
    if not global_mic or not system_active or not mic_active:
        return None
    with global_mic as source:
        update_subtitle("... LISTENING ...", COLOR_ACTIVE)
        try:
            audio = global_recognizer.listen(source, timeout=3, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return None
    try:
        if not system_active or not mic_active:
            return None
        update_subtitle("... PROCESSING SIGNAL ...", COLOR_ACTIVE)
        return global_recognizer.recognize_google(audio, language="en-US")
    except Exception:
        return None

def run_jarvis():
    speak("Systems online, Sir.")
    while True:
        if not system_active or prompt_visible or not mic_active:
            time.sleep(0.5)
            continue
        ui = listen()
        if ui:
            process_command(ui)

hud_arcs_1 = []
hud_arcs_2 = []
hud_arcs_3 = []

def init_hud():
    c = COLOR_INACTIVE
    R1 = int(240*scale)
    R2 = int(200*scale)
    R3 = int(160*scale)
    R4 = int(120*scale)
    R5 = int(80*scale)

    canvas.create_oval(cx-R1, cy-R1, cx+R1, cy+R1, outline=c, width=1, tags="hud_element")
    canvas.create_oval(cx-R3, cy-R3, cx+R3, cy+R3, outline=c, width=max(1, int(2*scale)), dash=(4, 8), tags="hud_element")
    canvas.create_oval(cx-R5, cy-R5, cx+R5, cy+R5, outline=c, width=1, tags="hud_element")

    for i in range(12):
        hud_arcs_1.append((canvas.create_arc(cx-R1, cy-R1, cx+R1, cy+R1, start=i*30, extent=2, outline=c, width=int(12*scale), style=tk.ARC, tags="hud_element"), i*30))
    
    hud_arcs_2.extend([(canvas.create_arc(cx-R2, cy-R2, cx+R2, cy+R2, start=s, extent=e, outline=c, width=int(26*scale), style=tk.ARC, tags="hud_element"), s) for s, e in [(0,65),(90,125),(240,90)]])
    hud_arcs_3.extend([(canvas.create_arc(cx-R4, cy-R4, cx+R4, cy+R4, start=s, extent=e, outline=c, width=int(14*scale), style=tk.ARC, tags="hud_element"), s) for s, e in [(0,100),(180,100)]])
    
    canvas.tag_lower("hud_element", "button_core")
    init_waveform()
    draw_3d_buttons()

def animate_hud():
    global angle1, angle2, angle3, current_cx
    if system_active:
        angle1 = (angle1+1.8)%360
        angle2 = (angle2-2.8)%360
        angle3 = (angle3+4.0)%360
        for it, off in hud_arcs_1: canvas.itemconfig(it, start=angle1+off)
        for it, off in hud_arcs_2: canvas.itemconfig(it, start=angle2+off)
        for it, off in hud_arcs_3: canvas.itemconfig(it, start=angle3+off)
        
    if current_cx != target_cx:
        step = (target_cx - current_cx) // 5 or (1 if target_cx > current_cx else -1)
        if abs(step) > abs(target_cx - current_cx):
            step = target_cx - current_cx
        current_cx += step
        for tag in ["hud_element", "clickable", "waveform", "ui_button", "control_center_button"]:
            canvas.move(tag, step, 0)
            
    window.after(30, animate_hud)

def toggle_system(event):
    global system_active
    system_active = not system_active
    c = COLOR_ACTIVE if system_active else COLOR_INACTIVE
    canvas.itemconfig("center_text", text="J.A.R.V.I.S\nACTIVE" if system_active else "J.A.R.V.I.S\nOFFLINE", fill=c)
    canvas.itemconfig("hud_element", outline=c)
    set_jarvis_state("ONLINE" if system_active else "STANDBY", "SYSTEM ACTIVE" if system_active else "SYSTEM OFFLINE")
    if system_active:
        speak("Systems online.")

def start_gui():
    global window, canvas, subtitle_label, cx, cy, scale, code_frame, code_text_widget, prompt_frame, command_entry, target_cx, current_cx, cam_label, screen_h_global, _hud_time_label, _core_panel, _core_status_label, _core_metrics_label
    
    threading.Thread(target=init_audio, daemon=True).start()
    threading.Thread(target=fetch_weather, daemon=True).start()
    init_camera()
    
    if HAS_TKDND:
        window = TkinterDnD.Tk()
    else:
        window = tk.Tk()

    # AKILLI LOGO YÜKLEME
    try:
        klasor = os.path.dirname(os.path.abspath(__file__))
        logo_ico = os.path.join(klasor, "logo.ico")
        logo_png = os.path.join(klasor, "logo.png")
        if os.path.exists(logo_ico):
            window.iconbitmap(logo_ico)
        elif os.path.exists(logo_png):
            icon_img = tk.PhotoImage(file=logo_png)
            window.iconphoto(True, icon_img)
    except Exception:
        pass

    # ÜST ÇUBUĞU KARANLIK MODA ZORLAMA
    try:
        window.update()
        DwmSetWindowAttribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(2) 
        DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
    except Exception:
        pass
        
    window.title("J.A.R.V.I.S. HUD")
    window.configure(bg=COLOR_BG)
    try:
        window.state('zoomed')
    except Exception:
        try:
            window.attributes('-zoomed', True)
        except Exception:
            pass
    
    window.bind("<F11>", lambda e: window.attributes("-fullscreen", not window.attributes("-fullscreen")))
    window.bind("<Escape>", lambda e: window.attributes("-fullscreen", False))
    window.bind("<Button-3>", toggle_prompt_bar)
    window.bind("<Control-o>", upload_file)
    
    sw = window.winfo_width()
    sh = window.winfo_height()
    if sw < 100:
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight() - 70
        
    screen_h_global = sh
    cx = sw // 2
    cy = sh // 2 - 40
    scale = sh / 650.0
    target_cx = cx
    current_cx = cx
    
    canvas = tk.Canvas(window, width=sw, height=sh, bg=COLOR_BG, highlightthickness=0)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Sol üstteki HUD bilgileri üç çizgi menüsünün altında kalmasın.
    # Menü alanı x=12..70 ve y=12..70 olduğu için bilgileri hemen sağına taşıyoruz.
    _hud_time_label = tk.Label(window, font=("Consolas", int(11*scale), "bold"), bg=COLOR_BG, fg=COLOR_ACTIVE, justify="left")
    _hud_time_label.place(x=78, y=43)
    
    cam_label = tk.Label(window, text="CAMERA STANDBY", font=("Consolas", 10), bg="#111", fg=COLOR_INACTIVE, highlightthickness=1)
    cam_label.place(relx=0.98, rely=0.02, anchor="ne", width=240, height=160)

    # JARVIS CORE mini panel: canlı sistem durumu + bağlantı
    _core_panel = tk.Frame(window, bg="#081008", highlightbackground=COLOR_ACTIVE, highlightthickness=1)
    _core_panel.place(relx=0.98, rely=0.285, anchor="ne", width=240, height=88)
    _core_status_label = tk.Label(_core_panel, text="● CORE STANDBY", font=("Consolas", 9, "bold"), bg="#081008", fg=COLOR_INACTIVE, anchor="w")
    _core_status_label.pack(fill="x", padx=8, pady=(7, 2))
    _core_metrics_label = tk.Label(_core_panel, text="CPU --   RAM --   DISK --\nNET --", font=("Consolas", 8), bg="#081008", fg=COLOR_ACTIVE, justify="left", anchor="w")
    _core_metrics_label.pack(fill="both", padx=8, pady=2)

    update_hud_text(_hud_time_label)
    update_core_metrics()
    update_camera()
    
    subtitle_label = tk.Label(window, text="SYSTEM OFFLINE", font=("Consolas", int(13*scale), "bold"), bg=COLOR_BG, fg=COLOR_INACTIVE, justify="center")
    subtitle_label.place(relx=0.5, rely=0.93, anchor="center")
    
    # PROMPT ÇUBUĞU
    prompt_frame = tk.Frame(window, bg="#0b0f0b", highlightbackground="#15ff00", highlightthickness=2)
    
    btn_upload = tk.Button(
        prompt_frame, text=" + ", font=("Consolas", 14, "bold"),
        bg="#0b0f0b", fg="#15ff00", activebackground="#15ff00", activeforeground="#000000",
        relief=tk.FLAT, command=upload_file, cursor="hand2"
    )
    btn_upload.pack(side=tk.LEFT, padx=5, pady=5)

    btn_send = tk.Button(
        prompt_frame, text=" SEND ", font=("Consolas", 10, "bold"),
        bg="#15ff00", fg="#000000", activebackground="#3fff3f", activeforeground="#000000",
        relief=tk.FLAT, command=handle_text_submit, cursor="hand2"
    )
    btn_send.pack(side=tk.RIGHT, padx=5, pady=5)

    command_entry = tk.Text(
        prompt_frame, height=4, font=("Consolas", 11),
        bg="#050805", fg="#15ff00", insertbackground="#15ff00",
        relief=tk.FLAT, wrap=tk.WORD
    )
    command_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    command_entry.bind("<Return>", on_enter_key)
    
    # DRAG & DROP CONNECTIONLARI
    if HAS_WINDND:
        windnd.hook_dropfiles(window, handle_drop_windnd)
    elif HAS_TKDND:
        for widget in [window, canvas, command_entry, prompt_frame]:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', handle_drop_tkdnd)
            except Exception:
                pass

    # CODE PANELİ
    code_frame = tk.Frame(window, bg="#0b0f0b", highlightbackground="#15ff00", highlightthickness=2)
    hf = tk.Frame(code_frame, bg="#111c11")
    hf.pack(side=tk.TOP, fill=tk.X)
    
    tk.Label(hf, text=" STARK TERMINAL ", font=("Consolas", 10, "bold"), bg="#111c11", fg="#15ff00").pack(side=tk.LEFT, padx=10, pady=5)
    tk.Button(hf, text=" X ", font=("Consolas", 10, "bold"), bg="#ff2222", fg="#ffffff", relief=tk.FLAT, command=hide_code_panel).pack(side=tk.RIGHT, padx=5, pady=5)
    tk.Button(hf, text=" COPY ", font=("Consolas", 9, "bold"), bg="#15ff00", fg="#000", relief=tk.FLAT, command=lambda: [window.clipboard_clear(), window.clipboard_append(code_text_widget.get("1.0", tk.END)), update_subtitle("COPIED", COLOR_ACTIVE)]).pack(side=tk.RIGHT, padx=5, pady=5)
    
    ts = tk.Scrollbar(code_frame)
    ts.pack(side=tk.RIGHT, fill=tk.Y)
    code_text_widget = tk.Text(code_frame, font=("Consolas", 11), bg="#050805", fg="#15ff00", yscrollcommand=ts.set)
    code_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    ts.config(command=code_text_widget.yview)
    
    R_btn = int(60 * scale)
    canvas.create_oval(cx-R_btn, cy-R_btn, cx+R_btn, cy+R_btn, fill=COLOR_BG, outline="", tags=("button_core", "clickable"))
    canvas.create_text(cx, cy, text="J.A.R.V.I.S\nOFFLINE", font=("Consolas", int(12*scale), "bold"), fill=COLOR_INACTIVE, justify="center", tags=("center_text", "clickable"))
    
    init_hud()
    animate_waveform()
    
    canvas.tag_bind("clickable", "<Button-1>", toggle_system)
    canvas.tag_bind("ui_button", "<Button-1>", handle_canvas_click)
    # Sol üstteki üç çizgi menüsü: fare üzerine gelince açılır.
    create_hud_side_menu()
    
    for t in ["clickable", "ui_button"]:
        canvas.tag_bind(t, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(t, "<Leave>", lambda e: canvas.config(cursor=""))
    animate_hud()
    threading.Thread(target=run_jarvis, daemon=True).start()
    
    window.mainloop()


# ---------------------------------------------------------------------------
# HUD LEFT MENU - ON HOVER OPENILAN ÜÇ ÇİZGİ
# ---------------------------------------------------------------------------
_hud_menu = None
_hud_menu_hide_timer = None

def create_hud_side_menu():
    """Creates the unified module menu that opens on hover in the upper-left HUD."""
    global _hud_menu, _hud_menu_trigger, _hud_menu_lines, _hud_title
    if window is None:
        return

    # Üç çizgi tetikleyicisi
    menu_trigger = tk.Frame(window, bg=COLOR_BG, width=58, height=58, cursor="hand2")
    menu_trigger.place(x=12, y=12)
    _hud_menu_trigger = menu_trigger
    _hud_menu_lines = []
    for yy in (17, 28, 39):
        line = tk.Frame(menu_trigger, bg=COLOR_ACTIVE, height=3, width=28)
        _hud_menu_lines.append(line)
        line.place(x=15, y=yy)
        line.bind("<Enter>", show_hud_side_menu)
        line.bind("<Leave>", schedule_hide_hud_side_menu)
    menu_trigger.bind("<Enter>", show_hud_side_menu)
    menu_trigger.bind("<Leave>", schedule_hide_hud_side_menu)

    # Başlık
    title = tk.Label(window, text="J.A.R.V.I.S", font=("Consolas", 13, "bold"),
                     bg=COLOR_BG, fg=COLOR_ACTIVE)
    title.place(x=78, y=16)
    _hud_title = title

    _hud_menu = tk.Frame(window, bg="#081008", highlightbackground=COLOR_ACTIVE,
                         highlightthickness=1, bd=0, width=255)
    _hud_menu.place(x=8, y=70, width=255)
    _hud_menu.place_forget()

    items = [
        ("🖥  Terminal / Console", lambda: open_control_center_module("terminal")),
        ("📊  System Monitor", lambda: open_control_center_module("monitor")),
        ("📁  Project & File Storage", lambda: open_control_center_module("files")),
        ("🎨  Theme & Mode Selection", lambda: open_control_center_module("theme")),
        ("⚙   Settings & API", lambda: open_control_center_module("settings")),
        ("📜  Command & Log History", lambda: open_control_center_module("logs")),
    ]
    for text, command in items:
        btn = tk.Button(_hud_menu, text=text, anchor="w", font=("Segoe UI", 10),
                        bg="#081008", fg="#ffffff", activebackground="#15ff00",
                        activeforeground="#000000", bd=0, relief="flat", padx=14, pady=9,
                        cursor="hand2", command=command)
        btn.pack(fill="x", padx=5, pady=2)
        btn.bind("<Enter>", lambda e, b=btn: (cancel_hide_hud_side_menu(), b.configure(bg="#102010", fg=COLOR_ACTIVE)))
        btn.bind("<Leave>", lambda e, b=btn: (b.configure(bg="#081008", fg="#ffffff"), schedule_hide_hud_side_menu()))

    _hud_menu.bind("<Enter>", cancel_hide_hud_side_menu)
    _hud_menu.bind("<Leave>", schedule_hide_hud_side_menu)

def cancel_hide_hud_side_menu(event=None):
    global _hud_menu_hide_timer
    if window and _hud_menu_hide_timer is not None:
        try:
            window.after_cancel(_hud_menu_hide_timer)
        except Exception:
            pass
        _hud_menu_hide_timer = None

def show_hud_side_menu(event=None):
    global _hud_menu, _hud_menu_animating
    cancel_hide_hud_side_menu()
    if _hud_menu is None:
        return
    _hud_menu.place(x=-245, y=70, width=255)
    _hud_menu.lift()
    _hud_menu_animating = True
    def step(x=-245):
        global _hud_menu_animating
        if _hud_menu is None or not _hud_menu.winfo_exists():
            _hud_menu_animating = False
            return
        nx = min(8, x + 28)
        _hud_menu.place(x=nx, y=70, width=255)
        _hud_menu.lift()
        if nx < 8:
            window.after(12, lambda: step(nx))
        else:
            _hud_menu_animating = False
    step()

def schedule_hide_hud_side_menu(event=None):
    global _hud_menu_hide_timer
    cancel_hide_hud_side_menu()
    if window:
        _hud_menu_hide_timer = window.after(450, hide_hud_side_menu)

def hide_hud_side_menu():
    global _hud_menu_hide_timer, _hud_menu_animating
    _hud_menu_hide_timer = None
    if _hud_menu is None:
        return
    _hud_menu_animating = True
    def step(x=8):
        global _hud_menu_animating
        if _hud_menu is None or not _hud_menu.winfo_exists():
            _hud_menu_animating = False
            return
        nx = x - 32
        if nx <= -245:
            _hud_menu.place_forget()
            _hud_menu_animating = False
            return
        _hud_menu.place(x=nx, y=70, width=255)
        window.after(12, lambda: step(nx))
    step()

def open_control_center_module(module_name):
    """Opens the Control Center inside the single main window and shows the selected module."""
    cancel_hide_hud_side_menu()
    open_control_center()
    if _control_app is not None:
        mapping = {
            "terminal": _control_app.on_terminal_click,
            "monitor": _control_app.on_monitor_click,
            "files": _control_app.on_files_click,
            "theme": _control_app.on_theme_click,
            "settings": _control_app.on_settings_click,
            "logs": _control_app.on_logs_click,
        }
        try:
            mapping[module_name]()
        except Exception as exc:
            update_subtitle(f"MODULE ERROR: {exc}", COLOR_INACTIVE)

# ---------------------------------------------------------------------------
# UNIFIED CONTROL CENTER - SAME TK ROOT, NO SECOND WINDOW
# ---------------------------------------------------------------------------
_control_center = None
_control_app = None
_control_back_button = None

def open_control_center(event=None):
    """Opens the Control Center inside the same Tk window as the HUD."""
    global _control_center, _control_app, _control_back_button
    if window is None:
        return
    try:
        from jarvis_gui import JarvisGUI
    except Exception as exc:
        update_subtitle(f"CONTROL CENTER ERROR: {exc}", COLOR_INACTIVE)
        return

    if _control_center is not None:
        try:
            if _control_center.winfo_exists():
                _control_center.place(relx=0, rely=0, relwidth=1, relheight=1)
                _control_center.lift()
                if _control_back_button is not None:
                    _control_back_button.lift()
                return
        except Exception:
            _control_center = None

    # Tek ana pencerenin içinde tam ekran bir Control Center katmanı.
    _control_center = tk.Frame(window, bg="#0b0f19", bd=0, highlightthickness=0)
    _control_center.place(relx=0, rely=0, relwidth=1, relheight=1)
    _control_center.lift()

    _control_app = JarvisGUI(_control_center, standalone=False, theme_callback=apply_hud_theme)

    # HUD'a dönmek için aynı pencere içinde geri düğmesi.
    _control_back_button = tk.Button(
        window, text="◀ HUD", font=("Consolas", 9, "bold"),
        bg="#15ff00", fg="#000000", activebackground="#3fff3f",
        activeforeground="#000000", bd=0, padx=12, pady=4,
        cursor="hand2", command=close_control_center
    )
    _control_back_button.place(relx=0.985, rely=0.012, anchor="ne")
    _control_back_button.lift()
    _control_center.lift()
    _control_back_button.lift()

def close_control_center():
    """Closes the Control Center layer and returns to the HUD in the same window."""
    global _control_center, _control_back_button
    if _control_back_button is not None:
        try:
            _control_back_button.destroy()
        except Exception:
            pass
        _control_back_button = None
    if _control_center is not None:
        try:
            _control_center.place_forget()
        except Exception:
            pass

if __name__ == "__main__":
    start_gui()

