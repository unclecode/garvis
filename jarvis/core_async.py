import threading
import json, time
import asyncio
import base64
import websockets
import subprocess

from groq import Groq as Groqq
from openai import OpenAI as OpenAII

from .audio_processor_async import AudioProcessor
from .listening_strategy import *
from .config import *
from .listening_strategy import *
from .llm import *
from .utils import websocker_text_iterator, create_mpv_process

class Jarvis:
    def __init__(self, 
                 assistant_name: str = DEFAULT_ASSISTANT_NAME, 
                 llm: LLM = AsyncOpenAI(),
                 listening_strategy: ListeningStrategy = None, 
                 transcriptor=DEFAULT_TRANSCRIPTOR, 
                 verbose: bool = False):
        self.assistant_name = assistant_name
        self.llm = llm
        strategy = listening_strategy or ContinuousUntilSilenceStrategy(verbose=verbose)
        self.audio_processor = AudioProcessor(self, strategy=strategy, verbose=verbose, transcriptor=transcriptor)
        self.collected_text = []
        self.history = []
        self.transcription_lock = threading.Lock()
        self.current_user_message = None
        self.mpv_process = None
        self.stop_streaming = False
        self.verbose = verbose
        self.llm = llm
        self.system_message = get_system_message(self.assistant_name)

        self.on_log = None
        self.on_transcription_start = None
        self.on_transcription_stop = None
        self.on_transcription_update = None
        self.on_llm_update = None
        self.on_llm_start = None
        self.on_llm_stop = None
        self.on_tts_stop = None
        self.on_tts_start = None
        self.audio_processor.on_audio_power = self.on_audio_power

    def log(self, message):
        if self.on_log and self.verbose:
            self.on_log(message)

    def transcription_start(self):
        if self.on_transcription_start:
            self.on_transcription_start()

    def transcription_stop(self):
        asyncio.create_task(self.process_collected_text())
        # To stop the ongoing TTS if any
        self.stop_tts()
        if self.on_transcription_stop:
            self.on_transcription_stop()

    def transcription_update(self, index, text):
        # Append transcription to collected text
        with self.transcription_lock:
            self.collected_text.append({"index": index, "text": text})
            self.collected_text.sort(key=lambda x: x["index"])
                        
            if self.on_transcription_update:
                self.on_transcription_update(index, text)

    def llm_update(self, text):
        if self.on_llm_update:
            self.on_llm_update(text)
        
    def llm_start(self):
        if self.on_llm_start:
            self.on_llm_start()
            
    def llm_stop(self):
        if self.on_llm_stop:
            self.on_llm_stop()
            
    def tts_start(self):
        if self.on_tts_start:
            self.on_tts_start()

    def tts_stop(self):
        if self.on_tts_stop:
            self.on_tts_stop()

    def on_audio_power(self, power):
        # Implement this in the consuming class if needed
        pass

    async def process_collected_text(self):
        with self.transcription_lock:
            all_text = ", ".join([chunk["text"] for chunk in self.collected_text])
        
        await self.get_llm_response(all_text)

    def stop_talking(self, raise_event=False):
        self.restart_mpv()
        # self.stop_tts(raise_event=raise_event)
        
    def stop_tts(self, raise_event=True):
        if self.mpv_process and self.mpv_process.poll() is None:
            # self.stop_streaming = True
            self.mpv_process.terminate()  # Send a SIGTERM signal to the process
            try:
                self.mpv_process.wait(timeout=2)  # Wait for the process to terminate
            except subprocess.TimeoutExpired:
                self.mpv_process.kill()  # Force kill if it does not terminate in time
            finally:
                self.mpv_process = None
                raise_event and self.tts_stop()
    
    def restart_mpv(self):
        self.stop_tts(raise_event=False)
        time.sleep(0.2)

    async def text_to_speech_input_streaming(self, text_iterator):
        async with websockets.connect(WEBSOCKET_URI) as websocket:
            await websocket.send(json.dumps({
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                "xi_api_key": ELEVENLABS_API_KEY,
            }))

            async def listen():
                first_chunk = True
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if data.get("audio"):
                            if first_chunk:
                                first_chunk = False
                                if self.on_tts_start:
                                    self.on_tts_start()
                            audio_data = base64.b64decode(data["audio"])
                            yield audio_data
                        elif data.get('isFinal'):
                            break
                    except websockets.exceptions.ConnectionClosed:
                        self.log("Connection closed")
                        break

            async def stream(audio_stream):
                self.mpv_process = create_mpv_process()
                self.log("Started streaming audio")
                
                # if mvp process is None wait a bit
                if not self.mpv_process:
                    await asyncio.sleep(0.5)
                    
                if not self.mpv_process:
                    self.log("Failed to start mpv process")
                    return
                
                async for chunk in audio_stream:
                    if chunk:
                        try:
                            if not self.mpv_process:
                                break
                            self.mpv_process.stdin.write(chunk)
                            self.mpv_process.stdin.flush()
                        except BrokenPipeError:
                            break

                if self.mpv_process:
                    if self.mpv_process.stdin:
                        self.mpv_process.stdin.close()
                    self.mpv_process.wait()
                    
                    self.restart_mpv()

            listen_task = asyncio.create_task(stream(listen()))

            async for text in websocker_text_iterator(text_iterator):
                await websocket.send(json.dumps({"text": text, "try_trigger_generation": True}))

            await websocket.send(json.dumps({"text": ""}))

            await listen_task

    async def get_llm_response(self, text):
        self.history.append({"role": "user", "content": text})

        def llm_task():
            asyncio.run(self.process_llm_response())

        threading.Thread(target=llm_task).start()

    async def process_llm_response(self):
        # self.history.append({"role": "user", "content": text})
        stream = await self.llm.acompletion(
            messages=[
                {"role": "system", "content": self.system_message},
                *self.history
            ],
        )

        self.llm_start()

        async def text_iterator():
            chunks = []
            async for chunk in stream:
                response_text = chunk.choices[0].delta.content
                if response_text:
                    self.llm_update(response_text)
                    chunks.append(response_text)
                    yield response_text
            self.history.append({"role": "assistant", "content": " ".join(chunks)})
            self.llm_stop()

        await self.text_to_speech_input_streaming(text_iterator())

    async def listen(self):
        # self.stop_tts(raise_event=False)
        # asyncio.create_task(self.audio_processor.toggle_listen())
        await self.audio_processor.toggle_listen()
