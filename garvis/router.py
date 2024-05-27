from semantic_router import Route
import os
from semantic_router.encoders import OpenAIEncoder
from semantic_router.layer import RouteLayer

# Define the semantic routes for detecting stop commands
encoder = OpenAIEncoder()
garvis_stop = Route(
    name="garvis-stop",
    utterances=[
        "garvis, listen to me",
        "stop please",
        "No need to talk about that",
        "garvis stop",
        "garvis, stop",
        "stop now",
        "please stop",
        "garvis, I need you to stop",
        "stop it now",
        "garvis stop talking",
        "I need you to stop now",
        "can you stop",
        "garvis stop please"
    ],
)
garvis_stop_implicit = Route(
    name="garvis-stop-implicit",
    utterances=[
        "garvis, can you hear me?",
        "garvis, I have something to say",
        "garvis, wait a moment",
        "garvis, hold on",
        "garvis, listen to me",
        "garvis, I need to talk",
        "garvis, I have a question",
        "garvis, let me speak",
        "garvis, give me a moment",
        "garvis, pause for a second",
        "garvis, I need your attention",
        "garvis, please listen",
        "garvis, can we talk?",
        "garvis, let me interrupt",
        "garvis, allow me to talk",
        "garvis, can I say something?",
        "garvis, I need to say something",
        "garvis, hold on a second",
        "garvis, I want to say something"
    ],
)
garvis_stop_without_name = Route(
    name="garvis-stop-without-name",
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
routes = [garvis_stop, garvis_stop_implicit, garvis_stop_without_name]
rl = RouteLayer(encoder=encoder, routes=routes)

def is_call_garvis(text):
    route = rl(text)
    return route.name in ["garvis-stop", "garvis-stop-implicit", "garvis-stop-without-name"]

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
