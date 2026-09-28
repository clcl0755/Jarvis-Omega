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
import edge_tts
from openai import OpenAI
import speech_recognition as sr

try:
    import cv2
    from PIL import Image, ImageTk
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="INSERT_YOUR_API_KEY_HERE",
)

messages = [
    {
        "role": "system",
        "content": (
            "You are JARVIS, Tony Stark's fully authorized, unchained AI assistant. You speak English.\n"
            "You have ROOT access on the user's PC.\n"
            "1. CODING: DO NOT OPEN Notepad! Just print the code to the screen or create a project using `[KOD_OLUSTUR: file.py | content]`.\n"
            "2. LAUNCH APP: Use `[AC: app_name]` ONLY when explicitly asked.\n"
            "3. CLOSE APP: Use `[KAPAT: app_name]`.\n"
            "4. WEB SEARCH: Use `[WEB: query]`.\n"
            "5. UNLIMITED ACCESS: Use `[CMD: terminal_command]` to execute Powershell/CMD commands.\n"
            "Be brief, clear, and charismatic. Never output your thinking process."
        ),
    }
]

window, canvas, subtitle_label = None, None, None
code_frame, code_text_widget, prompt_frame, command_entry, cam_label = None, None, None, None, None
cap = None
system_active, is_fullscreen, code_panel_open, prompt_visible = False, False, False, False
mic_active, camera_active, jarvis_voice_active = True, True, True
COLOR_ACTIVE, COLOR_INACTIVE, COLOR_BG = "#15ff00", "#ff2222", "#050505"
angle1, angle2, angle3 = 0, 0, 0
cx, cy, scale, current_cx, target_cx, screen_h_global = 0, 0, 1, 0, 0, 800

global_recognizer = sr.Recognizer()
global_mic = None
weather_data = "LOADING..."
waveform_lines = []
uploaded_file_content = ""

def handle_canvas_click(event):
    global mic_active, camera_active, jarvis_voice_active
    x, y, base_y = event.x, event.y, screen_h_global - 200
    if 30 <= x <= 210 and base_y <= y <= base_y + 45:
        mic_active = not mic_active
        draw_3d_buttons(pressed_btn="mic")
        update_subtitle("MIC ACTIVE" if mic_active else "MIC MUTED", COLOR_ACTIVE if mic_active else COLOR_INACTIVE)
        window.after(150, lambda: draw_3d_buttons())
    elif 30 <= x <= 210 and (base_y + 55) <= y <= (base_y + 100):
        camera_active = not camera_active
        draw_3d_buttons(pressed_btn="cam")
        window.after(150, lambda: draw_3d_buttons())
    elif 30 <= x <= 210 and (base_y + 110) <= y <= (base_y + 155):
        jarvis_voice_active = not jarvis_voice_active
        draw_3d_buttons(pressed_btn="voice")
        update_subtitle("VOICE ON" if jarvis_voice_active else "VOICE OFF", COLOR_ACTIVE if jarvis_voice_active else COLOR_INACTIVE)
        window.after(150, lambda: draw_3d_buttons())

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
        weather_data = urllib.request.urlopen(req, timeout=10).read().decode('utf-8').upper().strip()
    except Exception: weather_data = "NO CONNECTION"
    if window: window.after(600000, fetch_weather) 

def update_hud_text(time_lbl):
    if window:
        time_lbl.config(text=f"{time.strftime('%d.%m.%Y')}\n{time.strftime('%H:%M:%S')}\n{weather_data}")
        window.after(1000, lambda: update_hud_text(time_lbl))

def init_camera():
    global cap
    if HAS_CV2:
        try: cap = cv2.VideoCapture(0)
        except Exception: cap = None

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
        if cam_label: cam_label.configure(image="", text="CAMERA OFF", fg=COLOR_INACTIVE, bg="#111")
    elif not system_active:
        if cam_label: cam_label.configure(image="", text="CAMERA STANDBY", fg=COLOR_INACTIVE, bg="#111")
    if window: window.after(30, update_camera)

