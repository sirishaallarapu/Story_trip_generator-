import logging
from agents.itinerary_builder import ItineraryBuilder
from tools.prompt_templates import extract_mood_intent_destinations
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

def test_full_pipeline():
    prompt = "relaxing beach holiday with yoga and nature for 2 days in Goa"
    request = {
        "prompt": prompt,
        "budget": 20000,
        "travel_dates": "2025-05-27 to 2025-05-28",
        "restrictions": "vegetarian meals only",
        "trip_duration": 2,
        "currency": "INR"
    }

    try:
        # Mood/intent extraction
        mood_intent, destinations = extract_mood_intent_destinations(request["prompt"])
        mood, intent = mood_intent.get("mood", "neutral"), mood_intent.get("intent", "explore")
        logger.info(f"Mood: {mood}, Intent: {intent}, Destinations: {destinations}")

        # Itinerary generation
        builder = ItineraryBuilder()
        structured_itinerary, text_itinerary = builder.build_itinerary(
            destinations=destinations or ["Goa, India"],
            trip_duration=request["trip_duration"],
            budget=request["budget"],
            travel_dates=request["travel_dates"],
            restrictions=request["restrictions"],
            mood=mood,
            intent=intent
        )
        logger.info(f"Structured itinerary: {structured_itinerary}")
        logger.info(f"Text itinerary: {text_itinerary[:200]}...")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_full_pipeline()