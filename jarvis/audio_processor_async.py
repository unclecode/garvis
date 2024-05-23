from groq import Groq
import pyaudio
import wave
import webrtcvad
import numpy as np
import io
import time
from .utils import *
from .config import *
from .listening_strategy import *

class AudioProcessor:
    def __init__(self, jarvis, strategy, transcriptor=DEFAULT_TRANSCRIPTOR, verbose=False):
        assert jarvis is not None, "Jarvis instance is required."
        assert strategy is not None, "Listening strategy is required."
        self.jarvis = jarvis
        self.strategy = strategy
        self.audio_frames = []
        self.chunk_index = 0
        self.vad = webrtcvad.Vad(1)
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=SAMPLE_RATE,
                                      input=True,
                                      frames_per_buffer=FRAME_SIZE)
        self.listening = False
        self.on_audio_power = None
        
        self.transcriptor = transcriptor
        
        self.FRAME_SIZE = FRAME_SIZE
        self.SAMPLE_RATE = SAMPLE_RATE
        self.THRESHOLD_SILENCE = THRESHOLD_SILENCE
        self.FRAME_DURATION_MS = FRAME_DURATION_MS
        self.SPEECH_THRESHOLD = SPEECH_THRESHOLD
        self.MIN_AUDIO_LENGTH = MIN_AUDIO_LENGTH
        self.RECORD_DURATION = RECORD_DURATION        
        
        self.verbose = verbose

    def log(self, message):
        if self.verbose:
            self.jarvis.log(message)

    def update_listening_strategy(self, strategy):
        self.strategy = create_instance(strategy)
        self.log(f"Listening strategy updated to {strategy}")

    def update_audio_settings(self, threshold_silence, frame_duration, speech_threshold, min_audio_length, record_duration):
        self.THRESHOLD_SILENCE = threshold_silence
        self.FRAME_DURATION_MS = frame_duration
        self.SPEECH_THRESHOLD = speech_threshold
        self.MIN_AUDIO_LENGTH = min_audio_length
        self.RECORD_DURATION = record_duration
        self.log("Audio settings updated.")

    async def stop_listening(self):
        if self.listening:
            await self.toggle_listen()
            
    async def start_listening(self):
        if not self.listening:
            await self.toggle_listen()
    
    async def toggle_listen(self, event=None):
        if self.listening:
            self.log("Stopping listening. Waiting for the last chunk to process...")
            self.listening = False
            self.stream.stop_stream()
            # if self.audio_frames:
            #     await self.process_audio(self.chunk_index + 1, self.audio_frames.copy())
            self.log("Stopped listening.")
            self.jarvis.transcription_stop()
        else:
            self.listening = True
            self.jarvis.transcription_start()
            self.stream.start_stream()
            self.log("Started listening.")
            await self.strategy.listen(self)

    def on_audio_power(self, power):
        if self.on_audio_power:
            self.on_audio_power(power)

    async def process_audio(self, index, audio_frames, stop_listening=False, callback=None):
        if not self.listening:
            self.log(f"Skipping chunk {index} processing. Not listening.")
            return
            
        if not self.has_speech(audio_frames):
            self.log(f"No significant speech detected in chunk {index}. Skipping transcription.")
            return

        in_memory_file = io.BytesIO()
        wf = wave.open(in_memory_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(audio_frames))
        wf.close()

        self.log("Audio saved to in-memory file.")

        text = await self.transcribe_audio(in_memory_file)
        # text = "Why sky is blue?"
        
        self.jarvis.transcription_update(index, text)

        if callback:
            if not callback(self, index, text):
                return 
        
        if stop_listening:
            await self.toggle_listen()

    def has_speech(self, audio_frames):
        audio_data = b''.join(audio_frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        return np.max(np.abs(audio_array)) > SPEECH_THRESHOLD

    async def transcribe_audio(self, in_memory_file):
        if self.transcriptor == "groq":
            return await self.transcribe_audio_groq(in_memory_file)
        elif self.transcriptor == "colab":
            return await self.transcribe_audio_colab(in_memory_file)
        
    async def transcribe_audio_groq(self, in_memory_file):
        client = Groq()
        transcription = ""

        in_memory_file.seek(0)
        start = time.time()
        transcription = await client.audio.transcriptions.create(
            file=("in_memory_audio.wav", in_memory_file.read()),
            model="whisper-large-v3",
        )
        end = time.time()
        self.log(f"Transcription time: {end - start:.2f} seconds")
        return transcription.text

    async def transcribe_audio_colab(self, in_memory_file):
        in_memory_file.seek(0)
        start = time.time()
        
        full_result = await acall_transcribe(in_memory_file)
        text = [segment["text"] for segment in full_result["segments"]]
        text = " ".join(text)
        
        end = time.time()
        self.log(f"Transcription time: {end - start:.2f} seconds")
        return text

