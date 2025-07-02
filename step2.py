import os
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

# Data structures
@dataclass
class WeatherData:
    temperature: float
    humidity: float
    pressure: float
    weather_description: str
    wind_speed: float
    precipitation: float
    feels_like: float
    uv_index: float
    visibility: float
    local_time: str
    timezone: str

@dataclass
class SeasonData:
    season: str
    month: int
    day_of_year: int
    is_growing_season: bool
    planting_season: str

@dataclass
class LandCoverageData:
    plant_coverage: float
    building_coverage: float
    road_coverage: float
    empty_land: float
    water_body: float

@dataclass
class LocationData:
    latitude: float
    longitude: float
    city: str
    country: str

class PlantRecommendationParser(BaseOutputParser):
    def parse(self, text: str) -> Dict:
        try:
            lines = text.strip().split('\n')
            recommendations = []
            current_plant = {}

            for line in lines:
                line = line.strip()
                if line.startswith('Plant:') or line.startswith('**Plant:'):
                    if current_plant:
                        recommendations.append(current_plant)
                    current_plant = {'name': line.split(':', 1)[1].strip().replace('**', '')}
                elif line.startswith('Reason:') or line.startswith('**Reason:'):
                    current_plant['reason'] = line.split(':', 1)[1].strip().replace('**', '')
                elif line.startswith('Care:') or line.startswith('**Care:'):
                    current_plant['care'] = line.split(':', 1)[1].strip().replace('**', '')

            if current_plant:
                recommendations.append(current_plant)

            return {
                'recommendations': recommendations,
            }
        except Exception as e:
            return {
                'recommendations': [],
                'error': str(e)
            }

class WeatherService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1/current.json"

    def get_weather_data(self, city: str) -> Optional[WeatherData]:
        try:
            params = {'key': self.api_key, 'q': city, 'aqi': 'no'}
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()
            current = data['current']
            location = data['location']

            return WeatherData(
                temperature=current['temp_c'],
                humidity=current['humidity'],
                pressure=current['pressure_mb'],
                weather_description=current['condition']['text'],
                wind_speed=current['wind_kph'] / 3.6,
                precipitation=current['precip_mm'],
                feels_like=current['feelslike_c'],
                uv_index=current['uv'],
                visibility=current['vis_km'],
                local_time=location['localtime'],
                timezone=location['tz_id']
            )
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None

class SeasonService:
    @staticmethod
    def determine_season(date_str: str, timezone_str: str, latitude: float = 0, city: str = "", country: str = "") -> SeasonData:
        try:
            local_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            month = local_time.month
            day_of_year = local_time.timetuple().tm_yday
            is_southern = latitude < 0
            season = "Unknown"
            planting = "Season-appropriate planting recommended"

            # Monsoon logic for Indian subcontinent (rough guideline: June to September)
            is_tropical_region = country.lower() in ["india", "bangladesh", "sri lanka", "nepal", "pakistan"]
            if is_tropical_region and month in [6, 7, 8, 9]:
                season = "Rainy"
                planting = "Excellent for rice, sugarcane, tropical fruits, and water-loving plants"
            else:
                if is_southern:
                    if month in [12, 1, 2]:
                        season = "Summer"
                    elif month in [3, 4, 5]:
                        season = "Autumn"
                    elif month in [6, 7, 8]:
                        season = "Winter"
                    else:
                        season = "Spring"
                else:
                    if month in [12, 1, 2]:
                        season = "Winter"
                    elif month in [3, 4, 5]:
                        season = "Spring"
                    elif month in [6, 7, 8]:
                        season = "Summer"
                    else:
                        season = "Autumn"

                if season == "Spring":
                    planting = "Prime planting time for most plants"
                elif season == "Summer":
                    planting = "Good for heat-tolerant plants, ensure adequate watering"
                elif season == "Autumn":
                    planting = "Good for trees and shrubs, prepare for dormancy"
                else:
                    planting = "Indoor planting or dormant season preparations"

            is_growing = season in ["Spring", "Summer", "Rainy"]
            return SeasonData(season, month, day_of_year, is_growing, planting)

        except Exception as e:
            print(f"Error determining season: {e}")
            return SeasonData("Unknown", datetime.now().month, datetime.now().timetuple().tm_yday, True, "Season-appropriate planting recommended")

    @staticmethod
    def get_location_coordinates(city: str, country: str) -> tuple:
        coordinates = {
            "lucknow": (26.8467, 80.9462),
            "delhi": (28.7041, 77.1025),
            "mumbai": (19.0760, 72.8777),
            "bangalore": (12.9716, 77.5946),
            "london": (51.5074, -0.1278),
            "new york": (40.7128, -74.0060),
            "sydney": (-33.8688, 151.2093)
        }
        return coordinates.get(city.lower(), (26.8467, 80.9462))  # Default to Lucknow

