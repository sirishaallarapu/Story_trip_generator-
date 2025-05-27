import logging
import json
import re
from openai import OpenAI
from time import sleep

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI(timeout=60.0)

class StayActivityRecommender:
    def recommend(self, destination: str, daily_budget: float, intent: str) -> dict:
        logger.info(f"Generating recommendations for destination: {destination}, intent: {intent}")
        accommodation_budget = daily_budget * 0.5  # ₹5000
        activity_budget = daily_budget * 0.25  # ₹2500
        is_maldives = "Maldives" in destination
        destination_prompt = (
            f"{destination} (specify an island, e.g., Maafushi, Hulhumalé, or Aadaran)"
            if is_maldives else destination
        )
        activity_type = "thrilling adventure activity (e.g., jet skiing, shark diving)" if "adventure" in intent.lower() else "relaxing beach activity (e.g., spa session, sunset yoga)"
        prompt = f"""
        Generate recommendations for a stay and an {activity_type} in {destination_prompt} that align with the intent '{intent}'.
        Budget: Accommodation at {accommodation_budget:.2f} INR/night, Activity up to {activity_budget:.2f} INR.
        Restrictions: Vegetarian-friendly options only (no seafood or meat).
        Return a JSON object with:
        - stay: Specific accommodation (name, description, ₹5000/night, island if Maldives, booking URL)
        - activity: Specific activity (name, description, cost up to ₹2500, island if Maldives, booking URL)
        Example:
        ```json
        {{
            "stay": "Kaani Grand Seaview on Maafushi, beachfront, ₹{accommodation_budget:.2f}/night. Book at www.kaanihotels.com.",
            "activity": "Jet skiing at Bikini Beach, Maafushi, ₹{activity_budget:.2f}. Book at www.maldivesadventures.com."
        }}
        ```
        Return valid JSON only.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                raw_response = response.choices[0].message.content
                logger.info(f"Raw OpenAI response: {raw_response}")
                cleaned_response = re.sub(r'^```json\n|\n```$', '', raw_response).strip()
                
                try:
                    data = json.loads(cleaned_response)
                    return {
                        "stay": data.get("stay", "Not available"),
                        "activity": data.get("activity", "Not available")
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response (attempt {attempt+1}): {cleaned_response}")
                    if attempt == max_retries - 1:
                        return {"stay": "Not available", "activity": "Not available"}
            except Exception as e:
                logger.error(f"OpenAI API error (attempt {attempt+1}): {str(e)}")
                if attempt == max_retries - 1:
                    return {"stay": "Not available", "activity": "Not available"}
                sleep(2 ** attempt)