import asyncio
import time
import numpy as np

from abc import ABC, abstractmethod

class ListeningStrategy(ABC):

    def callback(self, audio_processor, index, text) -> bool:
        return True
        pass
    
    @abstractmethod
    def listen(self, audio_processor):
        pass
    
    def calculate_audio_power(self, audio_data):
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        power = np.linalg.norm(audio_array) / len(audio_array)
        normalized_power = power / 100  # Normalizing the power value
        return normalized_power 

class RealTimeStrategy(ListeningStrategy):
    def __init__(self, stop_criteria=None, *args, **kwargs):
        self.stop_criteria = stop_criteria
        self.last_text = False
        self.threshold_silence = kwargs.get("threshold_silence", 0.5)
        self.threshold_end = kwargs.get("threshold_end", self.threshold_silence * 8)
    
    def callback(self, audio_processor, index, text) -> bool:
        if self.last_text:
            audio_processor.audio_frames = []
            asyncio.create_task(audio_processor.toggle_listen())
            return False # There is no text to be passed to the transcription_update method
        elif text and self.stop_criteria and self.stop_criteria(text):
            audio_processor.audio_frames = []
            asyncio.create_task(audio_processor.toggle_listen())
            return False # There is no text to be passed to the transcription_update method
            
        return True # There is text to be passed to the transcription_update method

    async def listen(self, audio_processor):
        audio_processor.audio_frames = []
        silence_start = None
        start_time = None
        last_speech = None

        while audio_processor.listening:
            try:
                if audio_processor.stream.is_active():
                    data = audio_processor.stream.read(audio_processor.FRAME_SIZE, exception_on_overflow=False)
                    audio_power = self.calculate_audio_power(data)
                    audio_processor.on_audio_power(audio_power)
                    
                    audio_processor.audio_frames.append(data)
                    
                    now_time = time.time()

                    if start_time is None:
                        start_time = now_time

                    is_speech = audio_processor.vad.is_speech(data, audio_processor.SAMPLE_RATE)
                    if not is_speech:
                        if silence_start is None:
                            silence_start = now_time
                        elif now_time - silence_start > self.threshold_silence:
                            audio_length = now_time - start_time
                            if audio_length >= audio_processor.MIN_AUDIO_LENGTH:
                                audio_processor.log("Silence detected. Processing audio...")
                                audio_processor.chunk_index += 1
                                await audio_processor.process_audio(audio_processor.chunk_index, audio_processor.audio_frames.copy(), False, self.callback)
                                silence_start = None
                                start_time = None
                                audio_processor.audio_frames = []
                            else:
                                audio_processor.log("Audio length less than minimum threshold. Continuing to capture audio.")
                    else:
                        last_speech = now_time
                        silence_start = None
                        
                    if last_speech and now_time - last_speech > self.threshold_end:
                        audio_processor.log("Extended silence detected. Stopping listening.")
                        self.last_text = True
                        await audio_processor.process_audio(audio_processor.chunk_index, audio_processor.audio_frames.copy(), True, self.callback)
                        return
            except IOError as e:
                if e.errno == -9981:
                    audio_processor.log("Buffer overflow. Dropping frames.")
                    continue
                else:
                    raise

class FixedDurationStrategy(ListeningStrategy):
    def __init__(self, recording_timespan=10):
        self.recording_timespan = recording_timespan
        pass

    async def listen(self, audio_processor):
        audio_processor.audio_frames = []
        start_time = time.time()

        while audio_processor.listening:
            try:
                if audio_processor.stream.is_active():
                    data = audio_processor.stream.read(audio_processor.FRAME_SIZE, exception_on_overflow=False)
                    audio_power = self.calculate_audio_power(data)
                    audio_processor.on_audio_power(audio_power)

                    audio_processor.audio_frames.append(data)

                if time.time() - start_time > self.recording_timespan:
                    audio_processor.log(f"Listening duration of {self.recording_timespan} seconds completed. Processing audio...")
                    audio_processor.chunk_index += 1
                    await audio_processor.process_audio(audio_processor.chunk_index, audio_processor.audio_frames.copy(), True, self.callback)
                    start_time = time.time()
                    audio_processor.audio_frames = []
                    return
            except IOError as e:
                if e.errno == -9981:
                    audio_processor.log("Buffer overflow. Dropping frames.")
                    continue
                else:
                    raise

