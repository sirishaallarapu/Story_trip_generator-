import sys
import os
import re
import textwrap
import logging
from decimal import Decimal
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.prompt_templates import get_itinerary_prompt
from time import sleep
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=25.0)

def extract_mood_intent_destinations(prompt: str):
    logger.info(f"Extracting mood, intent, and destinations from prompt: {prompt}")
    prompt_lower = prompt.lower()

    dest_pattern = re.compile(r"(?:in|to)\s+([A-Za-z\s,']+?)(?:\s|$|[.!?])", re.IGNORECASE)
    dest_match = dest_pattern.search(prompt)

    if dest_match:
        raw_destination = dest_match.group(1).strip().lower()
    else:
        raw_destination = prompt.strip().lower()

    logger.info(f"Raw destination extracted: {raw_destination}")


    mood = (
        "romantic" if "couple" in prompt_lower else
        "lively" if "beach" in prompt_lower or "fun" in prompt_lower else
        "adventurous" if "adventure" in prompt_lower else
        "relaxing" if "spa" in prompt_lower else
        "cultural"
    )
    intent = (
        "romantic trip" if "couple" in prompt_lower else
        "beach trip" if "beach" in prompt_lower else
        "adventure trip" if "adventure" in prompt_lower else
        "cultural exploration" if "culture" in prompt_lower or "history" in prompt_lower else
        "city exploration"
    )

    prompt_text = f"""
Analyze the user prompt to extract the mood, intent, and specific destination.
Prompt: "{prompt}"
Return a JSON object with:
- mood: 'romantic', 'lively', 'adventurous', 'relaxing', or 'cultural'
- intent: 'romantic trip', 'beach trip', 'adventure trip', 'cultural exploration', or 'city exploration'
- destinations: List with one destination (e.g., 'Sultanahmet' if 'Turkey' is mentioned). If ambiguous, use a specific area.
Default to 'Unknown, Please Specify' if not extractable.
Return valid JSON only.
"""

    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Respond with valid JSON only."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.2,
                max_tokens=150
            )
            raw_response = response.choices[0].message.content
            logger.debug(f"OpenAI response: {raw_response}")
            data = json.loads(raw_response)

            destinations = data.get("destinations", [raw_destination or "Unknown, Please Specify"])
            if not destinations or not isinstance(destinations, list):
                destinations = [raw_destination or "Unknown, Please Specify"]

            result = {
                "mood": data.get("mood", mood),
                "intent": data.get("intent", intent),
                "destinations": destinations
            }
            logger.info(f"Extracted result: {result}")
            return result, destinations
        except Exception as e:
            logger.error(f"OpenAI error (attempt {attempt + 1}): {str(e)}")
            if attempt == max_retries - 1:
                fallback = {
                    "mood": mood,
                    "intent": intent,
                    "destinations": [raw_destination or "Unknown, Please Specify"]
                }
                logger.info(f"Fallback result: {fallback}")
                return fallback, fallback["destinations"]
            sleep(1)

