import logging
import re
from openai import OpenAI
import json
from time import sleep

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ItineraryBuilder:
    def __init__(self):
        self.client = OpenAI(timeout=20.0)

    def parse_text_itinerary(self, text):
        itinerary = []
        lines = text.split("\n")
        current_day = None
        current_destination = None
        current_description = ""
        current_activities = []
        current_transport = ""
        current_tip = ""
        current_budget = {"accommodation": 0, "food": 0, "activities": 0, "transport": 0}

        day_pattern = re.compile(r"Day (\d+): (.+)", re.IGNORECASE)
        budget_pattern = re.compile(r"Budget: Accommodation ₹([\d.]+), Food ₹([\d.]+), Activities ₹([\d.]+), Transport ₹([\d.]+)", re.IGNORECASE)
        activity_pattern = re.compile(r"^- (.+)", re.IGNORECASE)
        transport_pattern = re.compile(r"Transport: (.+)", re.IGNORECASE)
        tip_pattern = re.compile(r"Tip: (.+)", re.IGNORECASE)
        description_pattern = re.compile(r"Description: (.+)", re.IGNORECASE)

        for line in lines:
            line = line.strip()
            if not line:
                continue

            day_match = day_pattern.match(line)
            if day_match:
                if current_day is not None:
                    itinerary.append({
                        "day": current_day,
                        "destination": current_destination or "Unknown",
                        "description": current_description or "No description provided",
                        "activities": current_activities or ["No activities listed"],
                        "transport": current_transport or "No transport specified",
                        "tip": current_tip or "No tip provided",
                        "daily_budget": current_budget
                    })
                current_day = int(day_match.group(1))
                current_destination = day_match.group(2).strip()
                current_description = ""
                current_activities = []
                current_transport = ""
                current_tip = ""
                current_budget = {"accommodation": 0, "food": 0, "activities": 0, "transport": 0}
                continue

            description_match = description_pattern.match(line)
            if description_match:
                current_description = description_match.group(1).strip()
                continue

            activity_match = activity_pattern.match(line)
            if activity_match:
                current_activities.append(activity_match.group(1).strip())
                continue

            transport_match = transport_pattern.match(line)
            if transport_match:
                current_transport = transport_match.group(1).strip()
                continue

            tip_match = tip_pattern.match(line)
            if tip_match:
                current_tip = tip_match.group(1).strip()
                continue

            budget_match = budget_pattern.match(line)
            if budget_match:
                try:
                    current_budget = {
                        "accommodation": float(budget_match.group(1)),
                        "food": float(budget_match.group(2)),
                        "activities": float(budget_match.group(3)),
                        "transport": float(budget_match.group(4))
                    }
                except ValueError as e:
                    logger.warning(f"Invalid budget format in line: {line}, error: {str(e)}")
                continue

        if current_day is not None:
            itinerary.append({
                "day": current_day,
                "destination": current_destination or "Unknown",
                "description": current_description or "No description provided",
                "activities": current_activities or ["No activities listed"],
                "transport": current_transport or "No transport specified",
                "tip": current_tip or "No tip provided",
                "daily_budget": current_budget
            })

        text_itinerary = text.strip() or "No itinerary text provided"
        logger.info(f"Parsed itinerary: {len(itinerary)} days")
        return itinerary, text_itinerary

    def build_itinerary(self, destinations, trip_duration, budget, restrictions, mood, intent):
        logger.info(f"Building itinerary for destination: {destinations[0]}")
        daily_budget_cap = budget / trip_duration
        is_maldives = "Maldives" in destinations[0]
        is_goa = "Goa" in destinations[0]
        destination_prompt = (
            f"{destinations[0]} (specify a location, e.g., Anjuna, Vagator, Calangute)"
            if is_goa else
            f"{destinations[0]} (specify an island, e.g., Maafushi, Hulhumalé, Aadaran)"
            if is_maldives else destinations[0]
        )
        activity_type = (
            "thrilling adventure activities (e.g., jet skiing at Bikini Beach, Maafushi; paragliding at Anjuna Cliff)"
            if mood == "adventure" else
            "relaxing beach activities (e.g., spa at Adaaran Prestige Vadoo, yoga at Vagator Beach)"
        )
        vibe_description = (
            "An adrenaline-pumping escape with thrilling activities and vibrant energy."
            if mood == "adventure" else
            "A serene escape with tranquil beaches."
        )
        prompt = f"""
        Create a JSON response for a {trip_duration}-day travel itinerary for {destination_prompt}.
        Budget: {budget} INR (daily cap {daily_budget_cap:.2f} INR, accommodation ₹5000/day).
        Restrictions: {restrictions or 'None'} (vegetarian meals only).
        Intent: {intent} ({activity_type}).
        Requirements:
        - Exact locations (e.g., Maafushi, Anjuna).
        - 3-4 activities/day with details (e.g., 'Paragliding at Anjuna Cliff, 15-min').
        - Descriptions: 50-80 words, matching intent.
        - Transport, budget breakdown, practical tip.
        - Budget summary (total spent, remaining).
        Return JSON with:
        - itinerary: Array (day, destination, description, activities, transport, tip, daily_budget)
        - text_itinerary: String summary
        - vibe_description: String ({vibe_description})
        - recommendations: Array (stay, activity)
        Example:
        ```json
        {{
            "itinerary": [
                {{
                    "day": 1,
                    "destination": "Anjuna, Goa",
                    "description": "Kick off with paragliding over Anjuna Cliff.",
                    "activities": ["Check-in at Anjuna Beach Resort", "Paragliding at Anjuna Cliff, 15-min", "Vegetarian dinner at Artjuna Café"],
                    "transport": "Taxi from airport",
                    "tip": "Book paragliding early",
                    "daily_budget": {{"accommodation": 5000, "food": 2000, "activities": 2500, "transport": 1000}}
                }}
            ],
            "text_itinerary": "Day 1: Anjuna adventure. Total Spent: ₹10500, Remaining: ₹39500",
            "vibe_description": "{vibe_description}",
            "recommendations": [
                {{"stay": "Anjuna Beach Resort, ₹5000/night", "activity": "Paragliding at Anjuna Cliff, ₹2500"}}
            ]
        }}
        ```
        Return valid JSON only.
        """
        max_retries = 1
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Switched to gpt-3.5-turbo
                    messages=[
                        {"role": "system", "content": "Return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800,
                    timeout=10.0
                )
                raw_response = response.choices[0].message.content
                logger.debug(f"Raw OpenAI response: {raw_response[:200]}...")

                try:
                    data = json.loads(raw_response)
                    itinerary = data.get("itinerary", [])
                    text_itinerary = data.get("text_itinerary", "No itinerary text provided")
                    vibe_description = data.get("vibe_description", vibe_description)
                    recommendations = data.get("recommendations", [])

                    total_spent = 0
                    for day in itinerary:
                        daily_budget = day.get("daily_budget", {})
                        daily_total = sum(daily_budget.get(key, 0) for key in ["accommodation", "food", "activities", "transport"])
                        if daily_total > daily_budget_cap or daily_budget.get("accommodation", 0) != 5000:
                            logger.warning(f"Day {day['day']} budget {daily_total} invalid")
                            daily_budget["accommodation"] = 5000
                            scale = (daily_budget_cap - 5000) / max(daily_total - daily_budget.get("accommodation", 0), 1)
                            daily_budget["food"] = round(2000 * scale, 2)
                            daily_budget["activities"] = round(2500 * scale, 2)
                            daily_budget["transport"] = round(1000 * scale, 2)
                        total_spent += sum(daily_budget.values())

                    budget_status = f"Total Spent: ₹{total_spent:.2f}, "
                    if total_spent <= budget:
                        budget_status += f"Remaining: ₹{budget - total_spent:.2f}"
                    else:
                        budget_status += f"Exceeded by: ₹{total_spent - budget:.2f}"
                    text_itinerary += f" {budget_status}"
                    data["text_itinerary"] = text_itinerary
                    data["budget_summary"] = {
                        "total_spent": total_spent,
                        "remaining": max(0, budget - total_spent),
                        "exceeded": max(0, total_spent - budget)
                    }

                    return itinerary, text_itinerary, vibe_description, recommendations
                except json.JSONDecodeError as e:
                    logger.warning(f"Response not JSON: {str(e)}. Raw: {raw_response[:200]}...")
                    itinerary, text_itinerary = self.parse_text_itinerary(raw_response)
                    if not itinerary:
                        logger.error("Text parsing failed, using fallback")
                        itinerary = [{
                            "day": 1,
                            "destination": destinations[0],
                            "description": f"Begin your {intent.lower()} in {destinations[0]}.",
                            "activities": ["Check-in at budget hotel", "Adventure activity", "Vegetarian dinner"],
                            "transport": "Local transport",
                            "tip": "Plan activities early",
                            "daily_budget": {"accommodation": 5000, "food": 2000, "activities": 1500, "transport": 1000}
                        }]
                        total_spent = sum(itinerary[0]["daily_budget"].values())
                        text_itinerary = f"Day 1: {destinations[0]}. Total Spent: ₹{total_spent}, Remaining: ₹{budget - total_spent}"
                    return itinerary, text_itinerary, vibe_description, []
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                itinerary = [{
                    "day": 1,
                    "destination": destinations[0],
                    "description": f"Begin your {intent.lower()} in {destinations[0]}.",
                    "activities": ["Check-in at budget hotel", "Adventure activity", "Vegetarian dinner"],
                    "transport": "Local transport",
                    "tip": "Plan activities early",
                    "daily_budget": {"accommodation": 5000, "food": 2000, "activities": 1500, "transport": 1000}
                }]
                total_spent = sum(itinerary[0]["daily_budget"].values())
                text_itinerary = f"Day 1: {destinations[0]}. Total Spent: ₹{total_spent}, Remaining: ₹{budget - total_spent}"
                return itinerary, text_itinerary, vibe_description, []