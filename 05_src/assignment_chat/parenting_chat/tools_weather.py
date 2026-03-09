from langchain.tools import tool
import requests

@tool
def plan_outdoor_reset(city: str = "Toronto") -> str:
    """
    Uses a weather API to suggest a calm outdoor window for a parent-child reset.
    A nice bonding activity for connecting with your kiddo
    Assume default location of Toronto Canada if city is empty or not found. ?????
    Returns a transformed, parent-friendly plan (not raw API output).
    """
    # Simplest approach: use Open-Meteo geocoding + forecast.
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=15
    )
    geo.raise_for_status()
    g = geo.json()
    if not g.get("results"):
        return f"I couldn’t find '{city}'. Try a nearby major city name."

    lat = g["results"][0]["latitude"]
    lon = g["results"][0]["longitude"]
    place = f'{g["results"][0]["name"]}, {g["results"][0].get("country","")}'

    forecast = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,wind_speed_10m",
            "forecast_days": 1
        },
        timeout=15
    )
    forecast.raise_for_status()
    f = forecast.json()
    hourly = f.get("hourly", {})

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rainp = hourly.get("precipitation_probability", [])
    wind = hourly.get("wind_speed_10m", [])

    if not times:
        return "Weather data is temporarily unavailable. Try again in a bit."

    # Pick the “best” hour: lowest rain prob, then lower wind, then moderate temp
    best_i = 0
    best_score = None
    for i in range(len(times)):
        score = (rainp[i] if i < len(rainp) else 50) * 2 + (wind[i] if i < len(wind) else 10)
        if best_score is None or score < best_score:
            best_score = score
            best_i = i

    t = times[best_i]
    temp = temps[best_i] if best_i < len(temps) else None
    rp = rainp[best_i] if best_i < len(rainp) else None
    ws = wind[best_i] if best_i < len(wind) else None

    return (
        f"Outdoor reset plan for {place}:\n"
        f"- Best window today looks like around **{t}**.\n"
        f"- Conditions: ~{temp}°C, rain chance ~{rp}%, wind ~{ws} km/h.\n\n"
        "Tiny plan:\n"
        "1) Keep it short (15–30 min) and aim for regulation, not entertainment.\n"
        "2) Script to your kid: “We’re going outside to help our bodies calm down. I’ll help you.”\n"
        "3) If they resist: “You’re upset. I’m still helping. We’ll go together.”"
    )