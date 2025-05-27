import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from agents.itinerary_builder import ItineraryBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ItineraryRequest(BaseModel):
    destinations: List[str] = Field(..., min_items=1)
    trip_duration: int = Field(..., ge=1)
    budget: float = Field(..., gt=0)
    restrictions: Optional[str] = None
    mood: Optional[str] = "neutral"
    intent: Optional[str] = "explore"
    recommendations: Optional[List[str]] = None

def handle_itinerary_request(data: dict):
    try:
        request = ItineraryRequest(**data)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return {"detail": f"Invalid request data: {str(e)}"}

    builder = ItineraryBuilder()
    try:
        itinerary, text_itinerary, vibe_description, recommendations = builder.build_itinerary(
            destinations=request.destinations,
            trip_duration=request.trip_duration,
            budget=request.budget,
            restrictions=request.restrictions,
            mood=request.mood,
            intent=request.intent
        )
        budget_summary = {
            "total_spent": sum(sum(day["daily_budget"].values()) for day in itinerary),
            "remaining": max(0, request.budget - sum(sum(day["daily_budget"].values()) for day in itinerary)),
            "exceeded": max(0, sum(sum(day["daily_budget"].values()) for day in itinerary) - request.budget)
        }
        return {
            "itinerary": itinerary,
            "text_itinerary": text_itinerary,
            "vibe_description": vibe_description,
            "recommendations": recommendations,
            "budget_summary": budget_summary
        }
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        return {"detail": f"Failed to generate itinerary: {str(e)}"}