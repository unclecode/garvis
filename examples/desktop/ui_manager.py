# ui_manager.py

import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk
import json
from garvis.utils import get_listening_strategies
from garvis.config import *

# Constants
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
USER_AVATAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user.png")
GARVIS_AVATAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "garvis.jpeg")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

class UIManager:
    def __init__(self, master, app):
        self.master = master
        self.app = app
        self.avatars = {
            "You": USER_AVATAR,
            "Garvis": GARVIS_AVATAR
        }
        self.stop_button = None
        self.listen_strategy_var = tk.StringVar(value="ContinuousUntilSilenceStrategy")
        self.assistant_name_var = tk.StringVar(value="Garvis")
        self.threshold_silence_var = tk.DoubleVar(value=THRESHOLD_SILENCE)
        self.frame_duration_var = tk.IntVar(value=FRAME_DURATION_MS)
        self.speech_threshold_var = tk.IntVar(value=SPEECH_THRESHOLD)
        self.min_audio_length_var = tk.DoubleVar(value=MIN_AUDIO_LENGTH)
        self.record_duration_var = tk.IntVar(value=5)
        
        self.load_settings()

    def setup_ui(self):
        self.master.title("Garvis (Groq+Garvis)")
        self.master.geometry("600x1000")
        
        self.master.focus_force()

        self.tabs = ttk.Notebook(self.master)
        self.transcription_tab = ttk.Frame(self.tabs)
        self.log_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.transcription_tab, text="Transcription")
        self.tabs.add(self.log_tab, text="Logs")
        self.tabs.add(self.settings_tab, text="Settings")
        self.tabs.pack(expand=1, fill="both")

        self.setup_transcription_tab()
        self.setup_log_tab()
        self.setup_settings_tab()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_window_position()

    def setup_transcription_tab(self):
        self.transcription_frame = ttk.Frame(self.transcription_tab)
        self.transcription_frame.pack(expand=1, fill="both", padx=10, pady=10)

        self.buttons_frame = ttk.Frame(self.transcription_frame)
        self.buttons_frame.pack(pady=10)

        self.canvas = tk.Canvas(self.buttons_frame, width=100, height=100, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=5)
        self.circle = self.canvas.create_oval(10, 10, 90, 90, fill="green", outline="")
        self.text = self.canvas.create_text(50, 50, text="●", fill="white", font=("Helvetica", 24))
        self.canvas.bind("<Button-1>", self.app.start_listening)

        self.stop_button_canvas = tk.Canvas(self.buttons_frame, width=100, height=100, highlightthickness=0)
        self.stop_button_canvas.pack(side=tk.LEFT, padx=5)
        self.stop_button_circle = self.stop_button_canvas.create_oval(10, 10, 90, 90, fill="gray", outline="")
        self.stop_button_text = self.stop_button_canvas.create_text(50, 50, text="●", fill="white", font=("Helvetica", 24))
        self.stop_button_canvas.bind("<Button-1>", self.app.stop_audio)

        self.messages_frame = ttk.Frame(self.transcription_frame)
        self.messages_frame.pack(expand=1, fill="both", pady=10)
        self.messages_frame.columnconfigure(0, weight=1)
        self.messages_frame.rowconfigure(0, weight=1)

        self.message_canvas = tk.Canvas(self.messages_frame)
        self.scrollbar = ttk.Scrollbar(self.messages_frame, orient="vertical", command=self.message_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.message_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.message_canvas.configure(
                scrollregion=self.message_canvas.bbox("all")
            )
        )

        self.message_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.message_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.message_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

    def setup_log_tab(self):
        self.log_frame = ttk.Frame(self.log_tab)
        self.log_frame.pack(expand=1, fill="both", padx=10, pady=10)

        self.console_display = tk.Text(self.log_frame, height=20, width=70)
        self.console_display.pack(pady=10)

    def setup_settings_tab(self):
        self.settings_frame = ttk.Frame(self.settings_tab)
        self.settings_frame.pack(expand=1, fill="both", padx=10, pady=10)

        ttk.Label(self.settings_frame, text="Assistant Name:").pack(pady=5)
        tk.Entry(self.settings_frame, textvariable=self.assistant_name_var).pack(pady=5)

        ttk.Label(self.settings_frame, text="Listening Strategy:").pack(pady=5)
        listen_strategies = get_listening_strategies()
        strategy_combobox = ttk.Combobox(self.settings_frame, textvariable=self.listen_strategy_var, values=listen_strategies, state="readonly")
        strategy_combobox.pack(pady=5)

        ttk.Label(self.settings_frame, text="Threshold Silence (seconds):").pack(pady=5)
        tk.Entry(self.settings_frame, textvariable=self.threshold_silence_var).pack(pady=5)

        ttk.Label(self.settings_frame, text="Frame Duration (ms):").pack(pady=5)
        tk.Entry(self.settings_frame, textvariable=self.frame_duration_var).pack(pady=5)

        ttk.Label(self.settings_frame, text="Speech Threshold:").pack(pady=5)
        tk.Entry(self.settings_frame, textvariable=self.speech_threshold_var).pack(pady=5)

        ttk.Label(self.settings_frame, text="Minimum Audio Length (seconds):").pack(pady=5)
        tk.Entry(self.settings_frame, textvariable=self.min_audio_length_var).pack(pady=5)

        ttk.Button(self.settings_frame, text="Save Settings", command=self.save_settings).pack(pady=10)

    def update_circle_glow(self, power):
        normalized_power = min(max(power, 0), 1)
        intensity = int(normalized_power * 255)
        color = f'#{intensity:02x}0000'
        self.canvas.itemconfig(self.circle, fill=color)

    def enable_stop_button(self):
        self.stop_button_canvas.itemconfig(self.stop_button_circle, fill="purple")
        self.stop_button_canvas.config(state=tk.NORMAL)

    def disable_stop_button(self):
        self.stop_button_canvas.itemconfig(self.stop_button_circle, fill="gray")
        self.stop_button_canvas.config(state=tk.DISABLED)

    def log(self, message):
        self.console_display.insert(tk.END, message + "\n")
        self.console_display.see(tk.END)

    def update_circle_color(self, color):
        self.canvas.itemconfig(self.circle, fill=color)

    def create_message_frame(self, sender, text, avatar="You"):
        avatar = self.avatars.get(avatar, USER_AVATAR)
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=5)

        img = Image.open(avatar)
        img = img.resize((40, 40), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        label = ttk.Label(frame, image=photo)
        label.image = photo
        label.pack(side="left", padx=5)

        msg = ttk.Label(frame, text=f"{sender}: {text}", wraplength=400, anchor="w", justify="left")
        msg.pack(side="left", padx=5, fill="x", expand=True)

        return frame, msg

    def append_message_text(self, text):
        if not text:
            return
        if self.scrollable_frame.winfo_children():
            last_message = self.scrollable_frame.winfo_children()[-1]
            if len(last_message.winfo_children()) > 1:
                msg_label = last_message.winfo_children()[1]
                msg_label.config(text=msg_label.cget("text") + text)
                self.message_canvas.yview_moveto(1)
            else:
                self.log("Expected message label not found in last message frame.")
        else:
            self.log("No messages found in scrollable frame.")

    def update_user_message(self, text, final=False):
        if self.app.current_garvis_message:
            return
        if not self.app.current_user_message:
            self.app.current_user_message = self.create_message_frame("You", "")
            
        if self.app.current_user_message and text:
            self.append_message_text(text)
            
        if final:
            self.app.current_user_message = None

    def update_garvis_message(self, text, final=False):
        if not self.app.current_garvis_message:
            self.app.current_garvis_message = self.create_message_frame("Garvis", text, "Garvis")
            
        if self.app.current_garvis_message and text:
            self.append_message_text(text)
            
        if final:
            self.app.current_garvis_message = None
        

    def on_closing(self):
        self.save_window_position()
        self.master.destroy()

    def load_window_position(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                config = json.load(file)
                self.master.geometry(f"+{config['x']}+{config['y']}")
                self.log(f"Loaded window position: ({config['x']}, {config['y']})")

    def save_window_position(self):
        config = {
            'x': self.master.winfo_x(),
            'y': self.master.winfo_y()
        }
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file)
        self.log(f"Saved window position: ({config['x']}, {config['y']})")

    def save_settings(self):
        self.app.assistant_name = self.assistant_name_var.get()
        self.app.update_listening_strategy(self.listen_strategy_var.get())
        self.app.update_audio_settings(
            threshold_silence=self.threshold_silence_var.get(),
            frame_duration=self.frame_duration_var.get(),
            speech_threshold=self.speech_threshold_var.get(),
            min_audio_length=self.min_audio_length_var.get(),
            record_duration=self.record_duration_var.get()
        )
        settings = {
            'assistant_name': self.assistant_name_var.get(),
            'listen_strategy': self.listen_strategy_var.get(),
            'threshold_silence': self.threshold_silence_var.get(),
            'frame_duration': self.frame_duration_var.get(),
            'speech_threshold': self.speech_threshold_var.get(),
            'min_audio_length': self.min_audio_length_var.get(),
            'record_duration': self.record_duration_var.get()
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
        self.log("Settings saved to settings.json")
        self.log("Settings saved.")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                self.assistant_name_var.set(settings.get('assistant_name', 'Garvis'))
                self.listen_strategy_var.set(settings.get('listen_strategy', 'ContinuousUntilSilenceStrategy'))
                self.threshold_silence_var.set(settings.get('threshold_silence', 0.5))
                self.frame_duration_var.set(settings.get('frame_duration', 30))
                self.speech_threshold_var.set(settings.get('speech_threshold', 500))
                self.min_audio_length_var.set(settings.get('min_audio_length', 2))
                self.record_duration_var.set(settings.get('record_duration', 5))
