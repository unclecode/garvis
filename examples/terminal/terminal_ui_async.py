import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import asyncio
from garvis.core_async import Garvis
from garvis.utils import *
from garvis.listening_strategy import *

class TerminalUI:
    def __init__(self):
        self.garvis = Garvis(
            listening_strategy= RealTimeWithSilenceStrategy(threshold_silence=0.3, threshold_end=3.5),
            # listening_strategy= RealTimeStrategy(threshold_silence=0.3),
            # listening_strategy= IntentBaseRealTimeStrategy(),
            # transcriptor="colab",
            transcriptor="groq",
        )
        self.setup_event_handlers()
        self.transcription_buffer = ""
        self.user_message_updating = False
        self.assistant_message_updating = False
        
        self.print_lock = asyncio.Lock()

    def setup_event_handlers(self):
        self.garvis.on_log = self.log
        self.garvis.on_transcription_start = self.transcription_start
        self.garvis.on_transcription_stop = self.transcription_stop
        self.garvis.on_transcription_update = self.transcription_update
        self.garvis.on_llm_update = self.llm_update
        self.garvis.on_llm_start = self.llm_start
        self.garvis.on_llm_stop = self.llm_stop
        self.garvis.on_tts_start = self.tts_start
        self.garvis.on_tts_stop = self.tts_stop
        self.garvis.audio_processor.on_audio_power = self.audio_power

    def log(self, message):
        xprint(f"[LOG] {message}", color="dim")

    def transcription_start(self):
        print("\r" + " " * len("Press any key to listen or 'q' to quit."), end="", flush=True)
        xprint("Talk: ", color="yellow", style="bold", end="", pre="\r")

    def transcription_update(self, index, text):
        self.transcription_buffer += text + " "
        xprint(text, color="yellow", end="")

    def transcription_stop(self):
        self.transcription_buffer = ""

    def llm_start(self):
        xprint("\n\rGarvis: ", style="bold", color="green", end="")

    def llm_update(self, text):
        text = text.replace("\n", "\n\r")
        xprint(text, color="green", end="")
        
    def llm_stop(self):
        # asyncio.create_task(self.wait_for_keypress())
        pass
    
    def tts_start(self):
        pass

    def tts_stop(self):
        asyncio.create_task(self.wait_for_keypress())
        pass

    def audio_power(self, power):
        pass

    async def start_listening(self):
        self.garvis.stop_talking()
        asyncio.create_task(self.garvis.listen())

    async def wait_for_keypress(self):
        xprint("\n\rPress any key to listen or 'q' to quit.\n\r", color="bright_black", end="")
        key = await get_keypress()
        if key == 'q':
            async with self.print_lock:
                xprint("Exiting...", color="bright_black")
            sys.exit(0)
        else:
            await self.start_listening()

    async def start(self):
        xprint("\rHello, I am Garvis.", end="")
        await self.wait_for_keypress()
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    ui = TerminalUI()
    asyncio.run(ui.start())
