import logging
import json
import re
from openai import OpenAI
from time import sleep

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI(timeout=60.0)

def analyze_mood_intent(mood: str, intent: str) -> dict:
    logger.info(f"Analyzing mood: {mood}, intent: {intent}")
    vibe_description = (
        "An adrenaline-pumping escape with thrilling activities, vibrant energy, and scenic landscapes, perfect for adventure seekers."
        if "adventure" in intent.lower() else
        "A serene escape with gentle waves, warm sun, and tranquil beaches, perfect for unwinding."
    )
    return {"vibe_description": vibe_description}