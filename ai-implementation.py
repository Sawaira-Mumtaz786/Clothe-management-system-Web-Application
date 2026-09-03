import os
import json
from google import genai
from google.genai import types

def analyze_clothing_image(image_path):
    """
    Uses Google Gemini AI to inspect a clothing photo and auto-fill details.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    # If no key is set, return default empty values safely
    if not api_key:
        print("Warning: GEMINI_API_KEY is not set.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = """
        Analyze this clothing image and identify:
        1. Item Name (e.g., 'Blue Denim Jacket')
        2. Category (Must be one of: 'Men', 'Women', 'Kids')
        3. Season (Must be one of: 'Summer', 'Winter')
        4. Size (Must be one of: 'S', 'M', 'L', 'XL')
        5. Color

        Return ONLY a JSON object formatted like this without markdown block formatting:
        {
            "name": "Blue Denim Jacket",
            "category": "Men",
            "season": "Winter",
            "size": "L",
            "color": "Blue"
        }
        """

        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt
            ]
        )

        # Parse JSON response
        clean_json = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_json)

    except Exception as e:
        print(f"AI Tagging Error: {e}")
        return None
