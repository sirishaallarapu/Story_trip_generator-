import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI(timeout=60.0)

def analyze_mood_intent(trip_type: str, intent: str) -> dict:
    logger.info(f"Analyzing trip_type: {trip_type}, intent: {intent}")
    vibe_description = (
        "An adrenaline-pumping escape with thrilling activities, vibrant energy, and scenic landscapes, perfect for adventure seekers."
        if "adventure" in trip_type.lower() else
        "A serene escape with gentle waves, warm sun, and tranquil beaches, perfect for unwinding."
        if "beach" in trip_type.lower() else
        "A romantic getaway with intimate moments and charming settings."
        if "romantic" in trip_type.lower() else
        "An immersive journey through history and traditions, perfect for cultural enthusiasts."
        if "cultural" in trip_type.lower() else
        "A relaxing and leisurely exploration."
    )
    return {"vibe_description": vibe_description}