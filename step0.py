import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise ValueError("Google Maps API key not found. Set it in .env or pass explicitly.")

latitude = 26.856
longitude = 81.050763
zoom = 18
size = "600x640"  # Width x Height in pixels (max: 640x640 for free tier)
map_type = "satellite"  # roadmap, satellite, terrain, hybrid

# === Build URL ===
url = (
    f"https://maps.googleapis.com/maps/api/staticmap?"
    f"center={latitude},{longitude}&zoom={zoom}&size={size}&maptype={map_type}&key={API_KEY}"
)

# === Download the image ===
response = requests.get(url)

if response.status_code == 200:
    with open("static_map.png", "wb") as f:
        f.write(response.content)
    print("✅ Map image saved as static_map.png")
else:
    print(f"❌ Failed to download map: {response.status_code}")
    print(response.text)
