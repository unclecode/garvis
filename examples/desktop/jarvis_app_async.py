import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import tkinter as tk
import asyncio
from jarvis.core_async import Jarvis
from ui_manager import UIManager
# from jarvis.listening_strategy import ContinuousUntilSilenceStrategy, RealTimeStrategy
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
            listening_strategy=ContinuousUntilSilenceStrategy(verbose=True),
            # listening_strategy= RealTimeStrategy(threshold_silence = 0.3),
            transcriptor="colab",
            llm=AsyncGroq(),
            verbose=True
        )
        self.current_user_message = None
        self.current_jarvis_message = None
        self.collected_text = []
        self.setup_event_handlers()

        self.ui_manager.setup_ui()
        

    def setup_event_handlers(self):
        self.jarvis.on_log = self.log
        self.jarvis.on_transcription_start = self.on_transcription_start
        self.jarvis.on_transcription_stop = self.on_transcription_stop
        self.jarvis.on_transcription_update = self.on_transcription
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

    def on_transcription(self, index, text):
        self.ui_manager.log(f"Transcription for chunk {index}: {text}")
        self.ui_manager.update_user_message(text)

    def on_llm_start(self):
        self.ui_manager.log("AI is generating response...")
        self.ui_manager.update_jarvis_message("")

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
        asyncio.run(self.jarvis.listen())

    def stop_audio(self, event=None):
        self.jarvis.stop_tts()

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisApp(root)
    root.mainloop()
