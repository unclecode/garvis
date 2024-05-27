import subprocess
import importlib.util
import inspect
import os
from pathlib import Path
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from io import BytesIO
import aiohttp
from aiohttp import MultipartWriter
import asyncio
import sys
import tty
import termios
import shutil 
import sys
import threading
from dotenv import load_dotenv
load_dotenv()

lock = threading.Lock()

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
def get_listening_strategies(file_path='listening_strategy.py'):
    strategies = []

    # Load the module
    spec = importlib.util.spec_from_file_location("listening_strategy", Path(__location__, file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Iterate through the members of the module
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            strategies.append(name)
    
    return strategies

def create_instance(class_name, file_path='listening_strategy.py'):
    # Load the module
    spec = importlib.util.spec_from_file_location("listening_strategy", Path(__location__, file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get the class from the module
    cls = getattr(module, class_name)
    
    # Create an instance of the class
    instance = cls()
    return instance

def xprint(*args, style="normal", color=None, end='\n', pre = "", post = "\r", **kwargs):
    """
    Custom print function that supports style (bold, dim, or normal), color, and all standard print arguments.
    """
    with lock:
        message = " ".join(map(str, args))
        
        # Define color codes
        color_codes = {
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "reset": "\033[0m"
        }
        
        # Apply style and color
        if style == "bold":
            message = f"\033[1m{message}\033[0m"
        elif style == "dim":
            message = f"\033[2m{message}\033[0m"
        if color in color_codes:
            message = f"{color_codes[color]}{message}{color_codes['reset']}"
        
        if end == "\n":
            pre and sys.stdout.write(pre)
            print(f"\r{message:<0}", end=end, **kwargs)
            post and sys.stdout.write(post)
        elif end == "":
            pre and sys.stdout.write(pre)
            print(message, end=end, flush=True, **kwargs)
        
        sys.stdout.flush()
        
async def get_keypress():
    loop = asyncio.get_event_loop()
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    def read_keypress():
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return await loop.run_in_executor(None, read_keypress)

def get_keypress_sync():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def call_transcribe_stream(audio_bytes: BytesIO, initial_prompt: str = ""):
    url = os.environ.get("COLAB_URL", None)
    if not url:
        raise ValueError("COLAB_URL environment variable is not set.")
    url = url + "transcribe_stream"
    m = MultipartEncoder(
        fields={
            'audio': ('audio.wav', audio_bytes, 'audio/wav'),
            'initial_prompt': initial_prompt
        }
    )
    response = requests.post(url, data=m, headers={'Content-Type': m.content_type}, stream=True)
    
    for line in response.iter_lines():
        if line:
            yield line.decode('utf-8')

def call_transcribe(audio_bytes: BytesIO, initial_prompt: str = ""):
    url = os.environ.get("COLAB_URL", None)
    if not url:
        raise ValueError("COLAB_URL environment variable is not set.")
    url = url + "transcribe"
    
    m = MultipartEncoder(
        fields={
            'audio': ('audio.wav', audio_bytes, 'audio/wav'),
            'initial_prompt': initial_prompt
        }
    )
    response = requests.post(url, data=m, headers={'Content-Type': m.content_type})
    
    return response.json()

async def acall_transcribe_stream(audio_bytes: BytesIO, initial_prompt: str = ""):
    url = os.environ.get("COLAB_URL", None)
    if not url:
        raise ValueError("COLAB_URL environment variable is not set.")
    url = url + "transcribe_stream"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={
            'audio': ('audio.wav', audio_bytes, 'audio/wav'),
            'initial_prompt': initial_prompt
        }) as response:
            async for line in response.content:
                if line:
                    yield line.decode('utf-8')

async def acall_transcribe(audio_bytes: BytesIO, initial_prompt: str = ""):
    url = os.environ.get("COLAB_URL", None)
    if not url:
        raise ValueError("COLAB_URL environment variable is not set.")
    url = url + "transcribe"
    async with aiohttp.ClientSession() as session:
        with MultipartWriter('form-data') as mpwriter:
            part = mpwriter.append(audio_bytes)
            part.set_content_disposition('form-data', name='audio', filename='audio.wav')
            part.headers[aiohttp.hdrs.CONTENT_TYPE] = 'audio/wav'
            if initial_prompt:
                part = mpwriter.append(initial_prompt)
                part.set_content_disposition('form-data', name='initial_prompt')

            async with session.post(url, data=mpwriter) as response:
                return await response.json()

async def websocker_text_iterator(chunks):
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", " ")
    buffer = ""

    async for text in chunks:
        if text:
            if buffer.endswith(splitters):
                yield buffer + " "
                buffer = text
            elif text.startswith(splitters):
                yield buffer + text[0] + " "
                buffer = text[1:]
            else:
                buffer += text

    if buffer:
        yield buffer + " "
        
def is_installed(lib_name):
    return shutil.which(lib_name) is not None

def create_mpv_process():
    if not is_installed("mpv"):
        raise ValueError(
            "mpv not found, necessary to stream audio. "
            "Install instructions: https://mpv.io/installation/"
        )

    mpv_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )    
    
    return mpv_process