def validate_itinerary_costs(itinerary, num_members, expected_duration, trip_type, destination, strict=True):
    try:
        days = re.split(r'Day \d+[ :–-]*', itinerary)[1:]
        if len(days) != expected_duration:
            return False, [], Decimal('0'), f"Day count mismatch: found {len(days)}, expected {expected_duration}"

        calculated_total = Decimal('0')
        daily_totals = []

        keyword_map = {
            'beach': {
                'allowed': ['swimming', 'snorkeling', 'beach volleyball', 'sunbathing', 'kayaking', 'sandcastle', 'beach yoga', 'banana boat ride'],
                'disallowed': ['romantic', 'candlelit', 'couple', 'spa', 'heritage', 'museum']
            },
            'adventure': {
                'allowed': ['scuba', 'diving', 'jet ski', 'parasailing', 'windsurfing', 'adventure', 'kayaking'],
                'disallowed': ['romantic', 'sunset', 'candlelit', 'couple', 'spa', 'beach volleyball', 'sandcastle']
            },
            'romantic': {
                'allowed': ['candlelit', 'dinner', 'couple', 'spa', 'cruise'],
                'disallowed': ['scuba', 'jet ski', 'kayaking', 'adventure', 'snorkeling', 'volleyball']
            },
            'cultural': {
                'allowed': ['heritage', 'museum', 'cultural', 'temple', 'village tour', 'ashram', 'textile', 'jain', 'garba', 'stepwell'],
                'disallowed': ['romantic', 'sunset', 'candlelit', 'beach', 'adventure']
            },
            'generic': {
                'allowed': ['sightseeing', 'local markets', 'city tour', 'dining', 'museum', 'landmark'],
                'disallowed': ['romantic', 'sunset', 'candlelit', 'scuba', 'jet ski', 'beach']
            }
        }

        if destination.lower() == 'goa' and trip_type.lower() == 'beach':
            keyword_map['beach']['allowed'].extend(['baga beach', 'anjuna beach', 'curlies shack', 'club hopping'])
            keyword_map['beach']['disallowed'] = ['romantic', 'candlelit', 'couple', 'spa']
        elif destination.lower() == 'pondicherry' and trip_type.lower() == 'beach':
            keyword_map['beach']['allowed'].extend(['paradise beach', 'promenade beach', 'water sports', 'beach walk'])
            keyword_map['beach']['disallowed'] = ['romantic', 'candlelit', 'couple', 'spa']

        allowed_keywords = keyword_map[trip_type.lower()]["allowed"]
        disallowed_keywords = keyword_map[trip_type.lower()]["disallowed"]

        for i, day in enumerate(days):
            transport_cost = Decimal('0')
            accommodation_cost = Decimal('0')
            activity_costs = []
            meal_costs = []

            transport_match = re.search(r"Transport:.*Cost: ₹([\d,]+)", day)
            if transport_match:
                transport_cost = Decimal(transport_match.group(1).replace(",", ""))

            accommodation_match = re.search(r"Accommodation:.*Cost: ₹([\d,]+)", day)
            if accommodation_match:
                accommodation_cost = Decimal(accommodation_match.group(1).replace(",", ""))

            booking_link_match = re.search(r"Book Now: (https://www\.booking\.com/[^\s]+)", day)
            if i < expected_duration - 1 and not booking_link_match:
                return False, [], Decimal('0'), f"Day {i+1} missing valid Booking.com link"

            activities_section = re.search(r"Activities:\s*\n(.*?)(?:\n[A-Z][a-z]+:|\Z)", day, re.DOTALL)
            if activities_section and i < expected_duration - 1:
                activity_cost_matches = re.findall(r"  - .*Cost: ₹([\d,]+) per person", activities_section.group(1))
                activity_costs = [Decimal(cost.replace(",", "")) * Decimal(num_members) for cost in activity_cost_matches]
                if len(activity_costs) != 3:
                    return False, [], Decimal('0'), f"Day {i+1} has {len(activity_costs)} activities, expected 3"
                activity_text = activities_section.group(1).lower()
                if strict and not any(keyword in activity_text for keyword in allowed_keywords):
                    return False, [], Decimal('0'), f"Day {i+1} lacks {trip_type} activities. Expected: {allowed_keywords}"
                if strict:
                    disallowed_found = [keyword for keyword in disallowed_keywords if keyword in activity_text]
                    if disallowed_found:
                        return False, [], Decimal('0'), f"Day {i+1} contains disallowed activities for {trip_type}: {disallowed_found}"

            meals_section = re.search(r"Meals:\s*\n(.*?)(?:\n[A-Z][a-z]+:|\Z)", day, re.DOTALL)
            if meals_section:
                if i < expected_duration - 1:
                    meal_cost_matches = re.findall(r"  - .*Cost: ₹([\d,]+) per person", meals_section.group(1))
                    meal_costs = [Decimal(cost.replace(",", "")) * Decimal(num_members) for cost in meal_cost_matches]
                    if len(meal_costs) != 3:
                        return False, [], Decimal('0'), f"Day {i+1} has {len(meal_costs)} meals, expected 3"
                else:
                    breakfast_cost_matches = re.findall(r"  - Breakfast:.*Cost: ₹([\d,]+) per person", meals_section.group(1))
                    meal_costs = [Decimal(cost.replace(",", "")) * Decimal(num_members) for cost in breakfast_cost_matches]
                    if len(meal_costs) != 1:
                        return False, [], Decimal('0'), f"Day {i+1} has {len(meal_costs)} meals, expected 1 breakfast"

            expected_daily_total = transport_cost + accommodation_cost + sum(activity_costs) + sum(meal_costs)
            daily_totals.append(expected_daily_total)
            calculated_total += expected_daily_total

        return True, daily_totals, calculated_total, "Costs validated successfully."
    except Exception as e:
        return False, [], Decimal('0'), f"Validation failed: {str(e)}"

