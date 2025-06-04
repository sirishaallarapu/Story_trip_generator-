from datetime import datetime
import math

def get_itinerary_prompt(data, vibe, effective_trip_type, valid, activity_examples, meal_examples, budget_description, rooms_needed, extracted_data):
    destination = extracted_data.get("destinations", [data.get("destination", "").capitalize()])[0]
    trip_type = data.get("trip_type", "generic").lower()
    num_members = data.get("num_members", 1)
    food_preference = data.get("food_preference", "veg").lower()
    
    start_date = (
        data["start_date"]
        if isinstance(data["start_date"], datetime)
        else datetime.fromisoformat(data["start_date"].replace("Z", "+00:00"))
    )
    end_date = (
        data["end_date"]
        if isinstance(data["end_date"], datetime)
        else datetime.fromisoformat(data["end_date"].replace("Z", "+00:00"))
    )
    formatted_start = start_date.strftime("%B %d, %Y")
    formatted_end = end_date.strftime("%B %d, %Y")
    
    duration = data.get("duration") or (end_date - start_date).days + 1
    
    note = (
        f"\nNote: Since the requested {trip_type} trip is not available for {destination}, a generic itinerary is provided.\n"
        if not valid
        else ""
    )
    
    hotel_example = (
        "Courtyard by Marriott Ahmedabad" if destination.lower() == "gujarat" else
        "The Leela Goa" if destination.lower() == "goa" else
        "Comfortable Hotel"
    )
    hotel_slug = (
        "courtyard-by-marriott-ahmedabad" if destination.lower() == "gujarat" else
        "the-leela-goa" if destination.lower() == "goa" else
        "comfortable-hotel"
    )
    country_code = (
        "in" if destination.lower() in ["gujarat", "goa", "andaman", "hyderabad"] else
        "id" if destination.lower() == "bali" else
        "th" if destination.lower() == "thailand" else
        "au" if destination.lower() == "australia" else
        "mv"
    )
    airport_example = (
        "Sardar Vallabhbhai Patel International Airport" if destination.lower() == "gujarat" else
        "Goa International Airport" if destination.lower() == "goa" else
        f"{destination} Airport"
    )
    
    prompt = f"""
You are a professional travel planner specializing in accurate and detailed itineraries.

Plan a realistic, engaging, and structured {effective_trip_type} itinerary for {num_members} person(s) traveling to {destination}.
Dates: {formatted_start} to {formatted_end} ({duration} days exactly)
Budget: {budget_description}
Food Preference: {meal_examples}
Number of Rooms: {rooms_needed} (1 room for 1-2 people)
Mood: {extracted_data.get('mood', 'cultural')}
Intent: {extracted_data.get('intent', 'cultural exploration')}

Instructions:
1. Start the itinerary with "Your Trip Itinerary" followed by the vibe: "{vibe}".
2. Structure EXACTLY {duration} days, with each day starting with "Day X - <Date>: <Title>" (e.g., "Day 1 - {formatted_start}: Cultural Exploration Begins in {destination}"). Use "-" (hyphen) in headers.
3. Each day (except departure day) includes:
   - Transport: Specific mode (e.g., private car for medium-budget in {destination}) with cost for all {num_members} person(s) in ₹ (Indian Rupees).
   - Accommodation: {'5-star hotel' if data.get('budget', '').lower() == 'high' else 'comfortable hotel'} in {destination} (e.g., {hotel_example}) with price for {rooms_needed} room(s) in ₹ and a valid Booking.com link (e.g., Book Now: https://www.booking.com/hotel/{country_code}/{hotel_slug}.html).
   - Activities: EXACTLY THREE {effective_trip_type} activities (Morning, Afternoon, Evening) with costs per person in ₹. Use ONLY: {activity_examples[effective_trip_type]}. For Gujarat, prioritize Sabarmati Ashram visit, textile museum tour, or Jain temple visit.
   - Meals: EXACTLY THREE {food_preference} meals (Breakfast, Lunch, Dinner) with costs per person in ₹, reflecting {destination} cuisine (e.g., Gujarati thali for veg in Gujarat).
   - Total Cost: Placeholder (e.g., Total Cost: ₹0).
4. Departure day (Day {duration}) includes ONLY:
   - Transport: Specific mode to {airport_example} with cost for all {num_members} person(s) in ₹.
   - Meals: Breakfast ({food_preference}) with cost per person in ₹.
   - Total Cost: Placeholder (e.g., Total Cost: ₹0).
5. Output as plain text, no HTML/Markdown (e.g., Book Now: https://www.booking.com/..., not [Book Now](URL)).
6. Use Indian Rupees (₹) for all costs, formatted with commas (e.g., ₹15,000).
7. Include EXACTLY {duration - 1} valid Booking.com links for non-departure days, using real hotel names relevant to {destination}.
8. Ensure activities and meals are strictly relevant to {destination} and {effective_trip_type}.
9. Avoid terms like "sunset", "romantic", or irrelevant activities/meals (e.g., seafood for vegetarian).
10. Reflect the vibe "{vibe}", mood "{extracted_data.get('mood', 'cultural')}", and intent "{extracted_data.get('intent', 'cultural exploration')}" in the itinerary’s tone and activity choices.

{note}

Example for {effective_trip_type} trip in {destination}:
Your Trip Itinerary
{vibe}

Day 1 - {formatted_start}: Cultural Exploration Begins in {destination}
Transport: Private car from {airport_example} to hotel. Cost: ₹2,500 for {num_members}
Accommodation: {hotel_example} (1 room). Cost: ₹8,000 Book Now: https://www.booking.com/hotel/{country_code}/{hotel_slug}.html
Activities:
  - Morning: {'Sabarmati Ashram visit' if destination.lower() == 'gujarat' else 'Activity'}. Cost: ₹500 per person
  - Afternoon: {'Textile museum tour at Calico Museum' if destination.lower() == 'gujarat' else 'Activity'}. Cost: ₹1,000 per person
  - Evening: {'Jain temple visit at Hutheesing Temple' if destination.lower() == 'gujarat' else 'Activity'}. Cost: ₹300 per person
Meals:
  - Breakfast: {'Gujarati thali' if destination.lower() == 'gujarat' and food_preference == 'veg' else 'Local Dish'} at hotel. Cost: ₹800 per person
  - Lunch: {'Dhokla and fafda' if destination.lower() == 'gujarat' and food_preference == 'veg' else 'Local Dish'} at a local eatery. Cost: ₹600 per person
  - Dinner: {'Thepla and undhiyu' if destination.lower() == 'gujarat' and food_preference == 'veg' else 'Local Dish'} at a traditional restaurant. Cost: ₹1,200 per person
Total Cost: ₹0
...
Day {duration} - {formatted_end}: Departure from {destination}
Transport: Private car to {airport_example}. Cost: ₹2,500 for {num_members}
Meals:
  - Breakfast: {'Gujarati thepla' if destination.lower() == 'gujarat' and food_preference == 'veg' else 'Local Dish'} at hotel. Cost: ₹800 per person
Total Cost: ₹0
Total Estimated Trip Cost: ₹0
"""
    return prompt