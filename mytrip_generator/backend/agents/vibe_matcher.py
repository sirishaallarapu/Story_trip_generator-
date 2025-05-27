import logging
from openai import OpenAI
import json
from time import sleep

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class VibeMatcher:
    def __init__(self):
        self.client = OpenAI(timeout=60.0)

    def match(self, mood, intent, restrictions=None):
        logger.info(f"Matching vibe for mood: {mood}, intent: {intent}")
        vibe_type = "adrenaline-pumping with thrilling water sports and vibrant marine life" if "adventure" in intent.lower() else "serene with gentle waves, warm sun, and relaxing beach experiences"
        prompt = f"""
        Based on the intent '{intent}', suggest a destination for a trip that aligns with these preferences.
        Restrictions: {restrictions or 'None'} (e.g., vegetarian meals only).
        For Maldives, specify an island (e.g., Maafushi, Hulhumalé) and focus on a {vibe_type} vibe.
        Return a JSON object with:
        - destinations: Array of destination strings (e.g., 'Maafushi, Maldives')
        - vibe_description: String (50-100 words, matching intent)
        Example:
        ```json
        {{
            "destinations": ["Maafushi, Maldives"],
            "vibe_description": "An adrenaline-pumping escape with thrilling water sports and vibrant marine life, perfect for adventure seekers."
        }}
        ```
        Return valid JSON only.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
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
                logger.info(f"Raw OpenAI response: {raw_response[:200]}...")
                data = json.loads(raw_response)
                destinations = data.get("destinations", ["Goa, India"])
                return destinations
            except Exception as e:
                logger.error(f"OpenAI API error (attempt {attempt+1}): {str(e)}")
                if attempt == max_retries - 1:
                    return ["Goa, India"]
                sleep(2 ** attempt)