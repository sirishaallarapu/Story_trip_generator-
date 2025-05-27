from pydantic import BaseModel
from typing import List

class Budget(BaseModel):
    accommodation: float
    food: float
    activities: float
    transport: float

class ItineraryDay(BaseModel):
    day: int
    destination: str
    description: str
    activities: List[str]
    transport: str
    tip: str
    daily_budget: Budget

class ItineraryResponse(BaseModel):
    itinerary: List[ItineraryDay]
    text_itinerary: str