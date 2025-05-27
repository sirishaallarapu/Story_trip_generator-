import logging
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()

def test_mood_intent():
    prompt = "relaxing beach holiday with yoga and nature for 2 days in Goa"
    prompt_text = f"""
    Analyze the prompt: "{prompt}"
    Return JSON with mood, intent, destinations.
    Example: {{"mood": "relaxing", "intent": "beach holiday", "destinations": ["Goa, India"]}}
    Return valid JSON only.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Respond with valid JSON only."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        logger.info(f"Mood/intent response: {response.choices[0].message.content}")
    except Exception as e:
        logger.error(f"Mood/intent error: {str(e)}")

def test_itinerary():
    prompt = """
    Create a 2-day travel itinerary for Goa, India.
    Budget: 20000 INR
    Dates: 2025-05-27 to 2025-05-28
    Restrictions: vegetarian meals only
    Mood: relaxing
    Intent: beach holiday
    Return JSON with itinerary and text_itinerary.
    Example: {{"itinerary": [{"day": 1, "destination": "Goa, India", "description": "Relax", "activities": ["Yoga"], "transport": "Taxi", "tip": "Book early", "daily_budget": {"accommodation": 5000, "food": 1500, "activities": 1000, "transport": 500}}], "text_itinerary": "Day 1: Goa..."}}
    Return valid JSON only.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        logger.info(f"Itinerary response: {response.choices[0].message.content}")
    except Exception as e:
        logger.error(f"Itinerary error: {str(e)}")

if __name__ == "__main__":
    test_mood_intent()
    test_itinerary()