class PlantRecommendationSystem:
    def __init__(self, weatherapi_key: str, gemini_api_key: str):
        self.weather_service = WeatherService(weatherapi_key)
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.prompt_template = PromptTemplate(
            input_variables=[
                "temperature", "humidity", "weather_description", "wind_speed", 
                "precipitation", "feels_like", "uv_index", "visibility",
                "plant_coverage", "building_coverage", "road_coverage", 
                "empty_land", "water_body", "city", "country", "season", "planting_season"
            ],
            template="""
                You are an expert botanist and landscape designer. Based on the following environmental conditions and the current season, recommend 3-5 suitable plants that can thrive in this location.

                Location: {city}, {country}

                Weather Conditions:
                - Temperature: {temperature}°C (Feels like: {feels_like}°C)
                - Humidity: {humidity}%
                - Weather: {weather_description}
                - Wind Speed: {wind_speed} m/s
                - Precipitation: {precipitation} mm
                - UV Index: {uv_index}
                - Visibility: {visibility} km

                Land Coverage:
                - Plant Coverage: {plant_coverage}%
                - Building Coverage: {building_coverage}%
                - Road Coverage: {road_coverage}%
                - Empty Land Available: {empty_land}%
                - Water Bodies: {water_body}%

                Season: {season}
                Planting Guidelines: {planting_season}

                Please provide recommendations in the following format for each plant:

                Plant: [Plant Name]
                Reason: [Why this plant is suitable for these conditions]
                Care: [Basic care instructions]
                """
        )
        self.parser = PlantRecommendationParser()

    def get_plant_recommendations(self, city: str, land_coverage: LandCoverageData, country: str = "India") -> Dict:
        weather_data = self.weather_service.get_weather_data(city)
        if not weather_data:
            return {"error": "Could not fetch weather data"}

        total_coverage = (
            land_coverage.plant_coverage +
            land_coverage.building_coverage +
            land_coverage.road_coverage +
            land_coverage.empty_land
        )
        if abs(total_coverage - 100) > 1:
            return {"error": "Land coverage percentages must sum to 100%"}

        latitude, _ = SeasonService.get_location_coordinates(city, country)
        season_data = SeasonService.determine_season(
            weather_data.local_time, weather_data.timezone, latitude
        )

        prompt = self.prompt_template.format(
            temperature=weather_data.temperature,
            humidity=weather_data.humidity,
            weather_description=weather_data.weather_description,
            wind_speed=weather_data.wind_speed,
            precipitation=weather_data.precipitation,
            feels_like=weather_data.feels_like,
            uv_index=weather_data.uv_index,
            visibility=weather_data.visibility,
            plant_coverage=land_coverage.plant_coverage,
            building_coverage=land_coverage.building_coverage,
            road_coverage=land_coverage.road_coverage,
            empty_land=land_coverage.empty_land,
            city=city,
            country=country,
            season=season_data.season,
            planting_season=season_data.planting_season
        )

        try:
            response = self.model.generate_content(prompt)
            parsed_result = self.parser.parse(response.text)
            parsed_result['weather_data'] = weather_data.__dict__
            parsed_result['land_coverage'] = land_coverage.__dict__
            parsed_result['season'] = season_data.__dict__
            parsed_result['location'] = {'city': city, 'country': country}
            return parsed_result
        except Exception as e:
            return {"error": f"Error generating recommendations: {str(e)}"}

def generate_final_report(coverage_details: Dict) -> Dict:
    WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY')
    GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

    if not WEATHERAPI_KEY or not GEMINI_API_KEY:
        print("Missing API keys. Please set WEATHERAPI_KEY and GEMINI_API_KEY in your .env file.")
        return {
            "status": "error",
            "message": "API keys not found. Please set WEATHERAPI_KEY and GEMINI_API_KEY in your .env file.",
            "result": None,
        }

    if not coverage_details:
        return {
            "status": "error",
            "message": "No coverage details provided.",
            "result": None,
        }

    plant_system = PlantRecommendationSystem(WEATHERAPI_KEY, GEMINI_API_KEY)

    land_coverage = LandCoverageData(
        plant_coverage= coverage_details["plant_coverage"],
        building_coverage= coverage_details["building_coverage"],
        road_coverage= coverage_details["road"],
        empty_land= coverage_details["empty_land"],
        water_body=coverage_details["water_body"]
    )

    city = "Lucknow"
    country = "India"

    print(f"Getting plant recommendations for {city}, {country}...")
    results = plant_system.get_plant_recommendations(city, land_coverage, country)

    if "error" in results:
        return {
            "status": "error",
            "message": results["error"],
            "result": None,
        }

    return {
        "status": "success",
        "message": "Plant recommendations generated successfully.",
        "result": results,
    }
# if __name__ == "__main__":
#     main()
