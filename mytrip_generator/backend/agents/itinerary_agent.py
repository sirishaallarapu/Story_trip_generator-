from ..agents.itinerary_builder import build_itinerary
from ..agents.vibe_matcher import get_trip_vibe
from ..agents.mood_intent_analyzer import analyze_mood_intent

def generate_full_itinerary(data):
    mood_intent = analyze_mood_intent(data['trip_type'], data['trip_type'])
    vibe = get_trip_vibe(data)
    itinerary = build_itinerary(data)
    return {"itinerary": itinerary, "vibe": f"{vibe} - {mood_intent['vibe_description']}"}