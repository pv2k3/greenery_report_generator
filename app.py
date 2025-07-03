from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
from sqlite3 import Error

from step0 import download_static_map
from step1 import generate_coverage_details
from step2 import generate_final_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def test():
    return {
        "status": "success",
        "message": "Welcome to the Image Greenery Report Generator API"
    }

@app.post("/analyze-image/")
async def analyze_image(request: Request, file: UploadFile = File(...)):
    pass  # Placeholder for future image analysis logic

@app.post("/analyze-location/")
async def analyze_location(request: Request, latitude: float = Form(...), longitude: float = Form(...), zoom: int = Form(18)):
    """    Analyze a location by downloading a static map and generating a coverage report.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        zoom (int): Zoom level for the static map.
    Returns:
        dict: Result with status, message, and analysis result.
    """
    map_result = download_static_map(latitude, longitude, zoom=zoom)

    if map_result["status"] == "error":
        return {
            "status": "error",
            "message": map_result["message"],
            "file_path": None
        }
    try:
        coverage_details = generate_coverage_details(map_result["file_path"])
        if coverage_details["status"] == "error":
            return {
                "status": "error",
                "message": coverage_details["message"],
                "file_path": map_result["file_path"]
            }
        final_report = generate_final_report(coverage_details["caption"])
        return {
            "status": "success",
            "message": "Location analyzed successfully.",
            "file_path": map_result["file_path"],
            "final_report": final_report
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "file_path": map_result["file_path"]
        }
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)