from semantic_router import Route
import os
from semantic_router.encoders import OpenAIEncoder
from semantic_router.layer import RouteLayer

# Define the semantic routes for detecting stop commands
encoder = OpenAIEncoder()
jarvis_stop = Route(
    name="jarvis-stop",
    utterances=[
        "jarvis, listen to me",
        "stop please",
        "No need to talk about that",
        "jarvis stop",
        "jarvis, stop",
        "stop now",
        "please stop",
        "jarvis, I need you to stop",
        "stop it now",
        "jarvis stop talking",
        "I need you to stop now",
        "can you stop",
        "jarvis stop please"
    ],
)
jarvis_stop_implicit = Route(
    name="jarvis-stop-implicit",
    utterances=[
        "jarvis, can you hear me?",
        "jarvis, I have something to say",
        "jarvis, wait a moment",
        "jarvis, hold on",
        "jarvis, listen to me",
        "jarvis, I need to talk",
        "jarvis, I have a question",
        "jarvis, let me speak",
        "jarvis, give me a moment",
        "jarvis, pause for a second",
        "jarvis, I need your attention",
        "jarvis, please listen",
        "jarvis, can we talk?",
        "jarvis, let me interrupt",
        "jarvis, allow me to talk",
        "jarvis, can I say something?",
        "jarvis, I need to say something",
        "jarvis, hold on a second",
        "jarvis, I want to say something"
    ],
)
jarvis_stop_without_name = Route(
    name="jarvis-stop-without-name",
    utterances=[
        "can you hear me?",
        "I have something to say",
        "wait a moment",
        "hold on",
        "listen to me",
        "I need to talk",
        "I have a question",
        "let me speak",
        "give me a moment",
        "pause for a second",
        "I need your attention",
        "please listen",
        "let me interrupt",
        "allow me to talk",
        "can I say something?",
        "I need to say something",
        "hold on a second",
        "I want to say something"
    ],
    score_threshold=0.9
)

# Create a combined list of routes
routes = [jarvis_stop, jarvis_stop_implicit, jarvis_stop_without_name]
rl = RouteLayer(encoder=encoder, routes=routes)

def is_call_jarvis(text):
    route = rl(text)
    return route.name in ["jarvis-stop", "jarvis-stop-implicit", "jarvis-stop-without-name"]

# Define the route for detecting the end of conversation
user_endings = Route(
    name="user_endings",
    utterances=[
        "I've been thinking about this for a while, what do you think?",
        "That's all I wanted to ask, can you help with that?",
        "I've explained my situation, is that correct?",
        "Do you have any suggestions on what I should do?",
        "I didn't quite get that, could you explain it a bit more?",
        "Any advice you can offer would be great, thanks.",
        "What's your opinion on this matter?",
        "Is there more information you can provide on this topic?",
        "Based on what I've told you, how should I proceed?",
        "That's everything I need to know for now, what should I do next?"
        "That's everything I need to know for now, right?"
    ],
    # score_threshold=0.8
)

# Place the route in a list
user_endings_routes = [user_endings]
# Initialize the encoder and route layer
user_endings_encoder = OpenAIEncoder()
user_endings_rl = RouteLayer(encoder=user_endings_encoder, routes=user_endings_routes)

# Function to detect if the user has ended their conversation
def detect_end_of_conversation(transcribed_text):
    route_name = user_endings_rl(transcribed_text).name
    return route_name == "user_endings"
