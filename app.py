from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
from sqlite3 import Error

import step1  # Assuming step1.py contains the necessary functions for image processing
import step2 # Assuming step2.py contains the necessary functions for weather API integration

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
    
    # This is where the code for analyzing the image would go this will take the image pass it to the model to analyze call a weather api pass both the data to the new ai step and then return a report on it and on its bases return a report 
    pass