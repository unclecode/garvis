# Constants
import os

def get_system_message(assistant_name:str = "Garvis"):
    return f"You are a helpful assistant built on top of Groq technology. Groq is a startup building new chips called LPU to be used instead of GPUs, and they are crazy fast. So whenever I say 'grok' or 'groq', I am referring to the same thing. Always reply very short, concise, and to the point. Your name is {assistant_name}. Don't start every message with 'Garvis is here'."

DEFAULT_ASSISTANT_NAME = "Garvis"
DEFAULT_TRANSCRIPTOR = "groq"

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = 'eBbWyvt9h7JOW9HmCqZx'
MODEL_ID = 'eleven_turbo_v2'
WEBSOCKET_URI = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input?model_id={MODEL_ID}"

# THRESHOLD_SILENCE = 1  # seconds of silence to detect end of speech
THRESHOLD_SILENCE = 0.5 # seconds of silence to detect end of speech
FRAME_DURATION_MS = 30  # duration of each audio frame in milliseconds
SAMPLE_RATE = 16000  # sample rate in Hz
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # frame size in samples
SPEECH_THRESHOLD = 500  # amplitude threshold for speech detection
MIN_AUDIO_LENGTH = 0.3  # minimum audio length in seconds
RECORD_DURATION = 5  # duration of each audio recording in seconds