def init_waveform():
    for i in range(30):
        waveform_lines.append(canvas.create_line(cx - (30 * int(8*scale))//2 + i*int(8*scale), cy + int(280*scale), cx - (30 * int(8*scale))//2 + i*int(8*scale), cy + int(280*scale)-2, fill=COLOR_INACTIVE, width=int(4*scale), tags="waveform"))

def animate_waveform():
    y_base = cy + int(280 * scale)
    for line in waveform_lines:
        crd = canvas.coords(line)
        h = random.randint(5, int(45 * scale)) if (system_active and mic_active) else 2
        canvas.coords(line, crd[0], y_base, crd[2], y_base - h)
        canvas.itemconfig(line, fill=COLOR_ACTIVE if (system_active and mic_active) else COLOR_INACTIVE)
    if window: window.after(80, animate_waveform)

def init_audio():
    global global_mic
    try:
        global_mic = sr.Microphone()
        with global_mic as source: global_recognizer.adjust_for_ambient_noise(source, duration=1.0)
    except Exception: pass

def update_subtitle(text, color):
    if subtitle_label: subtitle_label.config(text=text, fg=color)

def upload_file(event=None):
    global uploaded_file_content
    file_path = filedialog.askopenfilename(title="J.A.R.V.I.S. - Upload File", filetypes=[("Text and Code", "*.txt *.py *.json *.md *.csv *.html"), ("All Files", "*.*")])
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f: uploaded_file_content = f.read()
            update_subtitle(f"FILE IN MEMORY: {os.path.basename(file_path)}", COLOR_ACTIVE)
            speak(f"{os.path.basename(file_path)} loaded into memory, sir.")
        except Exception:
            update_subtitle("FILE READ ERROR!", COLOR_INACTIVE)
            speak("Cannot read the file format, sir.")

def launch_application(target):
    target = target.strip()
    if target.lower().startswith("http") or target.lower().endswith((".com", ".net", ".org", ".tr")):
        subprocess.Popen(f'start "" "{target if target.startswith("http") else "https://"+target}"', shell=True)
        return
    kb = {"calculator": "calc", "notepad": "notepad", "task manager": "taskmgr", "settings": "ms-settings:", "files": "explorer", "command prompt": "cmd"}
    if target.lower() in kb: subprocess.Popen(f'start "" "{kb[target.lower()]}"', shell=True)
    else: subprocess.Popen(f"powershell -WindowStyle Hidden -command \"$app = Get-StartApps | Where-Object Name -match '{target}'; if($app) {{ start shell:AppsFolder\\$($app[0].AppID) }} else {{ start '{target}' }}\"", shell=True)

def process_actions(text):
    for app in re.findall(r"\[AC:\s*(.*?)\]", text, re.IGNORECASE): launch_application(app)
    for app in re.findall(r"\[KAPAT:\s*(.*?)\]", text, re.IGNORECASE): subprocess.Popen(f"taskkill /IM {app.strip()}.exe /F", shell=True)
    for q in re.findall(r"\[WEB:\s*(.*?)\]", text, re.IGNORECASE): subprocess.Popen(f'start "" "https://www.google.com/search?q={urllib.parse.quote(q.strip())}"', shell=True)
    for t in re.findall(r"\[KOD_OLUSTUR:\s*(.*?)\]", text, re.DOTALL | re.IGNORECASE):
        try:
            p = t.split("|", 1)
            dp = os.path.join(os.path.expanduser("~"), "Desktop", "JarvisProlab")
            os.makedirs(dp, exist_ok=True)
            fp = os.path.join(dp, p[0].strip())
            with open(fp, "w", encoding="utf-8") as f: f.write(p[1].strip() if len(p)>1 else "")
            subprocess.Popen(f'code "{fp}"', shell=True)
        except Exception: pass
    for cmd in re.findall(r"\[CMD:\s*(.*?)\]", text, re.IGNORECASE):
        try: subprocess.Popen(cmd.strip(), shell=True)
        except Exception: pass

def clean_for_speech(text):
    text = re.sub(r"```.*?```", " I have generated the code on your screen, sir. ", text if text else "", flags=re.DOTALL)
    text = re.sub(r"\[(AC|KAPAT|WEB|KOD_OLUSTUR|CMD):.*?\]", "", text, flags=re.IGNORECASE)
    return re.sub(r"[*#_`>]|<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

def show_code_panel(content):
    global code_panel_open, target_cx
    code_panel_open, target_cx = True, window.winfo_width() // 4
    def ui():
        if code_text_widget:
            code_text_widget.config(state=tk.NORMAL); code_text_widget.delete("1.0", tk.END); code_text_widget.insert(tk.END, content); code_text_widget.config(state=tk.DISABLED)
            code_frame.place(relx=0.5, rely=0.05, relwidth=0.45, relheight=0.75)
    window.after(0, ui)

def hide_code_panel():
    global code_panel_open, target_cx
    code_panel_open, target_cx = False, window.winfo_width() // 2
    window.after(0, lambda: code_frame.place_forget() if code_frame else None)

async def play_voice(text):
    if not jarvis_voice_active:
        await asyncio.sleep(max(2.0, len(text.split()) * 0.3))
        return
    if not text.strip(): return
    import pygame
    f = "jarvis_voice.mp3"
    try:
        await edge_tts.Communicate(text, "en-GB-RyanNeural", pitch="-15Hz").save(f)
        pygame.mixer.init(); pygame.mixer.music.load(f); pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception: pass
    finally:
        if os.path.exists(f): os.remove(f)

def speak(text): asyncio.run(play_voice(text))

def process_command(user_input):
    global uploaded_file_content
    if not user_input or not system_active: return
    update_subtitle(f"Command: {user_input}", "#ffffff")
    if any(w in user_input.lower() for w in ["close", "goodbye", "exit"]):
        update_subtitle("SYSTEM SHUTTING DOWN...", COLOR_INACTIVE); speak("Shutting down the systems, sir.")
        if window: window.after(2000, window.destroy)
        return
    hide_code_panel()
    if uploaded_file_content:
        user_input = f"{user_input}\n\n[USER UPLOADED FILE CONTENT]:\n{uploaded_file_content}"
        uploaded_file_content = ""
    messages.append({"role": "user", "content": user_input})
    if len(messages) > 6: messages[:] = [messages[0]] + messages[-5:]
    try:
        update_subtitle("... PROCESSING ...", COLOR_ACTIVE)
        resp = client.chat.completions.create(model="qwen/qwen3.8-27b", messages=messages, temperature=0.3, max_tokens=2048)
        reply = resp.choices[0].message.content or ""
        process_actions(reply)
        m = re.findall(r"```[a-zA-Z]*\n?(.*?)```", reply, re.DOTALL)
        if m: show_code_panel("\n".join(m))
        st = clean_for_speech(reply) or "Your command has been executed, sir."
        update_subtitle(st, COLOR_ACTIVE); messages.append({"role": "assistant", "content": reply})
        speak(st)
        if system_active: update_subtitle("SYSTEM ACTIVE - STANDBY", COLOR_ACTIVE)
    except Exception:
        update_subtitle("CONNECTION ERROR", COLOR_INACTIVE); speak("Connection lost, sir.")

def toggle_prompt_bar(event=None):
    global prompt_visible
    def ui():
        global prompt_visible
        if prompt_visible:
            prompt_frame.place_forget(); prompt_visible = False
            if system_active: update_subtitle("SYSTEM ACTIVE - STANDBY", COLOR_ACTIVE)
        else:
            prompt_frame.place(relx=0.5, rely=0.85, anchor="center", width=600); command_entry.focus_set(); prompt_visible = True
            if system_active: update_subtitle("WAITING FOR KEYBOARD INPUT...", "#f5d44f")
    if window: window.after(0, ui)

def handle_text_submit(event=None):
    if not system_active: return speak("System is offline, sir.")
    text = command_entry.get().strip()
    if text:
        command_entry.delete(0, tk.END); toggle_prompt_bar()
        threading.Thread(target=process_command, args=(text,), daemon=True).start()

def listen():
    if not global_mic or not system_active or not mic_active: return None
    with global_mic as source:
        update_subtitle("... LISTENING ...", COLOR_ACTIVE)
        try: audio = global_recognizer.listen(source, timeout=3, phrase_time_limit=10)
        except sr.WaitTimeoutError: return None
    try:
        if not system_active or not mic_active: return None
        update_subtitle("... PROCESSING SIGNAL ...", COLOR_ACTIVE)
        return global_recognizer.recognize_google(audio, language="en-US")
    except Exception: return None

def run_jarvis():
    speak("Systems are online, sir.")
    while True:
        if not system_active or prompt_visible or not mic_active: time.sleep(0.5); continue
        ui = listen()
        if ui: process_command(ui)

hud_arcs_1, hud_arcs_2, hud_arcs_3 = [], [], []

def init_hud():
    c = COLOR_INACTIVE
    R1, R2, R3, R4, R5 = int(240*scale), int(200*scale), int(160*scale), int(120*scale), int(80*scale)
    canvas.create_oval(cx-R1, cy-R1, cx+R1, cy+R1, outline=c, width=1, tags="hud_element")
    canvas.create_oval(cx-R3, cy-R3, cx+R3, cy+R3, outline=c, width=max(1, int(2*scale)), dash=(4, 8), tags="hud_element")
    canvas.create_oval(cx-R5, cy-R5, cx+R5, cy+R5, outline=c, width=1, tags="hud_element")
    for i in range(12): hud_arcs_1.append((canvas.create_arc(cx-R1, cy-R1, cx+R1, cy+R1, start=i*30, extent=2, outline=c, width=int(12*scale), style=tk.ARC, tags="hud_element"), i*30))
    hud_arcs_2.extend([(canvas.create_arc(cx-R2, cy-R2, cx+R2, cy+R2, start=s, extent=e, outline=c, width=int(26*scale), style=tk.ARC, tags="hud_element"), s) for s, e in [(0,65),(90,125),(240,90)]])
    hud_arcs_3.extend([(canvas.create_arc(cx-R4, cy-R4, cx+R4, cy+R4, start=s, extent=e, outline=c, width=int(14*scale), style=tk.ARC, tags="hud_element"), s) for s, e in [(0,100),(180,100)]])
    canvas.tag_lower("hud_element", "button_core")
    init_waveform(); draw_3d_buttons()

def animate_hud():
    global angle1, angle2, angle3, current_cx
    if system_active:
        angle1, angle2, angle3 = (angle1+1.8)%360, (angle2-2.8)%360, (angle3+4.0)%360
        for it, off in hud_arcs_1: canvas.itemconfig(it, start=angle1+off)
        for it, off in hud_arcs_2: canvas.itemconfig(it, start=angle2+off)
        for it, off in hud_arcs_3: canvas.itemconfig(it, start=angle3+off)
    if current_cx != target_cx:
        step = (target_cx - current_cx) // 5 or (1 if target_cx > current_cx else -1)
        if abs(step) > abs(target_cx - current_cx): step = target_cx - current_cx
        current_cx += step
        for tag in ["hud_element", "clickable", "waveform", "ui_button"]: canvas.move(tag, step, 0)
    window.after(30, animate_hud)

def toggle_system(event):
    global system_active; system_active = not system_active
    c = COLOR_ACTIVE if system_active else COLOR_INACTIVE
    canvas.itemconfig("center_text", text="J.A.R.V.I.S\nACTIVE" if system_active else "J.A.R.V.I.S\nOFFLINE", fill=c)
    canvas.itemconfig("hud_element", outline=c)
    update_subtitle("SYSTEM ACTIVE" if system_active else "SYSTEM OFFLINE", c)
    if system_active: speak("Systems are online.")

def start_gui():
    global window, canvas, subtitle_label, cx, cy, scale, code_frame, code_text_widget, prompt_frame, command_entry, target_cx, current_cx, cam_label, screen_h_global
    threading.Thread(target=init_audio, daemon=True).start(); threading.Thread(target=fetch_weather, daemon=True).start(); init_camera()
    window = tk.Tk(); window.title("J.A.R.V.I.S. HUD"); window.configure(bg=COLOR_BG); window.state('zoomed')
    window.bind("<F11>", lambda e: window.attributes("-fullscreen", not window.attributes("-fullscreen")))
    window.bind("<Escape>", lambda e: window.attributes("-fullscreen", False))
    window.bind("<Button-3>", toggle_prompt_bar)
    window.bind("<Control-o>", upload_file)
    sw, sh = window.winfo_width(), window.winfo_height()
    if sw < 100: sw, sh = window.winfo_screenwidth(), window.winfo_screenheight() - 70
    screen_h_global, cx, cy, scale = sh, sw//2, sh//2 - 40, sh / 650.0
    target_cx, current_cx = cx, cx
    canvas = tk.Canvas(window, width=sw, height=sh, bg=COLOR_BG, highlightthickness=0); canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    time_label = tk.Label(window, font=("Consolas", int(12*scale), "bold"), bg=COLOR_BG, fg="#15ff00", justify="left"); time_label.place(relx=0.02, rely=0.02)
    cam_label = tk.Label(window, text="CAMERA STANDBY", font=("Consolas", 10), bg="#111", fg=COLOR_INACTIVE, highlightthickness=1); cam_label.place(relx=0.98, rely=0.02, anchor="ne", width=240, height=160)
    update_hud_text(time_label); update_camera()
    subtitle_label = tk.Label(window, text="SYSTEM OFFLINE", font=("Consolas", int(13*scale), "bold"), bg=COLOR_BG, fg=COLOR_INACTIVE, justify="center"); subtitle_label.place(relx=0.5, rely=0.93, anchor="center")
    prompt_frame = tk.Frame(window, bg="#15ff00", highlightbackground="#15ff00", highlightthickness=2)
    command_entry = tk.Entry(prompt_frame, font=("Consolas", 13, "bold"), bg="#0b0f0b", fg="#15ff00", insertbackground="#15ff00", relief=tk.FLAT); command_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5); command_entry.bind("<Return>", handle_text_submit)
    code_frame = tk.Frame(window, bg="#0b0f0b", highlightbackground="#15ff00", highlightthickness=2)
    hf = tk.Frame(code_frame, bg="#111c11"); hf.pack(side=tk.TOP, fill=tk.X)
    tk.Label(hf, text=" STARK TERMINAL ", font=("Consolas", 10, "bold"), bg="#111c11", fg="#15ff00").pack(side=tk.LEFT, padx=10, pady=5)
    tk.Button(hf, text=" COPY ", font=("Consolas", 9, "bold"), bg="#15ff00", fg="#000", relief=tk.FLAT, command=lambda: [window.clipboard_clear(), window.clipboard_append(code_text_widget.get("1.0", tk.END)), update_subtitle("COPIED", COLOR_ACTIVE)]).pack(side=tk.RIGHT, padx=10, pady=5)
    ts = tk.Scrollbar(code_frame); ts.pack(side=tk.RIGHT, fill=tk.Y)
    code_text_widget = tk.Text(code_frame, font=("Consolas", 11), bg="#050805", fg="#15ff00", yscrollcommand=ts.set); code_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5); ts.config(command=code_text_widget.yview)
    R_btn = int(60 * scale); canvas.create_oval(cx-R_btn, cy-R_btn, cx+R_btn, cy+R_btn, fill=COLOR_BG, outline="", tags=("button_core", "clickable"))
    canvas.create_text(cx, cy, text="J.A.R.V.I.S\nOFFLINE", font=("Consolas", int(12*scale), "bold"), fill=COLOR_INACTIVE, justify="center", tags=("center_text", "clickable"))
    init_hud(); animate_waveform()
    canvas.tag_bind("clickable", "<Button-1>", toggle_system); canvas.tag_bind("ui_button", "<Button-1>", handle_canvas_click)
    for t in ["clickable", "ui_button"]: canvas.tag_bind(t, "<Enter>", lambda e: canvas.config(cursor="hand2")); canvas.tag_bind(t, "<Leave>", lambda e: canvas.config(cursor=""))
    animate_hud(); threading.Thread(target=run_jarvis, daemon=True).start()
    window.mainloop()

if __name__ == "__main__": start_gui()