def post_process_itinerary(itinerary, vibe, daily_totals, total_cost, destination):
    try:
        if not daily_totals or len(daily_totals) == 0:
            return itinerary
        lines = itinerary.splitlines()
        day_index = -1
        for i, line in enumerate(lines):
            if re.match(r"Day \d+[ :–-]*", line):
                day_index += 1
                lines[i] = line.replace('–', '-')
            if line.startswith("Total Cost:") and day_index < len(daily_totals):
                lines[i] = f"Total Cost: INR {int(daily_totals[day_index]):,}"
            elif re.match(r"Day \d+[ :–-]*.*Departure", line) and day_index == len(daily_totals) - 1:
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                if not next_line.startswith("Total Cost:"):
                    lines.insert(i + 1, f"Total Cost: INR {int(daily_totals[day_index]):,}")
            if "Book Now:" in line:
                hotel_name = re.search(r"Accommodation: (.*?)(?: \(|\Z)", line)
                if hotel_name:
                    hotel_slug = hotel_name.group(1).strip().lower().replace(" ", "-").replace("&", "and")
                    country_code = (
                        "in" if destination.lower() in ["goa", "andaman", "hyderabad", "gujarat", "pondicherry"] else
                        "id" if destination.lower() == "bali" else
                        "th" if destination.lower() == "thailand" else
                        "au" if destination.lower() in ["sydney", "australia"] else
                        "mv"
                    )
                    lines[i] = re.sub(
                        r"Book Now:.*",
                        f"Book Now: https://www.booking.com/hotel/{country_code}/{hotel_slug}.html",
                        line
                    )

        if lines[0].startswith("Your Trip Itinerary") and not lines[1].startswith(vibe):
            lines.insert(1, vibe)

        for i, line in enumerate(lines):
            if line.startswith("Total Estimated Trip Cost:"):
                lines[i] = f"Total Estimated Trip Cost: INR {int(total_cost):,}"
                break

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Post-processing error: {str(e)}")
        return itinerary

def validate_destination_trip_type(destination, trip_type):
    invalid_combinations = {
        'hyderabad': ['beach'],
        'delhi': ['beach'],
        'jaipur': ['beach'],
        'agra': ['beach'],
        'kolkata': ['beach'],
        'gujarat': ['beach', 'adventure']
    }
    valid_trip_types = ['generic', 'beach', 'adventure', 'romantic', 'cultural']
    if trip_type not in valid_trip_types:
        return False, f"Invalid trip type: {trip_type}. Must be one of: {', '.join(valid_trip_types)}."
    if (
        trip_type != 'generic' and
        destination.lower() in invalid_combinations and
        trip_type in invalid_combinations[destination.lower()]
    ):
        return False, f"No itinerary available for {trip_type} trip in {destination.capitalize()}. Please choose a different trip type or destination."
    return True, ""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
