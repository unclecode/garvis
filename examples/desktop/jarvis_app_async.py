import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import sys, os
import tkinter as tk
import asyncio
import threading
from jarvis.core_async import Jarvis
from ui_manager import UIManager
from jarvis.audio_processor_async import *
from jarvis.config import *
from jarvis.llm import *

class JarvisApp:
    def __init__(self, master):
        self.master = master
        self.assistant_name = "Jarvis"
        self.ui_manager = UIManager(master, self)
        
        # Create a new event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.jarvis = Jarvis(
            assistant_name=self.assistant_name,
            listening_strategy=RealTimeWithSilenceStrategy(threshold_silence=0.1, threshold_end=2.5),
            transcriptor="groq",
            llm=AsyncGroq(),
            verbose=True
        )
        self.current_user_message = None
        self.current_jarvis_message = None
        self.collected_text = []
        self.setup_event_handlers()
        self.last_text = ""

        self.ui_manager.setup_ui()
        threading.Thread(target=self.run_asyncio_loop, daemon=True).start()

    def setup_event_handlers(self):
        self.jarvis.on_log = self.log
        self.jarvis.on_transcription_start = self.on_transcription_start
        self.jarvis.on_transcription_stop = self.on_transcription_stop
        self.jarvis.on_transcription_update = self.on_transcription_update
        self.jarvis.on_llm_update = self.on_llm_update
        self.jarvis.on_llm_start = self.on_llm_start
        self.jarvis.on_llm_stop = self.on_llm_stop
        self.jarvis.on_tts_start = self.on_tts_start
        self.jarvis.on_tts_stop = self.on_tts_stop
        self.jarvis.audio_processor.on_audio_power = self.on_audio_power

    def log(self, message):
        self.ui_manager.log(message)

    def on_transcription_start(self):
        self.ui_manager.log("Listening...")
        self.ui_manager.update_circle_color("red")
        self.ui_manager.update_user_message("")

    def on_transcription_stop(self):
        self.ui_manager.log("Stopped listening.")
        self.ui_manager.update_circle_color("green")
        self.ui_manager.update_user_message(None, final=True)
        
        self.ui_manager.log("AI is generating response...")
        self.ui_manager.update_jarvis_message("")

    def on_transcription_update(self, index, text):
        self.ui_manager.log(f"Transcription for chunk {index}: {text}")
        if not self.last_text or self.last_text[-1] in [".", "?", "!"]:
            self.ui_manager.update_user_message(text)
        else:
            self.ui_manager.update_user_message(", " + text.lstrip())
            
        self.last_text = text 

    def on_llm_start(self):
        # self.ui_manager.log("AI is generating response...")
        # self.ui_manager.update_jarvis_message("")
        pass

    def on_llm_update(self, text):
        self.ui_manager.update_jarvis_message(text)
        
    def on_llm_stop(self):
        self.ui_manager.log("AI response generated.")
        self.ui_manager.update_jarvis_message(None, final=True)
        try:
            self.master.force_focus()
        except:           
            pass

    def on_tts_start(self):
        self.ui_manager.enable_stop_button()

    def on_tts_stop(self):
        self.ui_manager.disable_stop_button()
        try:
            self.master.force_focus()
        except:           
            pass

    def on_audio_power(self, power, event=None):
        self.ui_manager.update_circle_glow(power)

    def start_listening(self, event=None):
        asyncio.run_coroutine_threadsafe(self.jarvis.listen(), self.loop)

    def stop_audio(self, event=None):
        self.jarvis.stop_tts()

    def run_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisApp(root)
    root.mainloop()
