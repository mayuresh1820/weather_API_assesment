import os
import requests
import xml.etree.ElementTree as ET

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv


# Loading environment variables (API keys, secrets, etc.)
load_dotenv()

# External Weather API configuration
WEATHER_API_URL = "https://weatherapi-com.p.rapidapi.com/current.json"
WEATHER_API_HOST = "weatherapi-com.p.rapidapi.com"
WEATHER_API_KEY = os.getenv("RAPIDAPI_KEY")


app = FastAPI(title="Current Weather Service")


class WeatherRequest(BaseModel):
    """
    Incoming request model.
    FastAPI automatically validates this structure.
    """
    city: str
    output_format: str  # Expected values: json | xml


def get_weather_from_api(city: str) -> dict:
    """
    Calls the external Weather API and returns raw weather data.
    """
    if not WEATHER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Weather API key is missing",
        )

    headers = {
        "X-RapidAPI-Key": WEATHER_API_KEY,
        "X-RapidAPI-Host": WEATHER_API_HOST,
    }

    response = requests.get(
        WEATHER_API_URL,
        headers=headers,
        params={"q": city},
        timeout=10,
    )

    # Raise an exception for non-200 responses
    response.raise_for_status()
    return response.json()


def convert_dict_to_xml(data: dict) -> str:
    """
    Converts a simple dictionary into an XML string.
    """
    root = ET.Element("root")

    for key, value in data.items():
        child = ET.SubElement(root, key)
        child.text = str(value)

    return ET.tostring(root, encoding="utf-8").decode()


@app.get("/")
def service_status():
    """
    Basic health-check endpoint.
    """
    return {"status": "Weather service is running"}


@app.post("/getCurrentWeather")
def get_current_weather(request: WeatherRequest):
    """
    Main endpoint that returns current weather
    information in JSON or XML format.
    """
    # Validate requested output format
    if request.output_format not in {"json", "xml"}:
        raise HTTPException(
            status_code=400,
            detail="output_format must be either 'json' or 'xml'",
        )

    try:
        weather_response = get_weather_from_api(request.city)

        # Extract only the required information
        formatted_result = {
            "City": weather_response["location"]["name"],
            "Weather": f"{weather_response['current']['temp_c']} C",
            "Latitude": weather_response["location"]["lat"],
            "Longitude": weather_response["location"]["lon"],
        }

        # Return response in requested format
        if request.output_format == "xml":
            return convert_dict_to_xml(formatted_result)

        return formatted_result

    except requests.RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