class RealTimeWithSilenceStrategy(ListeningStrategy):
    def __init__(self, *args, **kwargs):
        self.threshold_silence = kwargs.get("threshold_silence", 0.5)
        self.threshold_end = kwargs.get("threshold_end", self.threshold_silence * 8)
        pass

    async def listen(self, audio_processor):
        audio_processor.audio_frames = []
        silence_start = None
        start_time = None
        last_spoken_time = time.time()

        while audio_processor.listening:
            try:
                if audio_processor.stream.is_active():
                    data = audio_processor.stream.read(audio_processor.FRAME_SIZE, exception_on_overflow=False)
                    audio_power = self.calculate_audio_power(data)
                    audio_processor.on_audio_power(audio_power)
                    
                    audio_processor.audio_frames.append(data)

                    if start_time is None:
                        start_time = time.time()

                    is_speech = audio_processor.vad.is_speech(data, audio_processor.SAMPLE_RATE)
                    current_time = time.time()

                    if not is_speech:
                        if silence_start is None:
                            silence_start = current_time
                        elif current_time - silence_start > self.threshold_silence:
                            audio_length = current_time - start_time
                            if audio_length >= audio_processor.MIN_AUDIO_LENGTH:
                                audio_processor.log("Silence detected. Processing audio...")
                                audio_processor.chunk_index += 1
                                audio_processor.process_audio(audio_processor.chunk_index, audio_processor.audio_frames.copy(), False, self.callback)
                                silence_start = None
                                start_time = None
                                audio_processor.audio_frames = []
                            else:
                                # audio_processor.log("Audio length less than minimum threshold. Continuing to capture audio.")
                                pass
                    else:
                        silence_start = None
                        last_spoken_time = current_time

                    # Check if we need to stop listening due to extended silence
                    if current_time - last_spoken_time > self.threshold_end:
                        audio_processor.log("Extended silence detected. Stopping listening.")
                        await audio_processor.toggle_listen()
                        return
            except IOError as e:
                if e.errno == -9981:
                    audio_processor.log("Buffer overflow. Dropping frames.")
                    continue
                else:
                    raise

class IntentBaseRealTimeStrategy(RealTimeStrategy):
    def __init__(self, ending_class = "QUESTION", last_n_sentence = 3, llm=None):
        super().__init__(self.stop_criteria)
        self.llm = llm or Groq()
        self.end_class = ending_class
    
    def stop_criteria(self, text):
        sentences = text.split(".")
        last_3_sentences = sentences[-3:]
        intent = self.llm.intentify(". ".join(last_3_sentences))
        print(f"Intent: {intent}")
        return intent == self.end_class
                   
class ContinuousUntilSilenceStrategy(ListeningStrategy):
    def __init__(self, *args, **kwargs):
        self.threshold_silence = kwargs.get("threshold_silence", 0.1)
        pass
    
    async def listen(self, audio_processor):
        audio_processor.audio_frames = []
        silence_start = None

        while audio_processor.listening:
            try:
                if audio_processor.stream.is_active():
                    data = audio_processor.stream.read(audio_processor.FRAME_SIZE, exception_on_overflow=False)
                    audio_power = self.calculate_audio_power(data)
                    audio_processor.on_audio_power(audio_power)
                    audio_processor.audio_frames.append(data)

                    is_speech = audio_processor.vad.is_speech(data, audio_processor.SAMPLE_RATE)
                    if not is_speech:
                        if silence_start is None:
                            silence_start = time.time()
                        elif (time.time() - silence_start) > self.threshold_silence:
                            audio_processor.log("Silence detected. Processing audio...")
                            audio_processor.chunk_index += 1
                            await audio_processor.process_audio(audio_processor.chunk_index, audio_processor.audio_frames.copy(), True, self.callback)
                            silence_start = None
                            audio_processor.audio_frames = []
                            return
                    else:
                        silence_start = None
            except IOError as e:
                if e.errno == -9981:
                    audio_processor.log("Buffer overflow. Dropping frames.")
                    continue
                else:
                    raise