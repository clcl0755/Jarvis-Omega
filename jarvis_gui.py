import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import time
import json
from datetime import datetime

# System Monitor için psutil kontrolü
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class JarvisGUI:
    def __init__(self, root, standalone=True, theme_callback=None):
        self.root = root
        self.standalone = standalone
        self.theme_callback = theme_callback
        if self.standalone:
            self.root.title("JARVIS - Control Center")
            self.root.geometry("950x650")

        self._closing = False
        self.active_tab = None  # Tracks the active module
        self.settings = self.load_settings()
        self.system_logs = []

        # --- COLOR PALETTES (THEMES) ---
        self.themes = {
            "normal": {
                "name": "🩵 Standard JARVIS Mode",
                "bg": "#0b0f19",
                "top_bg": "#111827",
                "menu_bg": "#1f2937",
                "accent": "#00f0ff",
                "text": "#ffffff",
                "card_bg": "#161b22",
                "subtext": "#8b949e"
            },
            "combat": {
                "name": "🚨 Combat Mode (Red Alert)",
                "bg": "#100404",
                "top_bg": "#220808",
                "menu_bg": "#330c0c",
                "accent": "#ff2a2a",
                "text": "#ffffff",
                "card_bg": "#220808",
                "subtext": "#ff8888"
            },
            "stealth": {
                "name": "🥷 Stealth Mode",
                "bg": "#080808",
                "top_bg": "#121212",
                "menu_bg": "#1c1c1c",
                "accent": "#888888",
                "text": "#e0e0e0",
                "card_bg": "#121212",
                "subtext": "#666666"
            },
            "hacker": {
                "name": "🟢 Hacker / Matrix Mode",
                "bg": "#020b04",
                "top_bg": "#051a0a",
                "menu_bg": "#0a2b11",
                "accent": "#00ff41",
                "text": "#00ff41",
                "card_bg": "#051a0a",
                "subtext": "#00aa2b"
            }
        }
        self.current_theme = "normal"

        # --- 1. TOP BAR (TOP BAR) ---
        self.top_bar = tk.Frame(self.root, height=50)
        self.top_bar.pack(side="top", fill="x")

        # THREE-LINE MENU ICON
        self.menu_btn = tk.Label(
            self.top_bar, 
            text=" ☰ ", 
            font=("Consolas", 18, "bold"), 
            cursor="hand2"
        )
        self.menu_btn.pack(side="left", padx=15, pady=10)

        self.title_label = tk.Label(
            self.top_bar, 
            text="JARVIS AI SYSTEM", 
            font=("Consolas", 14, "bold")
        )
        self.title_label.pack(side="left", padx=10)

        # RETURN TO HUD FROM ACTIVE MODULE
        # Visible when a module is open; hidden on the welcome screen.
        self.back_btn = tk.Button(
            self.top_bar,
            text="◀ HUD",
            font=("Consolas", 9, "bold"),
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.show_welcome_screen
        )
        self.back_btn.pack(side="right", padx=15, pady=8)
        self.back_btn.pack_forget()

        # --- 2. HOVER MENU FRAME ---
        self.menu_frame = tk.Frame(self.root, bd=1, relief="solid", highlightthickness=1)

        self.menu_items = [
            ("🖥️ Terminal / Console", self.on_terminal_click),
            ("📊 System Monitor", self.on_monitor_click),
            ("📁 Project & File Storage", self.on_files_click),
            ("🎨 Theme & Mode Selection", self.on_theme_click),
            ("⚙️ Settings & API", self.on_settings_click),
            ("📜 Command & Log History", self.on_logs_click),
        ]
        

        self.menu_buttons = []
        for text, command in self.menu_items:
            btn = tk.Button(
                self.menu_frame, 
                text=text, 
                font=("Segoe UI", 10), 
                bd=0, 
                anchor="w", 
                padx=15, 
                pady=8,
                command=command
            )
            btn.pack(fill="x")
            self.menu_buttons.append(btn)

        self.menu_btn.bind("<Enter>", self.show_menu)
        self.menu_frame.bind("<Enter>", self.keep_menu)
        self.menu_btn.bind("<Leave>", self.schedule_hide_menu)
        self.menu_frame.bind("<Leave>", self.schedule_hide_menu)

        self.hide_timer = None

        # --- 3. MAIN CONTENT AREA ---
        self.main_content = tk.Frame(self.root)
        self.main_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Apply the initial theme and show the welcome screen
        self.apply_theme("normal")
        self.show_welcome_screen()

    # --- SETTINGS / LOG HELPERS ---
    def load_settings(self):
        defaults = {
            "openai_key": "",
            "gemini_key": "",
            "nvidia_key": "",
            "default_model": "Gemini 1.5 Pro",
            "language": "EN"
        }
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    defaults.update(data)
        except Exception:
            pass
        return defaults

    def save_settings(self):
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            self.add_log("INFO", "Settings saved to config.json.")
        except Exception as e:
            messagebox.showerror("ERROR", f"Failed to save settings: {e}")

    def add_log(self, level, msg):
        entry = {"level": str(level), "msg": str(msg), "time": datetime.now().strftime("%H:%M:%S")}
        self.system_logs.append(entry)
        if len(self.system_logs) > 500:
            self.system_logs = self.system_logs[-500:]
        try:
            if hasattr(self, "log_console") and self.log_console.winfo_exists():
                self.filter_logs_display()
        except Exception:
            pass

    # --- THEME APPLICATION ENGINE ---
    def apply_theme(self, theme_key):
        if theme_key not in self.themes:
            return
        
        self.current_theme = theme_key
        t = self.themes[theme_key]

        # Main Window & Top Bar
        self.root.configure(bg=t["bg"])
        self.top_bar.configure(bg=t["top_bg"])
        self.menu_btn.configure(bg=t["top_bg"], fg=t["accent"])
        self.title_label.configure(bg=t["top_bg"], fg=t["text"])
        self.back_btn.configure(
            bg=t["accent"],
            fg="#000000",
            activebackground=t["text"],
            activeforeground="#000000"
        )

        # Menu Frame & Buttons
        self.menu_frame.configure(bg=t["menu_bg"])
        self.menu_frame.lift()
        for btn in self.menu_buttons:
            btn.configure(
                bg=t["menu_bg"], 
                fg=t["text"], 
                activebackground=t["accent"], 
                activeforeground="#000000"
            )
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=t["card_bg"], fg=t["accent"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=t["menu_bg"], fg=t["text"]))

        # Main content area
        self.main_content.configure(bg=t["bg"])

    # --- MENU CONTROL FUNCTIONS ---
    def show_menu(self, event=None):
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
            self.hide_timer = None
        # Menü, main_content sonradan oluşturulduğu için stacking sırasını
        # açıkça öne alıyoruz. Böylece içerik panelinin arkasında kalmaz.
        self.menu_frame.place(x=10, y=45, width=230)
        self.menu_frame.lift()
        self.root.after_idle(self.menu_frame.lift)

    def keep_menu(self, event=None):
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
            self.hide_timer = None
        if self.menu_frame.winfo_ismapped():
            self.menu_frame.lift()

    def schedule_hide_menu(self, event=None):
        self.hide_timer = self.root.after(200, self.hide_menu)

    def hide_menu(self):
        self.menu_frame.place_forget()

    def update_back_button(self):
        """Shows the return-to-HUD button when a module is active."""
        try:
            if self.active_tab:
                self.back_btn.pack(side="right", padx=15, pady=8)
            else:
                self.back_btn.pack_forget()
        except Exception:
            pass

    def clear_main_content(self):
        self.active_tab = None
        for widget in self.main_content.winfo_children():
            widget.destroy()
        # Çağıran modül active_tab değerini ayarladıktan sonra buton güncellensin.
        self.root.after_idle(self.update_back_button)

    def show_welcome_screen(self):
        self.clear_main_content()
        t = self.themes[self.current_theme]
        dash = tk.Frame(self.main_content, bg=t["bg"])
        dash.pack(fill="both", expand=True)

        hero = tk.Frame(dash, bg=t["card_bg"], bd=1, relief="solid")
        hero.pack(fill="x", padx=10, pady=(10, 8))
        tk.Label(hero, text="J.A.R.V.I.S CORE", font=("Consolas", 18, "bold"),
                 bg=t["card_bg"], fg=t["accent"]).pack(anchor="w", padx=20, pady=(16, 2))
        tk.Label(hero, text="Unified Control Interface • HUD + Core + Modules",
                 font=("Consolas", 10), bg=t["card_bg"], fg=t["subtext"]).pack(anchor="w", padx=20, pady=(0, 16))

        cards = tk.Frame(dash, bg=t["bg"])
        cards.pack(fill="both", expand=True, padx=10, pady=5)
        modules = [
            ("TERMINAL", "Command Center", self.on_terminal_click),
            ("SYSTEM", "CPU / RAM / Disk", self.on_monitor_click),
            ("FILES", "Projects & code", self.on_files_click),
            ("THEME", "HUD / interface mode", self.on_theme_click),
            ("SETTINGS", "API & system settings", self.on_settings_click),
            ("LOGS", "Event history", self.on_logs_click),
        ]
        for i, (name, desc, cmd) in enumerate(modules):
            card = tk.Frame(cards, bg=t["card_bg"], bd=1, relief="solid")
            card.grid(row=i//2, column=i%2, sticky="nsew", padx=6, pady=6)
            cards.grid_rowconfigure(i//2, weight=1)
            cards.grid_columnconfigure(i%2, weight=1)
            tk.Label(card, text=name, font=("Consolas", 12, "bold"), bg=t["card_bg"], fg=t["accent"]).pack(anchor="w", padx=14, pady=(14, 2))
            tk.Label(card, text=desc, font=("Segoe UI", 9), bg=t["card_bg"], fg=t["subtext"]).pack(anchor="w", padx=14, pady=(0, 10))
            tk.Button(card, text="OPEN", command=cmd, font=("Consolas", 9, "bold"),
                      bg=t["accent"], fg="#000000", bd=0, padx=14, pady=5, cursor="hand2").pack(anchor="e", padx=14, pady=(0, 14))

    # ==========================================
    # MODÜL 1: GELİŞMİŞ İNTERAKTİF TERMINAL & KONSOL
    # ==========================================
    def on_terminal_click(self):
        """🖥️ Advanced Interactive Terminal Module"""
        self.hide_menu()
        self.clear_main_content()
        self.active_tab = "terminal"
        t = self.themes[self.current_theme]

        # Ana Konteyner
        term_frame = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        term_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Header Bar
        header = tk.Frame(term_frame, bg=t["top_bg"], height=35)
        header.pack(fill="x")
        
        tk.Label(
            header, 
            text="🖥️ JARVIS INTERACTIVE TERMINAL & COMMAND CENTER", 
            font=("Consolas", 11, "bold"), 
            bg=t["top_bg"], 
            fg=t["accent"]
        ).pack(side="left", padx=10, pady=5)

        # Clear and Export Buttons
        tk.Button(
            header,
            text="💾 Save Output",
            font=("Segoe UI", 8, "bold"),
            bg=t["card_bg"],
            fg=t["text"],
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.export_terminal_output
        ).pack(side="right", padx=5, pady=5)

        tk.Button(
            header,
            text="📋 Copy",
            font=("Segoe UI", 8, "bold"),
            bg=t["card_bg"],
            fg=t["text"],
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.copy_terminal_output
        ).pack(side="right", padx=5, pady=5)

        tk.Button(
            header,
            text="🗑️ Clear (CLS)",
            font=("Segoe UI", 8, "bold"),
            bg=t["card_bg"],
            fg=t["text"],
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.clear_terminal_screen
        ).pack(side="right", padx=5, pady=5)

        # Shortcut / Quick Command Bar (Quick Commands)
        quick_bar = tk.Frame(term_frame, bg=t["top_bg"])
        quick_bar.pack(fill="x", padx=2, pady=(0, 2))

        tk.Label(
            quick_bar, 
            text=" Quick Commands: ", 
            font=("Consolas", 8, "bold"), 
            bg=t["top_bg"], 
            fg=t["subtext"]
        ).pack(side="left")

        quick_cmds = [
            ("🌐 IP Config", "ipconfig"),
            ("📡 Ping Google", "ping google.com -n 4"),
            ("📁 Directory Listing", "dir"),
            ("💻 System Information", "systeminfo"),
            ("⚙️ Active Processes", "tasklist")
        ]

        for label_text, cmd_text in quick_cmds:
            tk.Button(
                quick_bar,
                text=label_text,
                font=("Consolas", 8),
                bg=t["card_bg"],
                fg=t["accent"],
                bd=0,
                padx=6,
                pady=2,
                cursor="hand2",
                command=lambda c=cmd_text: self.run_quick_command(c)
            ).pack(side="left", padx=2, pady=2)

        # Console Output Area (Text + Scrollbar)
        output_frame = tk.Frame(term_frame, bg="#0d1117")
        output_frame.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")

        self.term_output = tk.Text(
            output_frame, 
            bg="#0d1117", 
            fg="#39d353", 
            insertbackground="#ffffff",
            font=("Consolas", 10), 
            bd=0, 
            yscrollcommand=scrollbar.set, 
            wrap="word"
        )
        self.term_output.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.term_output.yview)

        # Tag Renk Tanımlamaları
        self.term_output.tag_config("prompt", foreground=t["accent"], font=("Consolas", 10, "bold"))
        self.term_output.tag_config("cmd", foreground="#ffffff", font=("Consolas", 10, "bold"))
        self.term_output.tag_config("stdout", foreground="#39d353")
        self.term_output.tag_config("stderr", foreground="#ff5555")
        self.term_output.tag_config("system", foreground="#8b949e", font=("Consolas", 9, "italic"))

        # Geçmiş Değişkeni
        if not hasattr(self, 'terminal_history'):
            self.terminal_history = []
        self.history_index = len(self.terminal_history)

        self.term_output.insert("end", "=== JARVIS INTERACTIVE SYSTEM TERMINAL [v2.0] ===\n", "system")
        self.term_output.insert("end", "Enter a command to run a system command or use the quick buttons.\n\n", "system")
        self.term_output.config(state="disabled")

        # Giriş Satırı (Prompt & Entry)
        input_frame = tk.Frame(term_frame, bg=t["top_bg"])
        input_frame.pack(fill="x", side="bottom")

        self.prompt_label = tk.Label(
            input_frame, 
            text=f" {os.getcwd()}> ", 
            font=("Consolas", 9, "bold"), 
            bg=t["top_bg"], 
            fg=t["accent"]
        )
        self.prompt_label.pack(side="left")

        self.cmd_entry = tk.Entry(
            input_frame, 
            bg="#0d1117", 
            fg="#ffffff", 
            insertbackground="#ffffff", 
            font=("Consolas", 10), 
            bd=1, 
            relief="flat"
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=5, pady=6)
        self.cmd_entry.focus_set()

        # Klavye Kısayolları (Enter = Run, Yukarı/Aşağı = Geçmiş)
        self.cmd_entry.bind("<Return>", self.execute_terminal_command)
        self.cmd_entry.bind("<Up>", self.navigate_history_up)
        self.cmd_entry.bind("<Down>", self.navigate_history_down)

    def execute_terminal_command(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return

        self.cmd_entry.delete(0, "end")

        # Geçmişe Ekle
        if not hasattr(self, 'terminal_history'):
            self.terminal_history = []
        self.terminal_history.append(cmd)
        self.history_index = len(self.terminal_history)

        # Özel Dahili Commandlar (cls, clear, cd)
        if cmd.lower() in ["cls", "clear"]:
            self.clear_terminal_screen()
            return

        if cmd.lower().startswith("cd "):
            target_dir = cmd[3:].strip()
            try:
                os.chdir(target_dir)
                self.prompt_label.config(text=f" {os.getcwd()}> ")
                self.append_terminal_output(f"Directory changed: {os.getcwd()}\n", "system")
            except Exception as e:
                self.append_terminal_output(f"Error: {str(e)}\n", "stderr")
            return

        # Ekran Çıktısı
        self.term_output.config(state="normal")
        self.term_output.insert("end", f"\n{os.getcwd()}> ", "prompt")
        self.term_output.insert("end", f"{cmd}\n", "cmd")
        self.term_output.config(state="disabled")
        self.term_output.see("end")

        self.add_log("CMD", f"Terminal: {cmd}")

        # Thread ile Arka Planda Runma
        threading.Thread(target=self._run_subprocess_thread, args=(cmd,), daemon=True).start()

    def _run_subprocess_thread(self, cmd):
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            stdout, stderr = process.communicate()

            if stdout:
                self.root.after(0, self.append_terminal_output, stdout, "stdout")
            if stderr:
                self.root.after(0, self.append_terminal_output, stderr, "stderr")

        except Exception as e:
            self.root.after(0, self.append_terminal_output, f"System Error: {str(e)}\n", "stderr")

    def run_quick_command(self, cmd):
        if hasattr(self, 'cmd_entry') and self.cmd_entry.winfo_exists():
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, cmd)
            self.execute_terminal_command()

    def append_terminal_output(self, text, tag="stdout"):
        if self.active_tab == "terminal" and hasattr(self, 'term_output') and self.term_output.winfo_exists():
            self.term_output.config(state="normal")
            self.term_output.insert("end", text, tag)
            self.term_output.config(state="disabled")
            self.term_output.see("end")

    def copy_terminal_output(self):
        if hasattr(self, 'term_output') and self.term_output.winfo_exists():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.term_output.get("1.0", "end-1c"))
                self.add_log("INFO", "Terminal output copied to clipboard.")
            except Exception as e:
                self.add_log("ERROR", f"Could not copy to clipboard: {e}")

    def clear_terminal_screen(self):
        if hasattr(self, 'term_output') and self.term_output.winfo_exists():
            self.term_output.config(state="normal")
            self.term_output.delete("1.0", "end")
            self.term_output.insert("end", "=== Screen Cleared ===\n\n", "system")
            self.term_output.config(state="disabled")

    def export_terminal_output(self):
        if hasattr(self, 'term_output') and self.term_output.winfo_exists():
            content = self.term_output.get("1.0", "end-1c")
            filename = f"terminal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Terminal output saved:\n{filename}")
                self.add_log("INFO", f"Terminal output '{filename}' was exported.")
            except Exception as e:
                messagebox.showerror("ERROR", f"Could not save file: {e}")

    def navigate_history_up(self, event=None):
        if hasattr(self, 'terminal_history') and self.terminal_history:
            if self.history_index > 0:
                self.history_index -= 1
                self.cmd_entry.delete(0, "end")
                self.cmd_entry.insert(0, self.terminal_history[self.history_index])
        return "break"

    def navigate_history_down(self, event=None):
        if hasattr(self, 'terminal_history') and self.terminal_history:
            if self.history_index < len(self.terminal_history) - 1:
                self.history_index += 1
                self.cmd_entry.delete(0, "end")
                self.cmd_entry.insert(0, self.terminal_history[self.history_index])
            else:
                self.history_index = len(self.terminal_history)
                self.cmd_entry.delete(0, "end")
        return "break"

    # ==========================================
    # --- MODÜL 2: SİSTEM MONİTÖRÜ ---
    # ==========================================
    def on_monitor_click(self):
        self.hide_menu()
        self.open_monitor_view()

    def open_monitor_view(self):
        self.clear_main_content()
        self.active_tab = "monitor"
        t = self.themes[self.current_theme]

        if not HAS_PSUTIL:
            err_lbl = tk.Label(
                self.main_content,
                text="⚠️ The 'psutil' library is required to read live system data.\n\nYou can install it with 'pip install psutil' in the terminal.",
                font=("Consolas", 11),
                bg=t["bg"],
                fg="#ff7b72",
                justify="center"
            )
            err_lbl.pack(expand=True)
            return

        mon_frame = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        mon_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Label(
            mon_frame,
            text="📊 LIVE SYSTEM PERFORMANCE METRICS",
            font=("Consolas", 12, "bold"),
            bg=t["top_bg"],
            fg=t["accent"],
            pady=8
        )
        header.pack(fill="x")

        container = tk.Frame(mon_frame, bg=t["card_bg"])
        container.pack(fill="both", expand=True, padx=20, pady=15)

        self.cpu_val_lbl = tk.Label(container, text="CPU Usage: 0%", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"])
        self.cpu_val_lbl.pack(anchor="w", pady=(10, 2))
        self.cpu_canvas = tk.Canvas(container, height=22, bg=t["top_bg"], highlightthickness=0)
        self.cpu_canvas.pack(fill="x")

        self.ram_val_lbl = tk.Label(container, text="RAM Usage: 0 GB / 0 GB (0%)", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"])
        self.ram_val_lbl.pack(anchor="w", pady=(15, 2))
        self.ram_canvas = tk.Canvas(container, height=22, bg=t["top_bg"], highlightthickness=0)
        self.ram_canvas.pack(fill="x")

        self.disk_val_lbl = tk.Label(container, text="Disk (C:) Usage: 0 GB / 0 GB (0%)", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"])
        self.disk_val_lbl.pack(anchor="w", pady=(15, 2))
        self.disk_canvas = tk.Canvas(container, height=22, bg=t["top_bg"], highlightthickness=0)
        self.disk_canvas.pack(fill="x")

        info_frame = tk.Frame(container, bg=t["top_bg"], bd=1, relief="solid")
        info_frame.pack(fill="x", pady=25)

        self.info_lbl = tk.Label(
            info_frame,
            text="Loading system information...",
            font=("Consolas", 9),
            bg=t["top_bg"],
            fg=t["subtext"],
            justify="left",
            padx=15,
            pady=10
        )
        self.info_lbl.pack(side="left")

        self.update_system_metrics()

    def draw_progress_bar(self, canvas, percent, color="#00f0ff"):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10:
            w = 500

        fill_width = (percent / 100.0) * w
        bar_color = "#ff7b72" if percent > 85 else color

        canvas.create_rectangle(0, 0, fill_width, h, fill=bar_color, outline="")
        canvas.create_rectangle(fill_width, 0, w, h, fill="#21262d", outline="")

    def update_system_metrics(self):
        if self.active_tab != "monitor":
            return

        t = self.themes[self.current_theme]
        cpu_p = psutil.cpu_percent(interval=None)
        self.cpu_val_lbl.config(text=f"CPU Usage: %{cpu_p:.1f}")
        self.draw_progress_bar(self.cpu_canvas, cpu_p, t["accent"])

        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        self.ram_val_lbl.config(text=f"RAM Usage: {ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB (%{ram.percent:.1f})")
        self.draw_progress_bar(self.ram_canvas, ram.percent, "#39d353")

        try:
            disk = psutil.disk_usage("C:\\")
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            self.disk_val_lbl.config(text=f"Disk (C:) Usage: {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB (%{disk.percent:.1f})")
            self.draw_progress_bar(self.disk_canvas, disk.percent, "#d29922")
        except Exception:
            pass

        cores = psutil.cpu_count(logical=True)
        boot_time = time.strftime("%H:%M:%S", time.localtime(psutil.boot_time()))
        proc_count = len(psutil.pids())

        self.info_lbl.config(
            text=f"• Logical CPU Cores: {cores}\n"
                 f"• Active Processes: {proc_count}\n"
                 f"• System Boot Time: {boot_time}"
        )

        self.root.after(1000, self.update_system_metrics)

    # ==========================================
    # --- MODÜL 3: PROJE & DOSYA DEPOSU ---
    # ==========================================
    def on_files_click(self):
        self.hide_menu()
        self.open_files_view()

    def open_files_view(self):
        self.clear_main_content()
        self.active_tab = "files"
        t = self.themes[self.current_theme]

        files_frame = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        files_frame.pack(fill="both", expand=True)

        header = tk.Frame(files_frame, bg=t["top_bg"], height=35)
        header.pack(fill="x")

        title = tk.Label(
            header, 
            text=" 📂 JARVIS FILES", 
            font=("Consolas", 10, "bold"), 
            bg=t["top_bg"], 
            fg=t["accent"]
        )
        title.pack(side="left", pady=5)

        refresh_btn = tk.Button(
            header,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg=t["menu_bg"],
            fg=t["text"],
            bd=0,
            padx=10,
            cursor="hand2",
            command=self.load_project_files
        )
        refresh_btn.pack(side="right", padx=5, pady=4)

        paned = tk.PanedWindow(files_frame, orient="horizontal", bg=t["card_bg"], bd=0, sashwidth=4)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        left_frame = tk.Frame(paned, bg=t["top_bg"], width=250)
        paned.add(left_frame)

        lbl_list = tk.Label(left_frame, text="Project Files", font=("Consolas", 9, "bold"), bg=t["top_bg"], fg=t["subtext"])
        lbl_list.pack(anchor="w", padx=10, pady=5)

        self.file_listbox = tk.Listbox(
            left_frame,
            bg=t["card_bg"],
            fg=t["text"],
            selectbackground=t["accent"],
            selectforeground="#000000",
            font=("Consolas", 9),
            bd=0,
            highlightthickness=0
        )
        self.file_listbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)

        right_frame = tk.Frame(paned, bg=t["card_bg"])
        paned.add(right_frame)

        self.file_preview_lbl = tk.Label(right_frame, text="Select a file on the left to preview", font=("Consolas", 9), bg=t["top_bg"], fg=t["subtext"], anchor="w", padx=10)
        self.file_preview_lbl.pack(fill="x")

        preview_scroll = tk.Scrollbar(right_frame)
        preview_scroll.pack(side="right", fill="y")

        self.file_text_area = tk.Text(
            right_frame,
            bg=t["card_bg"],
            fg=t["text"],
            insertbackground="#ffffff",
            font=("Consolas", 10),
            bd=0,
            yscrollcommand=preview_scroll.set,
            wrap="none"
        )
        self.file_text_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        preview_scroll.config(command=self.file_text_area.yview)

        self.load_project_files()

    def load_project_files(self):
        self.file_listbox.delete(0, "end")
        current_dir = os.getcwd()
        
        try:
            items = os.listdir(current_dir)
            for item in sorted(items):
                full_path = os.path.join(current_dir, item)
                if os.path.isfile(full_path):
                    if item.endswith(".py"):
                        icon = "🐍 "
                    elif item.endswith(".json") or item.endswith(".txt") or item.endswith(".log"):
                        icon = "📄 "
                    else:
                        icon = "📦 "
                    self.file_listbox.insert("end", f"{icon}{item}")
        except Exception as e:
            self.file_listbox.insert("end", f"Error: {str(e)}")

    def on_file_selected(self, event=None):
        selection = self.file_listbox.curselection()
        if not selection:
            return

        selected_text = self.file_listbox.get(selection[0])
        filename = selected_text[2:].strip()
        filepath = os.path.join(os.getcwd(), filename)

        self.file_preview_lbl.config(text=f"📄 File: {filename}")
        self.file_text_area.config(state="normal")
        self.file_text_area.delete("1.0", "end")

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                self.file_text_area.insert("end", content)
        except Exception as e:
            self.file_text_area.insert("end", f"Error reading file: {str(e)}")

        self.file_text_area.config(state="disabled")

    # ==========================================
    # --- MODÜL 4: TEMA & MOD SEÇİMİ (CANLI) ---
    # ==========================================
    def on_theme_click(self):
        self.hide_menu()
        self.open_theme_view()

    def open_theme_view(self):
        self.clear_main_content()
        self.active_tab = "theme"
        t = self.themes[self.current_theme]

        theme_frame = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        theme_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Label(
            theme_frame,
            text="🎨 JARVIS THEME & WORK MODE SELECTION",
            font=("Consolas", 12, "bold"),
            bg=t["top_bg"],
            fg=t["accent"],
            pady=8
        )
        header.pack(fill="x")

        cards_container = tk.Frame(theme_frame, bg=t["card_bg"])
        cards_container.pack(expand=True, fill="both", padx=30, pady=20)

        # 4 Farklı Temayı Kart Şeklinde Oluşturma
        for key, theme_info in self.themes.items():
            card = tk.Frame(cards_container, bg=theme_info["top_bg"], bd=2, relief="groove")
            card.pack(fill="x", pady=8, ipady=5)

            # Sol Bilgi Metni
            is_active = " (ACTIVE)" if key == self.current_theme else ""
            title_lbl = tk.Label(
                card,
                text=f"{theme_info['name']}{is_active}",
                font=("Consolas", 11, "bold"),
                bg=theme_info["top_bg"],
                fg=theme_info["accent"]
            )
            title_lbl.pack(side="left", padx=15)

            # Aktifleştir Butonu
            btn = tk.Button(
                card,
                text="Uygula",
                font=("Segoe UI", 9, "bold"),
                bg=theme_info["accent"],
                fg="#000000",
                bd=0,
                padx=15,
                pady=4,
                cursor="hand2",
                command=lambda k=key: self.change_theme_action(k)
            )
            btn.pack(side="right", padx=15)

    def change_theme_action(self, theme_key):
        self.apply_theme(theme_key)
        self.open_theme_view()  # Sayfayı yeni temayla yeniden çiz

    # --- DİĞER BAŞLIKLAR (SIRAYLA DOLDURULACAK) ---
    def on_camera_click(self):
        self.hide_menu()
        self.clear_main_content()
        tk.Label(self.main_content, text="📷 Camera & Vision Module (Standby)", font=("Consolas", 12), bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["accent"]).pack(expand=True)

    def on_settings_click(self):
        self.hide_menu()
        self.clear_main_content()
        tk.Label(self.main_content, text="⚙️ Settings & API Module (Standby)", font=("Consolas", 12), bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["accent"]).pack(expand=True)

    def on_logs_click(self):
        self.hide_menu()
        self.clear_main_content()
        tk.Label(self.main_content, text="📜 Command & Log History Module (Standby)", font=("Consolas", 12), bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["accent"]).pack(expand=True)

    # ==========================================
    # MODÜL: PROJE & DOSYA DEPOSU (KOD GÖRÜNTÜLEYİCİ)
    # ==========================================
    def on_files_click(self):
        """📁 Code File Viewer, Editor & Runner Module"""
        self.hide_menu()
        self.clear_main_content()
        self.active_tab = "files"
        t = self.themes[self.current_theme]

        card = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=5, pady=5)

        # Header Bar
        header = tk.Frame(card, bg=t["top_bg"], height=35)
        header.pack(fill="x")
        
        tk.Label(
            header, 
            text="📁 PROJECT & CODE FILE MANAGER", 
            font=("Consolas", 11, "bold"), 
            bg=t["top_bg"], 
            fg=t["accent"]
        ).pack(side="left", padx=10, pady=5)

        tk.Button(
            header, text="🔄 Refresh", font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text"], bd=0, padx=8, cursor="hand2",
            command=self.refresh_file_list
        ).pack(side="right", padx=5, pady=5)

        # Ana Gövde (Sol: Dosya Listesi | Sağ: Kod Düzenleyici)
        body = tk.Frame(card, bg=t["card_bg"])
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # Sol Panel (Dosya Listesi)
        left_panel = tk.Frame(body, bg=t["top_bg"], width=220)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text=" Directory Files ", font=("Consolas", 9, "bold"), bg=t["top_bg"], fg=t["accent"]).pack(anchor="w", pady=5)

        list_scroll = tk.Scrollbar(left_panel)
        list_scroll.pack(side="right", fill="y")

        self.file_listbox = tk.Listbox(
            left_panel, bg="#0d1117", fg=t["text"], selectbackground=t["accent"], selectforeground="#000000",
            font=("Consolas", 9), bd=0, yscrollcommand=list_scroll.set
        )
        self.file_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.file_listbox.yview)

        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)

        # Sağ Panel (Kod İçeriği ve İşlem Butonları)
        right_panel = tk.Frame(body, bg=t["card_bg"])
        right_panel.pack(side="right", fill="both", expand=True)

        # Dosya Bilgisi ve Aksiyon Barı
        action_bar = tk.Frame(right_panel, bg=t["top_bg"])
        action_bar.pack(fill="x", pady=(0, 5))

        self.lbl_selected_file = tk.Label(action_bar, text="Select a file...", font=("Consolas", 9, "bold"), bg=t["top_bg"], fg=t["subtext"])
        self.lbl_selected_file.pack(side="left", padx=10, pady=5)

        self.btn_run_file = tk.Button(
            action_bar, text="▶️ Run File", font=("Segoe UI", 8, "bold"), bg=t["accent"], fg="#000000", bd=0, padx=10, cursor="hand2",
            state="disabled", command=self.run_selected_python_file
        )
        self.btn_run_file.pack(side="right", padx=5, pady=3)

        self.btn_save_file = tk.Button(
            action_bar, text="💾 Save", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["text"], bd=0, padx=10, cursor="hand2",
            state="disabled", command=self.save_selected_file_content
        )
        self.btn_save_file.pack(side="right", padx=5, pady=3)

        # Kod Metin Editörü
        editor_frame = tk.Frame(right_panel, bg="#0d1117")
        editor_frame.pack(fill="both", expand=True)

        edit_scroll = tk.Scrollbar(editor_frame)
        edit_scroll.pack(side="right", fill="y")

        self.code_editor = tk.Text(
            editor_frame, bg="#0d1117", fg="#39d353", insertbackground="#ffffff",
            font=("Consolas", 10), bd=0, yscrollcommand=edit_scroll.set, wrap="none"
        )
        self.code_editor.pack(side="left", fill="both", expand=True)
        edit_scroll.config(command=self.code_editor.yview)

        self.current_open_file = None
        self.refresh_file_list()

    def refresh_file_list(self):
        """Lists files in the working directory"""
        if not hasattr(self, 'file_listbox') or not self.file_listbox.winfo_exists():
            return
        
        self.file_listbox.delete(0, "end")
        valid_extensions = ('.py', '.json', '.txt', '.log', '.md', '.html', '.css', '.js')
        
        for item in sorted(os.listdir(os.getcwd())):
            if os.path.isfile(item) and item.endswith(valid_extensions):
                self.file_listbox.insert("end", f" 📄 {item}")

    def on_file_selected(self, event=None):
        """Reads the selected file from the list"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        raw_filename = self.file_listbox.get(selection[0]).strip().replace("📄 ", "")
        filepath = os.path.join(os.getcwd(), raw_filename)

        if os.path.exists(filepath):
            self.current_open_file = filepath
            self.lbl_selected_file.config(text=f"Open File: {raw_filename}", fg=self.themes[self.current_theme]["accent"])
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                self.code_editor.delete("1.0", "end")
                self.code_editor.insert("1.0", content)
                self.btn_save_file.config(state="normal")
                
                # Python dosyası ise çalıştırma butonunu aktif et
                if raw_filename.endswith('.py'):
                    self.btn_run_file.config(state="normal")
                else:
                    self.btn_run_file.config(state="disabled")

            except Exception as e:
                messagebox.showerror("ERROR", f"Could not read file: {e}")

    def save_selected_file_content(self):
        """Saves the edited code file"""
        if self.current_open_file and os.path.exists(self.current_open_file):
            try:
                new_content = self.code_editor.get("1.0", "end-1c")
                with open(self.current_open_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.add_log("INFO", f"File saved: {os.path.basename(self.current_open_file)}")
                messagebox.showinfo("Success", "File changes saved.")
            except Exception as e:
                messagebox.showerror("ERROR", f"Could not save file: {e}")

    def run_selected_python_file(self):
        """Runs the selected .py file in the background terminal"""
        if self.current_open_file and self.current_open_file.endswith('.py'):
            filename = os.path.basename(self.current_open_file)
            self.add_log("CMD", f"Running file: python {filename}")
            # Terminal modülüne geçip komutu gönder
            self.on_terminal_click()
            self.run_quick_command(f"python \"{filename}\"")


    # ==========================================
    # MODÜL 1: AYARLAR & API MODÜLÜ (SEÇENEK 1)
    # ==========================================
    def on_settings_click(self):
        """⚙️ Settings & API Management Module"""
        self.hide_menu()
        self.clear_main_content()
        self.active_tab = "settings"
        t = self.themes[self.current_theme]

        card = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=10, pady=10)

        # Başlık Barı
        header = tk.Frame(card, bg=t["top_bg"], height=40)
        header.pack(fill="x")
        tk.Label(header, text="⚙️ SYSTEM, MODEL & API CONFIGURATION", font=("Consolas", 11, "bold"), bg=t["top_bg"], fg=t["accent"]).pack(side="left", padx=15, pady=8)

        # Form Alanı
        form = tk.Frame(card, bg=t["card_bg"])
        form.pack(fill="both", expand=True, padx=30, pady=20)

        # OpenAI API Key
        tk.Label(form, text="OpenAI API Key:", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"]).pack(anchor="w", pady=(5, 2))
        self.entry_openai = tk.Entry(form, font=("Consolas", 10), bg=t["top_bg"], fg=t["text"], insertbackground=t["text"], bd=1, show="*")
        self.entry_openai.insert(0, self.settings.get("openai_key", ""))
        self.entry_openai.pack(fill="x", pady=(0, 15))

        # Google Gemini API Key
        tk.Label(form, text="Google Gemini API Key:", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"]).pack(anchor="w", pady=(5, 2))
        self.entry_gemini = tk.Entry(form, font=("Consolas", 10), bg=t["top_bg"], fg=t["text"], insertbackground=t["text"], bd=1, show="*")
        self.entry_gemini.insert(0, self.settings.get("gemini_key", ""))
        self.entry_gemini.pack(fill="x", pady=(0, 15))

        # NVIDIA NIM API Key
        tk.Label(form, text="NVIDIA NIM / LLM API Key:", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"]).pack(anchor="w", pady=(5, 2))
        self.entry_nvidia = tk.Entry(form, font=("Consolas", 10), bg=t["top_bg"], fg=t["text"], insertbackground=t["text"], bd=1, show="*")
        self.entry_nvidia.insert(0, self.settings.get("nvidia_key", ""))
        self.entry_nvidia.pack(fill="x", pady=(0, 15))

        # Varsayılan AI Modeli Selectimi
        tk.Label(form, text="Default AI Model:", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"]).pack(anchor="w", pady=(5, 2))
        self.model_var = tk.StringVar(value=self.settings.get("default_model", "Gemini 1.5 Pro"))
        model_dropdown = ttk.Combobox(form, textvariable=self.model_var, state="readonly", font=("Consolas", 10))
        model_dropdown['values'] = ("Gemini 1.5 Pro", "GPT-4o", "NVIDIA Llama-3-70B", "Local Mistral")
        model_dropdown.pack(fill="x", pady=(0, 15))

        # Sistem Dili
        tk.Label(form, text="System Language:", font=("Consolas", 10, "bold"), bg=t["card_bg"], fg=t["text"]).pack(anchor="w", pady=(5, 2))
        self.lang_var = tk.StringVar(value=self.settings.get("language", "TR"))
        lang_frame = tk.Frame(form, bg=t["card_bg"])
        lang_frame.pack(anchor="w", pady=(0, 20))
        
        tk.Radiobutton(lang_frame, text="Turkish (TR)", variable=self.lang_var, value="TR", bg=t["card_bg"], fg=t["text"], selectcolor=t["top_bg"], activebackground=t["card_bg"], activeforeground=t["accent"]).pack(side="left", padx=(0, 15))
        tk.Radiobutton(lang_frame, text="English (EN)", variable=self.lang_var, value="EN", bg=t["card_bg"], fg=t["text"], selectcolor=t["top_bg"], activebackground=t["card_bg"], activeforeground=t["accent"]).pack(side="left")

        # Save Butonu
        tk.Button(
            form, text="💾 Save Changes", font=("Segoe UI", 10, "bold"), bg=t["accent"], fg="#000000", bd=0, padx=20, pady=8, cursor="hand2",
            command=self.save_settings_action
        ).pack(anchor="w")

    def save_settings_action(self):
        """Writes settings to config.json"""
        self.settings["openai_key"] = self.entry_openai.get().strip()
        self.settings["gemini_key"] = self.entry_gemini.get().strip()
        self.settings["nvidia_key"] = self.entry_nvidia.get().strip()
        self.settings["default_model"] = self.model_var.get()
        self.settings["language"] = self.lang_var.get()
        self.save_settings()


    # ==========================================
    # MODÜL 2: KOMUT & LOG GEÇMİŞİ (SEÇENEK 2)
    # ==========================================
    def on_logs_click(self):
        """📜 Advanced Command & Log History Module"""
        self.hide_menu()
        self.clear_main_content()
        self.active_tab = "logs"
        t = self.themes[self.current_theme]

        card = tk.Frame(self.main_content, bg=t["card_bg"], bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=10, pady=10)

        # Header Bar
        header = tk.Frame(card, bg=t["top_bg"], height=40)
        header.pack(fill="x")
        tk.Label(header, text="📜 SYSTEM & COMMAND LOG HISTORY", font=("Consolas", 11, "bold"), bg=t["top_bg"], fg=t["accent"]).pack(side="left", padx=15, pady=8)

        # Arama ve Filtreleme Barı
        filter_bar = tk.Frame(card, bg=t["card_bg"])
        filter_bar.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(filter_bar, text="🔍 Loglarda Ara: ", font=("Consolas", 9), bg=t["card_bg"], fg=t["text"]).pack(side="left")
        self.log_search_entry = tk.Entry(filter_bar, font=("Consolas", 9), bg=t["top_bg"], fg=t["text"], insertbackground=t["text"], bd=1)
        self.log_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.log_search_entry.bind("<KeyRelease>", self.filter_logs_display)

        # Filtre Butonları
        self.log_filter_level = "ALL"
        for level_name in ["ALL", "INFO", "CMD", "ERROR"]:
            tk.Button(
                filter_bar, text=level_name, font=("Segoe UI", 8), bg=t["top_bg"], fg=t["text"], bd=0, padx=8, cursor="hand2",
                command=lambda l=level_name: self.set_log_filter(l)
            ).pack(side="left", padx=2)

        # Log Görünüm Konsolu
        body = tk.Frame(card, bg=t["card_bg"])
        body.pack(fill="both", expand=True, padx=15, pady=10)

        scrollbar = tk.Scrollbar(body)
        scrollbar.pack(side="right", fill="y")

        self.log_console = tk.Text(
            body, bg="#07090f", fg="#39d353", font=("Consolas", 9), bd=0, yscrollcommand=scrollbar.set, wrap="word"
        )
        self.log_console.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_console.yview)

        # Renk Etiketleri (Tagging)
        self.log_console.tag_config("INFO", foreground="#39d353")
        self.log_console.tag_config("CMD", foreground="#00f0ff", font=("Consolas", 9, "bold"))
        self.log_console.tag_config("ERROR", foreground="#ff5555", font=("Consolas", 9, "bold"))
        self.log_console.tag_config("TIME", foreground="#8b949e")

        self.filter_logs_display()

        # Bottom Action Bar
        btn_bar = tk.Frame(card, bg=t["top_bg"])
        btn_bar.pack(fill="x")

        tk.Button(
            btn_bar, text="🗑️ Clear Logs", font=("Segoe UI", 9), bg=t["card_bg"], fg=t["text"], bd=0, padx=10, pady=5, cursor="hand2",
            command=self.clear_logs_action
        ).pack(side="right", padx=10, pady=5)

    def set_log_filter(self, level_name):
        self.log_filter_level = level_name
        self.filter_logs_display()

    def filter_logs_display(self, event=None):
        if not hasattr(self, 'log_console') or not self.log_console.winfo_exists():
            return

        query = self.log_search_entry.get().lower() if hasattr(self, 'log_search_entry') else ""
        self.log_console.config(state="normal")
        self.log_console.delete("1.0", "end")

        for log in self.system_logs:
            level = log.get('level', 'INFO')
            msg = log.get('msg', '')
            time_str = log.get('time', '')

            # Check compatibility with the filter and search query
            if self.log_filter_level != "ALL" and self.log_filter_level != "ALL" and level != self.log_filter_level:
                continue
            if query and query not in msg.lower() and query not in level.lower():
                continue

            self.log_console.insert("end", f"[{time_str}] ", "TIME")
            self.log_console.insert("end", f"[{level}] ", level)
            self.log_console.insert("end", f"{msg}\n")

        self.log_console.config(state="disabled")
        self.log_console.see("end")

    def clear_logs_action(self):
        self.system_logs.clear()
        self.add_log("INFO", "Log history cleared.")
        self.filter_logs_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root, standalone=True)
    root.mainloop()

