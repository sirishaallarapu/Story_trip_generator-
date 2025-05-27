import logging
from openai import OpenAI
import json
import re
from time import sleep

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI(timeout=20.0)

def extract_mood_intent_destinations(prompt: str):
    logger.info(f"Extracting mood, intent, and destinations from prompt: {prompt}")
    dest_pattern = re.compile(r"\bin\s+([A-Za-z\s,']+?)(?:\s|$)", re.IGNORECASE)
    dest_match = dest_pattern.search(prompt)
    destination = dest_match.group(1).strip() if dest_match else prompt.strip()

    prompt_text = f"""
    Analyze the user prompt to extract the mood, intent, and specific destination.
    Prompt: "{prompt}"
    Return a JSON object with:
    - mood: 'adventurous' if 'adventure' or related terms (e.g., thrilling, exciting) are in the prompt, else 'relaxing'
    - intent: 'adventure trip' if adventurous, else 'beach holiday'
    - destinations: List with one specific location (e.g., 'Maafushi, Maldives' for Maldives, 'Anjuna, Goa' for Goa). Infer specific location if prompt is vague.
    Example:
    ```json
    {{
        "mood": "adventurous",
        "intent": "adventure trip",
        "destinations": ["Anjuna, Goa"]
    }}
    ```
    Return valid JSON only.
    """
    max_retries = 1
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Switched to gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": "Respond with valid JSON only."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=150,  # Reduced for speed
                timeout=10.0
            )
            raw_response = response.choices[0].message.content
            logger.debug(f"Raw OpenAI response: {raw_response}")
            data = json.loads(raw_response)
            if destination:
                if "Maldives" in destination:
                    destinations = [data.get("destinations", ["Maafushi, Maldives"])[0]]
                elif "Goa" in destination:
                    destinations = [data.get("destinations", ["Anjuna, Goa"])[0]]
                else:
                    destinations = [destination]
            else:
                destinations = data.get("destinations", ["Anjuna, Goa"])[:1]
            return {
                "mood": data.get("mood", "adventurous" if "adventure" in prompt.lower() else "relaxing"),
                "intent": data.get("intent", "adventure trip" if "adventure" in prompt.lower() else "beach holiday"),
                "destinations": destinations
            }, destinations
        except Exception as e:
            logger.error(f"Error (attempt {attempt+1}): {str(e)}")
            if attempt == max_retries - 1:
                fallback = {
                    "mood": "adventurous" if "adventure" in prompt.lower() else "relaxing",
                    "intent": "adventure trip" if "adventure" in prompt.lower() else "beach holiday",
                    "destinations": ["Anjuna, Goa" if "Goa" in prompt else "Maafushi, Maldives"]
                }
                return fallback, fallback["destinations"]
            sleep(1)