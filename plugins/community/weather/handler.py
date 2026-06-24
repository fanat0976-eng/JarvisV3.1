"""
Weather plugin — current weather + forecast via Open-Meteo (free, no API key).
"""
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def _get_coords(city: str) -> dict:
    geocoding = "https://geocoding-api.open-meteo.com/v1/search"
    r = httpx.get(geocoding, params={"name": city, "count": 1, "language": "ru"}, timeout=10)
    results = r.json().get("results", [])
    if not results:
        return {}
    return results[0]


@router.get("/health")
def health():
    return {"status": "ok", "plugin": "weather", "provider": "open-meteo"}


@router.get("/current")
def current(city: str = "Moscow"):
    coords = _get_coords(city)
    if not coords:
        return JSONResponse({"error": f"City '{city}' not found"}, status_code=404)

    r = httpx.get(OPEN_METEO, params={
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "current_weather": True,
        "timezone": coords.get("timezone", "auto"),
    }, timeout=10)
    data = r.json().get("current_weather", {})

    return {
        "city": coords.get("name", city),
        "country": coords.get("country", ""),
        "temperature": data.get("temperature"),
        "windspeed": data.get("windspeed"),
        "winddirection": data.get("winddirection"),
        "weathercode": data.get("weathercode"),
        "time": data.get("time"),
    }


@router.get("/forecast")
def forecast(city: str = "Moscow", days: int = 3):
    coords = _get_coords(city)
    if not coords:
        return JSONResponse({"error": f"City '{city}' not found"}, status_code=404)

    r = httpx.get(OPEN_METEO, params={
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": coords.get("timezone", "auto"),
        "forecast_days": min(days, 7),
    }, timeout=10)
    daily = r.json().get("daily", {})

    days_data = []
    for i in range(len(daily.get("time", []))):
        days_data.append({
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precipitation": daily["precipitation_sum"][i],
            "weathercode": daily["weathercode"][i],
        })

    return {"city": coords.get("name", city), "forecast": days_data}


def on_startup():
    print("  [weather] Started: Open-Meteo provider")


def on_shutdown():
    pass
