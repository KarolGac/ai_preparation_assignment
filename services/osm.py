"""OpenStreetMap integration: geocoding via Nominatim, venue search via Overpass."""

import math

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Nominatim/Overpass usage policy requires a descriptive, non-generic User-Agent.
HEADERS = {"User-Agent": "hhs-horeca-competition-lens/0.1 (student assignment)"}

CATEGORY_TAGS = {
    "cafe": ("amenity", "cafe"),
    "restaurant": ("amenity", "restaurant"),
    "hotel": ("tourism", "hotel"),
}

RADIUS_METERS = 1000

# Simple in-process cache so repeated identical lookups during testing don't
# hammer the public Nominatim/Overpass endpoints.
_geocode_cache: dict[str, tuple[float, float]] = {}
_overpass_cache: dict[tuple[float, float, str], list[dict]] = {}


class OsmLookupError(Exception):
    """Raised when geocoding or venue search fails."""


def geocode_address(address: str) -> tuple[float, float]:
    """Resolve a free-text address to (lat, lon) using Nominatim."""
    cache_key = address.strip().lower()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    params = {"q": address, "format": "json", "limit": 1}
    response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    results = response.json()

    if not results:
        raise OsmLookupError(f"No location found for address: {address!r}")

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    _geocode_cache[cache_key] = (lat, lon)
    return lat, lon


def find_nearby_venues(lat: float, lon: float, category: str) -> list[dict]:
    """Query Overpass for mapped venues of the given category within RADIUS_METERS."""
    if category not in CATEGORY_TAGS:
        raise ValueError(f"Unknown category: {category!r}")

    cache_key = (round(lat, 5), round(lon, 5), category)
    if cache_key in _overpass_cache:
        return _overpass_cache[cache_key]

    tag_key, tag_value = CATEGORY_TAGS[category]
    query = f"""
    [out:json][timeout:25];
    (
      node["{tag_key}"="{tag_value}"](around:{RADIUS_METERS},{lat},{lon});
      way["{tag_key}"="{tag_value}"](around:{RADIUS_METERS},{lat},{lon});
    );
    out center tags;
    """

    response = requests.post(
        OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=30
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])

    venues = []
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip unnamed/poorly mapped entries, not useful to the user

        if element["type"] == "node":
            venue_lat, venue_lon = element["lat"], element["lon"]
        else:
            center = element.get("center")
            if not center:
                continue
            venue_lat, venue_lon = center["lat"], center["lon"]

        distance = haversine_distance_m(lat, lon, venue_lat, venue_lon)
        venues.append(
            {
                "name": name,
                "type": tags.get(tag_key, category),
                "website": tags.get("website") or tags.get("contact:website"),
                "distance_m": distance,
            }
        )

    venues.sort(key=lambda v: v["distance_m"])
    _overpass_cache[cache_key] = venues
    return venues


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance between two lat/lon points, in meters."""
    r = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c