import os
import textwrap
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_pdf(itinerary, output_path=None, destination="Trip", vibe="",
                 logo_path=r"C:\Users\Dell\Desktop\mytrip_generator\mytrip_generator\frontend\src\assets\infologo1.png"):
    try:
        # Prepare safe filename if output_path not given
        if not output_path:
            safe_destination = destination.replace(" ", "_")
            output_path = f"{safe_destination}_Trip_Itinerary.pdf"

        # Create PDF doc with margins
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=15*mm, leftMargin=15*mm,
                                topMargin=30*mm, bottomMargin=20*mm)

        # Set PDF metadata
        doc.title = f"{destination} Trip Itinerary"
        doc.author = "YourAppName"
        doc.subject = f"{vibe} themed trip itinerary"
        doc.creator = "YourAppName"

        width, height = A4

        # Prepare styles
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 11
        normal_style.leading = 14

        day_style = ParagraphStyle(
            'DayStyle',
            parent=normal_style,
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor='#1E5AA0',
            spaceAfter=10,
        )
        italic_style = ParagraphStyle(
            'ItalicStyle',
            parent=normal_style,
            fontName='Helvetica-Oblique',
            fontSize=11,
            leading=14,
            spaceAfter=6,
        )
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        vibe_style = ParagraphStyle(
            'VibeStyle',
            fontName='Helvetica-Oblique',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        footer_style = ParagraphStyle(
            'FooterStyle',
            fontName='Helvetica',
            fontSize=8,
            alignment=TA_CENTER,
        )

        story = []

        # Remove logo Image from story; logo will be drawn on canvas in page callback

        # Add Title and vibe centered
        story.append(Paragraph(f"{destination.upper()} TRIP ITINERARY", title_style))
        story.append(Paragraph(f"Theme: {vibe}", vibe_style))

        # Prepare itinerary lines with replacements and splitting
        lines = itinerary.replace('\u20b9', 'INR ').replace('\u2013', '-').strip().splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Day"):
                story.append(Paragraph(line, day_style))
            elif line.startswith(("Transport", "Accommodation", "Activities", "Meals")):
                story.append(Paragraph(line, italic_style))
            else:
                # Wrap long lines manually
                wrapped_lines = textwrap.wrap(line, 95)
                for wline in wrapped_lines:
                    story.append(Paragraph(wline, normal_style))
            story.append(Spacer(1, 4))  # small spacing after each paragraph

        # Page callback to add footer, page number, and logo on every page
        def add_page_elements(canvas, doc):
            canvas.saveState()
            # Footer text - generated date left bottom
            canvas.setFont('Helvetica', 8)
            canvas.drawString(15 * mm, 15 * mm, f"Generated on: {datetime.now().strftime('%m/%d/%Y')}")
            # Page number right bottom
            canvas.drawRightString(doc.pagesize[0] - 15 * mm, 15 * mm, f"Page {doc.page}")

            # Draw logo top-right corner
            if os.path.exists(logo_path):
                logo_img = ImageReader(logo_path)
                logo_width = 50 * mm
                logo_height = 20 * mm
                x = doc.pagesize[0] - logo_width - 15 * mm
                y = doc.pagesize[1] - logo_height - 15 * mm
                canvas.drawImage(logo_img, x, y, width=logo_width, height=logo_height,
                                 preserveAspectRatio=True, mask='auto')

            canvas.restoreState()

        # Build the PDF
        doc.build(story, onFirstPage=add_page_elements, onLaterPages=add_page_elements)

        logger.info(f"PDF generated successfully at {output_path}")
        return True, output_path

    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        return False, f"Error: Failed to generate PDF: {str(e)}"


def build_itinerary(data):
    logger.info(f"Building itinerary for: {data}")
    vibe = "Relaxed and memorable - A wonderful escape"
    valid = True
    trip_type = data.get("trip_type", "generic").lower() or "generic"
    destination = data.get("destination", "").lower()

    try:
        prompt = f"Plan a {trip_type} trip to {destination}"
        extracted_data, extracted_destinations = extract_mood_intent_destinations(prompt)
        destination = extracted_data["destinations"][0].lower() if extracted_destinations else destination

        required_fields = ["destination", "trip_type", "budget", "num_members", "start_date", "end_date", "food_preference"]
        missing = [key for key in required_fields if key not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

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

        duration = data.get("duration")
        if not duration:
            duration = (end_date - start_date).days + 1
        if duration <= 0:
            raise ValueError("End date must be after start date.")

        num_members = data["num_members"]
        budget_tier = data["budget"].lower()
        food_preference = data["food_preference"].lower()
        rooms_needed = math.ceil(num_members / 2)

        budget_map = {
            "low": "Low-budget (basic stay, public/shared transport, budget-friendly activities and meals)",
            "medium": "Medium-budget (comfortable stay, private transport, a mix of budget and premium activities and meals)",
            "high": "High-budget (luxury stay in 5-star hotels, premium transport and dining)"
        }
        if budget_tier not in budget_map:
            raise ValueError(f"Invalid budget: {budget_tier}. Must be 'low', 'medium', or 'high'.")
        budget_description = budget_map[budget_tier]

        vibe_map = {
            "beach": f"Sunny and serene - A classic beach retreat in {destination.capitalize()}",
            "adventure": f"Thrilling and bold - An adrenaline-packed {trip_type} trip in {destination.capitalize()}",
            "romantic": f"Romantic and intimate - A dreamy {trip_type} escape in {destination.capitalize()}",
            "cultural": f"Authentic and immersive - A deep dive into the local culture of {destination.capitalize()}",
            "generic": f"Iconic and memorable - Exploring the must-see landmarks of {destination.capitalize()}"
        }
        vibe = vibe_map.get(trip_type, vibe_map["generic"])
        data["vibe"] = vibe

        valid, error_message = validate_destination_trip_type(destination, trip_type)
        effective_trip_type = trip_type if valid else "generic"
        if not valid:
            vibe = vibe_map["generic"]
            logger.info(f"Invalid trip type {trip_type} for {destination}. Using generic itinerary.")

        activity_examples = {
            "beach": (
                "snorkeling, swimming, beach volleyball, sunbathing, kayaking, beach yoga, sandcastle building, "
                "banana boat ride, baga beach, anjuna beach, curlies shack, club hopping"
                if destination.lower() == "goa" else
                "snorkeling, swimming, beach volleyball, sunbathing, kayaking, beach yoga, sandcastle building, "
                "paradise beach, promenade beach, water sports, beach walk"
                if destination.lower() == "pondicherry" else
                "snorkeling, swimming, beach volleyball, sunbathing, kayaking, beach yoga, sandcastle building, "
                "nusa dua beach"
                if destination.lower() == "bali" else
                "snorkeling, swimming, beach volleyball, sunbathing, kayaking, beach yoga, sandcastle building"
            ),
            "adventure": (
                "rock climbing, go-karting, zip-lining, laser tag, paragliding, rappelling, paintball"
                if destination.lower() == "hyderabad" else
                "scuba diving, jet skiing, parasailing, windsurfing, underwater scooter, snorkeling"
            ),
            "romantic": (
                "candlelit dinners, sunset cruises, couple’s spa, romantic beach walks, private villa dinner"
                if destination.lower() == "bali" else
                "candlelit dinners, sunset cruises, couple’s spa, romantic beach walks"
            ),
            "cultural": (
                "Sabarmati Ashram visit, textile museum tour, Dandi Salt March historical tour, Garba dance workshop, "
                "stepwell exploration, Jain temple visit, local handicraft workshop"
                if destination.lower() == "gujarat" else
                "local village visits, cultural shows, historical site exploration, craft workshops, museum visits, "
                "temple tours"
                if destination.lower() != "sydney" else
                "art gallery visit, historical tour, indigenous cultural experience, museum visit, cultural festival"
            ),
            "generic": (
                "Sydney Opera House tour, Harbour Bridge visit, Royal Botanic Garden walk, The Rocks historical tour, "
                "Bondi Beach visit"
                if destination.lower() == "sydney" else
                "Auroville visit, French Quarter tour, Sri Aurobindo Ashram, Promenade Beach walk, local market "
                "exploration"
                if destination.lower() == "pondicherry" else
                "sightseeing major landmarks, visiting iconic sites, exploring famous attractions, local markets, "
                "city tour"
            )
        }

        meal_examples = (
            "vegetarian (e.g., Gujarati thali, undhiyu, dhokla, thepla)"
            if food_preference == "veg" and destination.lower() == "gujarat" else
            "vegetarian (e.g., gado-gado, Balinese vegetable curry, tempeh satay)"
            if food_preference == "veg" and destination.lower() == "bali" else
            "non-vegetarian (e.g., Balinese grilled fish, chicken satay)"
            if food_preference == "non_veg" and destination.lower() == "bali" else
            "vegetarian (e.g., Goan vegetable curry, paneer tikka, bhaji pav)"
            if food_preference == "veg" and destination.lower() == "goa" else
            "non-vegetarian (e.g., Goan fish curry, prawn balchao)"
            if food_preference == "non_veg" and destination.lower() == "goa" else
            "vegetarian (e.g., dosa, vegetable korma, coconut chutney)"
            if food_preference == "veg" and destination.lower() == "pondicherry" else
            "non-vegetarian (e.g., Creole prawn curry, grilled fish, chicken vindaloo)"
            if food_preference == "non_veg" and destination.lower() == "pondicherry" else
            "non-vegetarian (e.g., Aussie BBQ, seafood platter, kangaroo steak)"
            if food_preference == "non_veg" and destination.lower() == "sydney" else
            "vegetarian (e.g., vegetable curry, paneer masala, coconut dhal)"
            if food_preference == "veg" else
            "non-vegetarian (e.g., grilled seafood, chicken masala)"
        )

        prompt = get_itinerary_prompt(
            data, vibe, effective_trip_type, valid, activity_examples, meal_examples, budget_description, rooms_needed,
            extracted_data
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} to generate itinerary")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional travel planner specializing in accurate "
                                                     "and detailed itineraries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=4000
                )
                itinerary = response.choices[0].message.content.strip()
                logger.info(f"Generated itinerary (preview): {itinerary[:200]}...")

                valid_costs, daily_totals, total_cost, message = validate_itinerary_costs(
                    itinerary, num_members, duration, effective_trip_type, destination, strict=(attempt < max_retries - 1)
                )
                if valid_costs:
                    processed_itinerary = post_process_itinerary(itinerary, vibe, daily_totals, total_cost, destination)
                    booking_links = re.findall(r"Book Now: (https://www\.booking\.com/[^\s]+)", processed_itinerary)
                    if len(booking_links) != duration - 1:
                        logger.warning(f"Invalid booking links: found {len(booking_links)}, expected {duration - 1}")
                        continue

                    pdf_output_path = f"itinerary_{destination}_{start_date.strftime('%Y%m%d')}.pdf"
                    pdf_success, pdf_result = generate_pdf(processed_itinerary, pdf_output_path, destination, vibe)
                    if not pdf_success:
                        logger.error(f"PDF generation failed: {pdf_result}")
                        return f"Your Trip Itinerary\n{vibe}\n\n{pdf_result}"

                    return processed_itinerary

                logger.warning(f"Validation failed: {message}")
                if attempt < max_retries - 1:
                    continue

                logger.info("Falling back to simplified itinerary")
                fallback_prompt = prompt + f"""
If specific activities are unavailable, use general {effective_trip_type} activities suitable for {destination.capitalize()}. For generic trips, prioritize iconic landmarks and must-see attractions. For beach trips in Pondicherry, include activities like Paradise Beach visit, kayaking, or Promenade Beach walk. Avoid activities unrelated to the selected trip type.
"""
                fallback_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional travel planner."},
                        {"role": "user", "content": fallback_prompt}
                    ],
                    temperature=0.6,
                    max_tokens=4000
                )
                fallback_itinerary = fallback_response.choices[0].message.content.strip()
                valid_costs, daily_totals, total_cost, message = validate_itinerary_costs(
                    fallback_itinerary, num_members, duration, effective_trip_type, destination, strict=False
                )
                if valid_costs:
                    processed_itinerary = post_process_itinerary(fallback_itinerary, vibe, daily_totals, total_cost,
                                                                destination)
                    pdf_output_path = f"itinerary_{destination}_{start_date.strftime('%Y%m%d')}.pdf"
                    pdf_success, pdf_result = generate_pdf(processed_itinerary, pdf_output_path, destination, vibe)
                    if not pdf_success:
                        logger.error(f"PDF generation failed: {pdf_result}")
                        return f"Your Trip Itinerary\n{vibe}\n\n{pdf_result}"
                    return processed_itinerary
                return (f"Your Trip Itinerary\n{vibe}\n\nError: Failed to generate valid {effective_trip_type} itinerary "
                        f"for {destination.capitalize()} after {max_retries} attempts.")

            except Exception as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    continue
                return (f"Your Trip Itinerary\n{vibe}\n\nError: OpenAI API failed after {max_retries} attempts: "
                        f"{str(e)}.")

        return (f"Your Trip Itinerary\n{vibe}\n\nError: Failed to generate valid {effective_trip_type} itinerary for "
                f"{destination.capitalize()} after {max_retries} attempts.")

    except Exception as e:
        logger.error(f"Itinerary building error: {str(e)}")
        return f"Your Trip Itinerary\n{vibe}\n\nError: Failed to build itinerary: {str(e)}"
