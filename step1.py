import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
import json

# Load environment variables
load_dotenv()

def get_mime_type(file_path):
    extension = file_path.lower().split('.')[-1]
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp'
    }
    return mime_types.get(extension, 'image/jpeg')

# test your code with this function

def caption_image(image_path, prompt="Caption this image.", api_key=None):
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API key not found. Set it in .env or pass explicitly.")

    # Configure Gemini
    genai.configure(api_key=api_key)

    # Load image bytes
    try:
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type = get_mime_type(image_path)

    # Create model and generate caption
    model = genai.GenerativeModel("gemini-2.5-flash")  # or 'gemini-2.5-pro' if available
    response = model.generate_content([
        {"mime_type": mime_type, "data": image_data},
        prompt
    ])

    return response.text


def extract_json_from_caption(caption):
    try:
        match = re.search(r"```json\s*(\{.*?\})\s*```", caption, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in the caption.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON: {e}")


def generate_coverage_details():
    image_path = r"C:/Users/Lenovo/OneDrive/Pictures/Screenshots/Screenshot 2025-07-02 032652.png"
    prompt = """From this image, estimate the land coverage percentages and return the result in valid JSON format. The JSON must match the following schema:
    {
    "plant_coverage": float,
    "building_coverage": float,
    "road_coverage": float,
    "empty_land": float,
    "water_body": float
    }
    Only return the JSON object. Do not include any explanation or extra text. All values should be in percentage format as floats (e.g., 23.5).
"""

    try:
        caption = caption_image(image_path, prompt=prompt)
        parsed_json = extract_json_from_caption(caption)
        return parsed_json
    except Exception as e:
        return e

# if __name__ == "__main__":
#     main()

print(generate_coverage_details())