from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import uuid
from agents.itinerary_builder import ItineraryBuilder
from agents.vibe_matcher import VibeMatcher
from agents.mood_intent_analyzer import analyze_mood_intent
from agents.stay_activity_recommender import StayActivityRecommender
from tools.prompt_templates import extract_mood_intent_destinations
from database.db_utils import store_itinerary

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

class ItineraryRequest(BaseModel):
    prompt: str
    budget: float
    restrictions: Optional[str] = None
    trip_duration: int

class ItineraryResponse(BaseModel):
    itinerary: list
    text_itinerary: str
    vibe_description: str
    recommendations: list
    budget_summary: dict

@router.post("/api/generate-itinerary")
async def generate_itinerary(request: ItineraryRequest):
    try:
        mood_intent, destinations = extract_mood_intent_destinations(request.prompt)
        mood = "adventure" if "adventure" in request.prompt.lower() else mood_intent.get("mood", "relaxation")
        intent = request.prompt
        logger.info(f"Extracted mood: {mood}, intent: {intent}, destinations: {destinations}")

        itinerary_builder = ItineraryBuilder()
        vibe_matcher = VibeMatcher()
        recommender = StayActivityRecommender()

        final_destinations = destinations[:1] if destinations and destinations[0] not in ["South India", "Unknown"] else vibe_matcher.match(mood, intent, request.restrictions)
        if not final_destinations:
            final_destinations = ["Maafushi, Maldives" if "Maldives" in request.prompt.lower() else "Anjuna, Goa"]
        logger.info(f"Final destinations: {final_destinations}")

        itinerary, text_itinerary, vibe_description, recommendations = itinerary_builder.build_itinerary(
            destinations=final_destinations,
            trip_duration=request.trip_duration,
            budget=request.budget,
            restrictions=request.restrictions,
            mood=mood,
            intent=intent
        )

        if not itinerary:
            logger.warning("No itinerary generated, using fallback")
            itinerary = []
            for day in range(1, request.trip_duration + 1):
                itinerary.append({
                    "day": day,
                    "destination": final_destinations[0],
                    "description": f"Day {day}: Explore {final_destinations[0]} with adventure activities.",
                    "activities": [
                        f"Check-in at budget hotel (Day {day})",
                        "Adventure activity (to be planned)",
                        "Vegetarian dinner"
                    ],
                    "transport": "Local transport",
                    "tip": "Plan activities in advance",
                    "daily_budget": {"accommodation": 5000, "food": 2000, "activities": 1500, "transport": 1000}
                })
            total_spent = sum(sum(day["daily_budget"].values()) for day in itinerary)
            text_itinerary = f"Fallback itinerary for {request.trip_duration} days in {final_destinations[0]}. Total Spent: ₹{total_spent}, Remaining: ₹{request.budget - total_spent}"
            vibe_description = "A thrilling adventure awaits." if mood == "adventure" else "A serene escape."

        for day in itinerary:
            destination = day.get("destination", final_destinations[0])
            rec = recommender.recommend(destination, request.budget / request.trip_duration, intent)
            recommendations.append(rec)

        budget_summary = {
            "total_spent": sum(sum(day["daily_budget"].values()) for day in itinerary),
            "remaining": max(0, request.budget - sum(sum(day["daily_budget"].values()) for day in itinerary)),
            "exceeded": max(0, sum(sum(day["daily_budget"].values()) for day in itinerary) - request.budget)
        }

        itinerary_key = str(uuid.uuid4())
        itinerary_data = {
            "itinerary": itinerary,
            "text_itinerary": text_itinerary,
            "vibe_description": vibe_description,
            "recommendations": recommendations,
            "budget_summary": budget_summary
        }
        store_itinerary(itinerary_key, itinerary_data)

        return ItineraryResponse(
            itinerary=itinerary,
            text_itinerary=text_itinerary,
            vibe_description=vibe_description,
            recommendations=recommendations,
            budget_summary=budget_summary
        )
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        itinerary = []
        for day in range(1, request.trip_duration + 1):
            itinerary.append({
                "day": day,
                "destination": "Anjuna, Goa" if "Goa" in request.prompt.lower() else "Maafushi, Maldives",
                "description": f"Day {day}: Begin your trip.",
                "activities": ["Check-in at budget hotel", "Explore local area", "Vegetarian dinner"],
                "transport": "Local transport",
                "tip": "Carry cash for vendors",
                "daily_budget": {"accommodation": 5000, "food": 2000, "activities": 1500, "transport": 1000}
            })
        total_spent = sum(sum(day["daily_budget"].values()) for day in itinerary)
        text_itinerary = f"Fallback itinerary for {request.trip_duration} days. Total Spent: ₹{total_spent}, Remaining: ₹{request.budget - total_spent}"
        vibe_description = "A thrilling adventure awaits." if "adventure" in request.prompt.lower() else "A serene escape."
        budget_summary = {
            "total_spent": total_spent,
            "remaining": request.budget - total_spent,
            "exceeded": 0
        }
        return ItineraryResponse(
            itinerary=itinerary,
            text_itinerary=text_itinerary,
            vibe_description=vibe_description,
            recommendations=[],
            budget_summary=budget_summary
        )