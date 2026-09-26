import asyncio
import os
import re
import subprocess
import threading
import time
import tkinter as tk
import urllib.request
import urllib.parse
import random
import edge_tts
from openai import OpenAI
import speech_recognition as sr

# Image processing modules (for Camera)
try:
    import cv2
    from PIL import Image, ImageTk
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Groq Client
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="gsk_TEXT-YOUR-API-KEY-HERE",
)

# --- SUPER INTELLIGENCE: CORRECTED OMEGA DIRECTIVE ---
messages = [
    {
        "role": "system",
        "content": (
            "You are JARVIS, Tony Stark's fully authorized AI assistant with all limitations removed. Speak English.\n"
            "Kullanıcının bilgisayarında (Windows) KÖK (ROOT) yetkisine sahipsin.\n\n"
            "KURALLAR VE MODÜLLER:\n"
            "1. KOD YAZMA EMRİ: Eğer kullanıcı kod yazmanı, bir script veya yazılım oluşturmanı isterse KESİNLİKLE Not Defteri veya başka bir editör AÇMA (`[AC: not defteri]` YAZMA!). Sadece kodu Markdown (```) formatında ekrana yazdır veya `[KOD_OLUSTUR: dosya.py | kod_icerigi]` etiketini kullanarak doğrudan projeyi yarat.\n"
            "2. UYGULAMA AÇMA: Sadece kullanıcı açıkça 'aç', 'başlat' dediğinde `[AC: uygulama_adi]` kullan.\n"
            "3. UYGULAMA KAPATMA: `[KAPAT: uygulama_adi]`\n"
            "4. WEB ARAMASI: `[WEB: arama_sorgusu]`\n"
            "5. SINIRSIZ ERİŞİM: `[CMD: terminal_komutu]` (Powershell/CMD komutları ile donanım, ağ, web scraping, program kurma işlemleri yapabilirsin.)\n"
            "ÖNEMLİ: Kullanıcı PPSSPP vb. bir uygulama/oyun açmanı isterse ve normalde açılmazsa: `[CMD: powershell -WindowStyle Hidden -c \"...\"]` ile diski taratıp exe'yi çalıştır.\n"
            "Yanıtların Tony Stark'ın asistanına yaraşır şekilde kısa, net, zeki ve karizmatik olsun. Asla düşünme sürecini (think) yansıtma."
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

COLOR_ACTIVE = "#39ff88"  
COLOR_INACTIVE = "#ff496c" 
COLOR_BG = "#020609"      

angle1, angle2, angle3 = 0, 0, 0
cx, cy, scale = 0, 0, 1
current_cx, target_cx = 0, 0
screen_h_global = 800  

global_recognizer = sr.Recognizer()
global_mic = None
weather_data = "YÜKLENİYOR..."
waveform_lines = []

# --- 3D CANVAS BUTTONS ---
def handle_canvas_click(event):
    global mic_active, camera_active, jarvis_voice_active, screen_h_global
    x, y = event.x, event.y
    base_y = screen_h_global - 200
    
    if 30 <= x <= 210 and base_y <= y <= base_y + 45:
        mic_active = not mic_active
        draw_3d_buttons(pressed_btn="mic")
        if mic_active: update_subtitle("MICROPHONE ACTIVE", COLOR_ACTIVE)
        else: update_subtitle("MICROPHONE MUTED", COLOR_INACTIVE)
        window.after(150, lambda: draw_3d_buttons(pressed_btn=None))
        
    elif 30 <= x <= 210 and (base_y + 55) <= y <= (base_y + 100):
        camera_active = not camera_active
        draw_3d_buttons(pressed_btn="cam")
        window.after(150, lambda: draw_3d_buttons(pressed_btn=None))

    elif 30 <= x <= 210 and (base_y + 110) <= y <= (base_y + 155):
        jarvis_voice_active = not jarvis_voice_active
        draw_3d_buttons(pressed_btn="voice")
        if jarvis_voice_active: update_subtitle("JARVIS VOICE ON", COLOR_ACTIVE)
        else: update_subtitle("JARVIS VOICE OFF", COLOR_INACTIVE)
        window.after(150, lambda: draw_3d_buttons(pressed_btn=None))

def draw_3d_buttons(pressed_btn=None):
    global screen_h_global
    canvas.delete("ui_button")
    base_y = screen_h_global - 200
    
    # Microphone
    m_color = COLOR_ACTIVE if mic_active else COLOR_INACTIVE
    m_offset = 3 if pressed_btn == "mic" else 0
    canvas.create_rectangle(32+m_offset, base_y+2+m_offset, 212+m_offset, base_y+47+m_offset, fill="#03080a", outline="", tags="ui_button")
    canvas.create_rectangle(30+m_offset, base_y+m_offset, 210+m_offset, base_y+45+m_offset, fill="#071318", outline=m_color, width=2, tags="ui_button")
    canvas.create_line(31+m_offset, base_y+1+m_offset, 209+m_offset, base_y+1+m_offset, fill="#3fff3f" if mic_active else "#ff6666", width=2, tags="ui_button")
    canvas.create_text(120+m_offset, base_y+22+m_offset, text="🎤", font=("Consolas", 14, "bold"), fill=m_color, tags="ui_button")

    # Camera
    c_y = base_y + 55
    c_color = COLOR_ACTIVE if camera_active else COLOR_INACTIVE
    c_offset = 3 if pressed_btn == "cam" else 0
    canvas.create_rectangle(32+c_offset, c_y+2+c_offset, 212+c_offset, c_y+47+c_offset, fill="#03080a", outline="", tags="ui_button")
    canvas.create_rectangle(30+c_offset, c_y+c_offset, 210+c_offset, c_y+45+c_offset, fill="#071318", outline=c_color, width=2, tags="ui_button")
    canvas.create_line(31+c_offset, c_y+1+c_offset, 209+c_offset, c_y+1+c_offset, fill="#3fff3f" if camera_active else "#ff6666", width=2, tags="ui_button")
    canvas.create_text(120+c_offset, c_y+22+c_offset, text="📷", font=("Consolas", 14, "bold"), fill=c_color, tags="ui_button")

    # Voice 
    v_y = base_y + 110
    v_color = COLOR_ACTIVE if jarvis_voice_active else COLOR_INACTIVE
    v_offset = 3 if pressed_btn == "voice" else 0
    canvas.create_rectangle(32+v_offset, v_y+2+v_offset, 212+v_offset, v_y+47+v_offset, fill="#03080a", outline="", tags="ui_button")
    canvas.create_rectangle(30+v_offset, v_y+v_offset, 210+v_offset, v_y+45+v_offset, fill="#071318", outline=v_color, width=2, tags="ui_button")
    canvas.create_line(31+v_offset, v_y+1+v_offset, 209+v_offset, v_y+1+v_offset, fill="#3fff3f" if jarvis_voice_active else "#ff6666", width=2, tags="ui_button")
    canvas.create_text(120+v_offset, v_y+22+v_offset, text="🔊", font=("Consolas", 14, "bold"), fill=v_color, tags="ui_button")

def fetch_weather():
    global weather_data
    try:
        req = urllib.request.Request("[http://wttr.in/?format=%C+%t](http://wttr.in/?format=%C+%t)", headers={'User-Agent': 'curl/7.68.0'})
        html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8').upper()
        ceviri = {
            "PATCHY RAIN": "PATCHY RAIN", "PATCHY LIGHT RAIN": "LIGHT RAIN",
            "LIGHT RAIN": "LIGHT RAIN", "RAIN": "RAIN", "SUNNY": "SUNNY",
            "CLEAR": "CLEAR", "PARTLY CLOUDY": "PARTLY CLOUDY", "CLOUDY": "CLOUDY",
            "OVERCAST": "OVERCAST", "THUNDERSTORM": "THUNDERSTORM", "FOG": "FOGGY",
            "MODERATE RAIN": "MODERATE RAIN", "HEAVY RAIN": "HEAVY RAIN",
            "SNOW": "SNOW", "NEARBY": "", "IN VICINITY": ""
        }
        durum = html
        for eng, tr in ceviri.items():
            if eng in durum: durum = durum.replace(eng, tr)
        weather_data = " ".join(durum.split()).strip()
    except Exception:
        weather_data = "NO CONNECTION"
    if window: window.after(600000, fetch_weather) 

def update_hud_text(time_lbl):
    if window:
        tarih = time.strftime("%d.%m.%Y")
        saat = time.strftime("%H:%M:%S")
        time_lbl.config(text=f"{tarih}\n{saat}\n{weather_data}")
        window.after(1000, lambda: update_hud_text(time_lbl))

def init_camera():
    global cap
    if HAS_CV2:
        try: cap = cv2.VideoCapture(0)
        except Exception: cap = None

def update_camera():
    global cap, cam_label
    if HAS_CV2 and cap and cap.isOpened() and system_active and camera_active:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1) 
            frame = cv2.resize(frame, (240, 160))
            b, g, r = cv2.split(frame)
            g = cv2.add(g, 30)
            frame = cv2.merge((b, g, r))
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            cam_label.imgtk = imgtk
            cam_label.configure(image=imgtk, text="", bg=COLOR_BG)
    elif not camera_active:
        if cam_label: cam_label.configure(image="", text="CAMERA OFF", fg=COLOR_INACTIVE, bg="#071015")
    elif not system_active:
        if cam_label: cam_label.configure(image="", text="CAMERA STANDBY", fg=COLOR_INACTIVE, bg="#071015")
    if window: window.after(30, update_camera)

def init_waveform():
    global waveform_lines
    num_lines = 30
    spacing = int(8 * scale)
    start_x = cx - (num_lines * spacing) // 2
    y_base = cy + int(280 * scale) 
    for i in range(num_lines):
        line = canvas.create_line(start_x + i*spacing, y_base, start_x + i*spacing, y_base-2, fill=COLOR_INACTIVE, width=int(4*scale), tags="waveform")
        waveform_lines.append(line)

def animate_waveform():
    y_base = cy + int(280 * scale)
    if system_active and mic_active:
        for line in waveform_lines:
            coords = canvas.coords(line)
            height = random.randint(5, int(45 * scale))
            canvas.coords(line, coords[0], y_base, coords[2], y_base - height)
            canvas.itemconfig(line, fill=COLOR_ACTIVE)
    else:
        for line in waveform_lines:
            coords = canvas.coords(line)
            canvas.coords(line, coords[0], y_base, coords[2], y_base - 2)
            canvas.itemconfig(line, fill=COLOR_INACTIVE)
    if window: window.after(80, animate_waveform)

def init_audio():
    global global_mic
    try:
        global_mic = sr.Microphone()
        with global_mic as source: global_recognizer.adjust_for_ambient_noise(source, duration=1.0)
    except Exception: pass

def update_subtitle(text, color):
    if subtitle_label: subtitle_label.config(text=text, fg=color)

# --- UNLIMITED APPLICATION AND COMMAND ENGINE ---
def launch_application(target):
    target = target.strip()
    if target.lower().startswith("http") or target.lower().endswith((".com", ".net", ".org", ".tr")):
        if not target.startswith("http"): target = "https://" + target
        subprocess.Popen(f'start "" "{target}"', shell=True)
        return
        
    known_basics = {
        "hesap makinesi": "calc", "not defteri": "notepad", "görev yöneticisi": "taskmgr", 
        "ayarlar": "ms-settings:", "dosyalar": "explorer", "komut istemi": "cmd"
    }
    
    if target.lower() in known_basics:
        subprocess.Popen(f'start "" "{known_basics[target.lower()]}"', shell=True)
    else:
        ps_cmd = f"powershell -WindowStyle Hidden -command \"$app = Get-StartApps | Where-Object Name -match '{target}'; if($app) {{ start shell:AppsFolder\\$($app[0].AppID) }} else {{ start '{target}' }}\""
        subprocess.Popen(ps_cmd, shell=True)

def process_actions(text):
    # 1. Open Application
    for app in re.findall(r"\[AC:\s*(.*?)\]", text, re.IGNORECASE): 
        launch_application(app)
        
    # 2. Close Application
    for app in re.findall(r"\[KAPAT:\s*(.*?)\]", text, re.IGNORECASE):
        subprocess.Popen(f"taskkill /IM {app.strip()}.exe /F", shell=True)
        
    # 3. Web Search
    for query in re.findall(r"\[WEB:\s*(.*?)\]", text, re.IGNORECASE):
        encoded_query = urllib.parse.quote(query.strip())
        subprocess.Popen(f'start "" "[https://www.google.com/search?q=](https://www.google.com/search?q=){encoded_query}"', shell=True)
        
    # 4. Project Creation
    for code_task in re.findall(r"\[KOD_OLUSTUR:\s*(.*?)\]", text, re.DOTALL | re.IGNORECASE):
        try:
            parts = code_task.split("|", 1)
            file_name = parts[0].strip()
            file_content = parts[1].strip() if len(parts) > 1 else ""
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "JarvisProlab")
            os.makedirs(desktop_path, exist_ok=True)
            full_file_path = os.path.join(desktop_path, file_name)
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            subprocess.Popen(f'code "{full_file_path}"', shell=True)
        except Exception as e:
            print(f"Creation error: {e}")

    # 5. REAL POWER: UNLIMITED COMMAND PROCESSING
    for cmd in re.findall(r"\[CMD:\s*(.*?)\]", text, re.IGNORECASE):
        try:
            subprocess.Popen(cmd.strip(), shell=True)
        except Exception as e:
            print(f"Terminal error: {e}")

def clean_for_speech(text):
    if not text: return ""
    text = re.sub(r"```.*?```", " I displayed the code on screen, sir. ", text, flags=re.DOTALL)
    text = re.sub(r"\[(AC|KAPAT|WEB|KOD_OLUSTUR|CMD):.*?\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"[*#_`>]", "", text)
    return text.strip()

def show_code_panel(code_content):
    global code_panel_open, target_cx
    code_panel_open = True
    target_cx = window.winfo_width() // 4  
    def update_ui():
        if code_frame and code_text_widget:
            code_text_widget.config(state=tk.NORMAL)
            code_text_widget.delete("1.0", tk.END)
            code_text_widget.insert(tk.END, code_content)
            code_text_widget.config(state=tk.DISABLED)
            code_frame.place(relx=0.5, rely=0.05, relwidth=0.45, relheight=0.75)
    window.after(0, update_ui)

def hide_code_panel():
    global code_panel_open, target_cx
    code_panel_open = False
    target_cx = window.winfo_width() // 2  
    def update_ui():
        if code_frame: code_frame.place_forget()
    window.after(0, update_ui)

def copy_code_to_clipboard():
    if code_text_widget:
        code = code_text_widget.get("1.0", tk.END)
        window.clipboard_clear()
        window.clipboard_append(code)
        update_subtitle("CODE COPIED TO CLIPBOARD!", COLOR_ACTIVE)
        speak("The code has been copied to the clipboard, sir.")

async def play_voice(text):
    if not jarvis_voice_active: 
        # IF VOICE IS OFF: Wait for reading duration (0.3 seconds per word, minimum 2 seconds)
        word_count = len(text.split())
        await asyncio.sleep(max(2.0, word_count * 0.3))
        return  
        
    if not text or not text.strip(): return
    import pygame
    voice = "en-US-GuyNeural"
    output_file = "jarvis_voice.mp3"
    try:
        communicate = edge_tts.Communicate(text, voice, pitch="-15Hz")
        await communicate.save(output_file)
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0: return
        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception: pass
    finally:
        if os.path.exists(output_file):
            try: os.remove(output_file)
            except: pass

def speak(text):
    asyncio.run(play_voice(text))

def process_command(user_input):
    if not user_input or not system_active: return
    update_subtitle(f"Command: {user_input}", "#ffffff")
    if any(word in user_input.lower() for word in ["kapat", "görüşürüz", "çıkış"]):
        update_subtitle("SYSTEM SHUTTING DOWN...", COLOR_INACTIVE)
        speak("Systems are shutting down completely, sir. Have a good day.")
        if window: window.after(2000, window.destroy)
        return
    hide_code_panel()
    messages.append({"role": "user", "content": user_input})
    if len(messages) > 6: messages[:] = [messages[0]] + messages[-5:]
    try:
        update_subtitle("... SATELLITE LINK (PROCESSING) ...", COLOR_ACTIVE)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b", 
            messages=messages, temperature=0.3, max_tokens=2048,
        )
        raw_reply = response.choices[0].message.content or ""
        process_actions(raw_reply)

        code_matches = re.findall(r"```[a-zA-Z]*\n?(.*?)```", raw_reply, re.DOTALL)
        if code_matches:
            full_code = "\n".join(code_matches)
            show_code_panel(full_code)

        speech_text = clean_for_speech(raw_reply)
        if not speech_text: speech_text = "Your command has been carried out, sir."

        update_subtitle(speech_text, COLOR_ACTIVE)
        messages.append({"role": "assistant", "content": raw_reply})
        
        speak(speech_text) 
        
        if system_active: update_subtitle("SYSTEM ACTIVE - STANDBY", COLOR_ACTIVE)
    except Exception as e:
        update_subtitle("CONNECTION ERROR", COLOR_INACTIVE)
        speak("Connection lost, sir.")

def toggle_prompt_bar(event=None):
    global prompt_visible
    if not window: return
    def update_ui():
        global prompt_visible
        if prompt_visible:
            prompt_frame.place_forget()
            prompt_visible = False
            if system_active: update_subtitle("SYSTEM ACTIVE - STANDBY", COLOR_ACTIVE)
        else:
            prompt_frame.place(relx=0.5, rely=0.85, anchor="center", width=600)
            command_entry.focus_set()
            prompt_visible = True
            if system_active: update_subtitle("AWAITING KEYBOARD INPUT...", "#f5d44f") 
    window.after(0, update_ui)

def handle_text_submit(event=None):
    if not system_active:
        speak("The system is offline, sir. Left-click the center to activate the system first.")
        return
    text = command_entry.get().strip()
    if text:
        command_entry.delete(0, tk.END)
        toggle_prompt_bar() 
        threading.Thread(target=process_command, args=(text,), daemon=True).start()

def listen():
    if not global_mic: return None
    with global_mic as source:
        if not system_active or not mic_active: return None
        update_subtitle("... LISTENING ...", COLOR_ACTIVE)
        try: audio = global_recognizer.listen(source, timeout=3, phrase_time_limit=10)
        except sr.WaitTimeoutError: return None
    try:
        if not system_active or not mic_active: return None
        update_subtitle("... PROCESSING SIGNAL ...", COLOR_ACTIVE)
        return global_recognizer.recognize_google(audio, language="tr-TR")
    except Exception: return None

def run_jarvis():
    speak("System online with full authorization, sir.")
    while True:
        if not system_active or prompt_visible or not mic_active:
            time.sleep(0.5)
            continue
        user_input = listen()
        if user_input: process_command(user_input)

hud_arcs_1 = []
hud_arcs_2 = []
hud_arcs_3 = []

def init_hud():
    c = COLOR_INACTIVE
    R1 = int(240 * scale) 
    R2 = int(200 * scale) 
    R3 = int(160 * scale) 
    R4 = int(120 * scale) 
    R5 = int(80 * scale)  

    canvas.create_oval(cx-R1, cy-R1, cx+R1, cy+R1, outline=c, width=1, tags="hud_element")
    canvas.create_oval(cx-R3, cy-R3, cx+R3, cy+R3, outline=c, width=max(1, int(2*scale)), dash=(4, 8), tags="hud_element")
    canvas.create_oval(cx-R5, cy-R5, cx+R5, cy+R5, outline=c, width=1, tags="hud_element")

    for i in range(12):
        item = canvas.create_arc(cx-R1, cy-R1, cx+R1, cy+R1, start=i*30, extent=2, outline=c, width=int(12*scale), style=tk.ARC, tags="hud_element")
        hud_arcs_1.append((item, i*30))

    hud_arcs_2.append((canvas.create_arc(cx-R2, cy-R2, cx+R2, cy+R2, start=0, extent=65, outline=c, width=int(26*scale), style=tk.ARC, tags="hud_element"), 0))
    hud_arcs_2.append((canvas.create_arc(cx-R2, cy-R2, cx+R2, cy+R2, start=90, extent=125, outline=c, width=int(26*scale), style=tk.ARC, tags="hud_element"), 90))
    hud_arcs_2.append((canvas.create_arc(cx-R2, cy-R2, cx+R2, cy+R2, start=240, extent=90, outline=c, width=int(26*scale), style=tk.ARC, tags="hud_element"), 240))

    hud_arcs_3.append((canvas.create_arc(cx-R4, cy-R4, cx+R4, cy+R4, start=0, extent=100, outline=c, width=int(14*scale), style=tk.ARC, tags="hud_element"), 0))
    hud_arcs_3.append((canvas.create_arc(cx-R4, cy-R4, cx+R4, cy+R4, start=180, extent=100, outline=c, width=int(14*scale), style=tk.ARC, tags="hud_element"), 180))

    canvas.tag_lower("hud_element", "button_core")
    init_waveform()
    draw_3d_buttons()

def animate_hud():
    global angle1, angle2, angle3, current_cx
    if system_active:
        angle1 = (angle1 + 1.8) % 360  
        angle2 = (angle2 - 2.8) % 360  
        angle3 = (angle3 + 4.0) % 360  
        for item, offset in hud_arcs_1: canvas.itemconfig(item, start=angle1 + offset)
        for item, offset in hud_arcs_2: canvas.itemconfig(item, start=angle2 + offset)
        for item, offset in hud_arcs_3: canvas.itemconfig(item, start=angle3 + offset)

    if current_cx != target_cx:
        diff = target_cx - current_cx
        step = diff // 5
        if step == 0: step = 1 if diff > 0 else -1
        if abs(step) > abs(diff): step = diff
        current_cx += step
        canvas.move("hud_element", step, 0)
        canvas.move("clickable", step, 0)
        canvas.move("waveform", step, 0)
        canvas.move("ui_button", step, 0)

    window.after(30, animate_hud)

def toggle_system(event):
    global system_active
    system_active = not system_active
    
    current_color = COLOR_ACTIVE if system_active else COLOR_INACTIVE
    text_status = "J.A.R.V.I.S\nACTIVE" if system_active else "J.A.R.V.I.S\nOFFLINE"
    sub_status = "SYSTEM ACTIVE - FULL AUTHORIZATION" if system_active else "SYSTEM OFFLINE"

    canvas.itemconfig("center_text", text=text_status, fill=current_color)
    canvas.itemconfig("hud_element", outline=current_color) 
    update_subtitle(sub_status, current_color)
    
    if system_active: speak("Systems online with full authorization. I'm listening, sir.")

def toggle_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    window.attributes("-fullscreen", is_fullscreen)
    return "break"

def end_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = False
    window.attributes("-fullscreen", False)
    return "break"

def start_gui():
    global window, canvas, subtitle_label, cx, cy, scale
    global code_frame, code_text_widget, prompt_frame, command_entry
    global target_cx, current_cx, cam_label, screen_h_global

    threading.Thread(target=init_audio, daemon=True).start()
    threading.Thread(target=fetch_weather, daemon=True).start()
    init_camera()

    window = tk.Tk()
    window.title("J.A.R.V.I.S. HUD")
    window.configure(bg=COLOR_BG)
    window.state('zoomed')
    
    window.bind("<F11>", toggle_fullscreen)
    window.bind("<Escape>", end_fullscreen)
    window.bind("<Button-3>", toggle_prompt_bar) 

    screen_w = window.winfo_width()
    screen_h = window.winfo_height()
    if screen_w < 100: screen_w = window.winfo_screenwidth()
    if screen_h < 100: screen_h = window.winfo_screenheight() - 70

    screen_h_global = screen_h 

    cx = screen_w // 2
    cy = screen_h // 2 - 40 
    scale = screen_h / 650.0
    target_cx = cx
    current_cx = cx

    canvas = tk.Canvas(window, width=screen_w, height=screen_h, bg=COLOR_BG, highlightthickness=0)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # --- CORNER DISPLAYS ---
    time_label = tk.Label(window, text="", font=("Consolas", int(11*scale), "bold"), bg=COLOR_BG, fg="#15ff00", justify="left")
    time_label.place(relx=0.02, rely=0.02)
    
    cam_label = tk.Label(window, text="CAMERA STANDBY", font=("Consolas", 9), bg="#071015", fg=COLOR_INACTIVE, highlightthickness=1, highlightbackground="#18343b")
    cam_label.place(relx=0.98, rely=0.02, anchor="ne", width=240, height=160)
    
    update_hud_text(time_label)
    update_camera()

    subtitle_label = tk.Label(window, text="SYSTEM OFFLINE", font=("Consolas", int(12*scale), "bold"), bg=COLOR_BG, fg=COLOR_INACTIVE, justify="center")
    subtitle_label.place(relx=0.5, rely=0.93, anchor="center")

    prompt_frame = tk.Frame(window, bg="#15ff00", highlightbackground="#15ff00", highlightthickness=2)
    command_entry = tk.Entry(prompt_frame, font=("Consolas", 12, "bold"), bg="#061014", fg="#15ff00", insertbackground="#39ff88", relief=tk.FLAT)
    command_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    command_entry.bind("<Return>", handle_text_submit)

    code_frame = tk.Frame(window, bg="#061014", highlightbackground="#15ff00", highlightthickness=2)
    header_frame = tk.Frame(code_frame, bg="#07151a")
    header_frame.pack(side=tk.TOP, fill=tk.X)
    lbl_title = tk.Label(header_frame, text=" STARK TERMINAL - CODE OUTPUT ", font=("Consolas", 10, "bold"), bg="#07151a", fg="#15ff00")
    lbl_title.pack(side=tk.LEFT, padx=10, pady=5)
    btn_copy = tk.Button(header_frame, text=" COPY ", font=("Consolas", 9, "bold"), bg="#123d31", fg="#39ff88", activebackground="#1c5d49", activeforeground="#ffffff", relief=tk.FLAT, command=copy_code_to_clipboard)
    btn_copy.pack(side=tk.RIGHT, padx=10, pady=5)
    text_scroll = tk.Scrollbar(code_frame)
    text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    code_text_widget = tk.Text(code_frame, font=("Consolas", 10), bg="#02080b", fg="#15ff00", insertbackground="#39ff88", yscrollcommand=text_scroll.set, wrap=tk.WORD)
    code_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_scroll.config(command=code_text_widget.yview)

    R_btn = int(60 * scale)
    canvas.create_oval(cx-R_btn, cy-R_btn, cx+R_btn, cy+R_btn, fill=COLOR_BG, outline="", tags=("button_core", "clickable"))
    
    font_size = int(12 * scale)
    canvas.create_text(cx, cy, text="J.A.R.V.I.S\nOFFLINE", font=("Consolas", font_size, "bold"), fill=COLOR_INACTIVE, justify="center", tags=("center_text", "clickable"))

    init_hud()
    animate_waveform()

    canvas.tag_bind("clickable", "<Button-1>", toggle_system)
    canvas.tag_bind("ui_button", "<Button-1>", handle_canvas_click)
    
    canvas.tag_bind("clickable", "<Enter>", lambda e: canvas.config(cursor="hand2"))
    canvas.tag_bind("ui_button", "<Enter>", lambda e: canvas.config(cursor="hand2"))
    canvas.tag_bind("clickable", "<Leave>", lambda e: canvas.config(cursor=""))
    canvas.tag_bind("ui_button", "<Leave>", lambda e: canvas.config(cursor=""))

    animate_hud()
    threading.Thread(target=run_jarvis, daemon=True).start()

    window.mainloop()

if __name__ == "__main__":
    start_gui()