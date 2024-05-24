# Constants
import os

def get_system_message(assistant_name:str = "Jarvis"):
    return f"You are a helpful assistant.You are built on top of Groq tecnology. Groq is a startup building new chips called LPU to be used instead of GPU and that is xrazy fast. So whever I said 'grok' or 'groq' I am referring to the same thing. Always reply very short, concise, and to the point. Your name is {assistant_name}."

DEFAULT_ASSISTANT_NAME = "Jarvis"
DEFAULT_TRANSCRIPTOR = "groq"

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = 'oVYLyfQLNQCZVeuCq7oQ'
VOICE_ID = '21m00Tcm4TlvDq8ikWAM'
VOICE_ID = 'eBbWyvt9h7JOW9HmCqZx'
MODEL_ID = 'eleven_turbo_v2'
WEBSOCKET_URI = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input?model_id={MODEL_ID}"

# THRESHOLD_SILENCE = 1  # seconds of silence to detect end of speech
THRESHOLD_SILENCE = 0.5 # seconds of silence to detect end of speech
FRAME_DURATION_MS = 30  # duration of each audio frame in milliseconds
SAMPLE_RATE = 16000  # sample rate in Hz
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # frame size in samples
SPEECH_THRESHOLD = 500  # amplitude threshold for speech detection
MIN_AUDIO_LENGTH = 2  # minimum audio length in seconds
RECORD_DURATION = 5  # duration of each audio recording in seconds
