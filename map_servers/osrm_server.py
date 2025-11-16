# map_servers/osrm_server.py

from __future__ import annotations

import logging
from typing import Any, Dict

import requests
from agents import function_tool

from .base import ServerParams

logger = logging.getLogger(__name__)

OSRM_PARAMS = ServerParams(
    name="osrm_demo",
    base_url="https://router.project-osrm.org",
    description="OSRM public demo server for routing.",
    commands={
        "route": "/route/v1",      # /route/v1/{profile}/{coordinates}
        "nearest": "/nearest/v1",  # /nearest/v1/{profile}/{coordinate}
    },
)


def _osrm_headers() -> Dict[str, str]:
    return {
        "User-Agent": "map-agents-assignment/1.0 (student-project)",
        "Accept": "application/json",
    }


def _format_coords(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> str:
    """
    OSRM expects "lon,lat;lon,lat".
    """
    return f"{start_lon},{start_lat};{end_lon},{end_lat}"


def _request_route(profile: str, coords: str) -> Dict[str, Any]:
    url = f"{OSRM_PARAMS.base_url}{OSRM_PARAMS.commands['route']}/{profile}/{coords}"
    params = {
        "overview": "simplified",
        "geometries": "geojson",
        "steps": "true",
        "alternatives": "false",
    }
    logger.debug("Calling OSRM route: %s %s", url, params)
    resp = requests.get(url, params=params, headers=_osrm_headers(), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data


# ------------------------
# Pure implementation APIs
# ------------------------

def osrm_route_driving_impl(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> Dict[str, Any]:
    """
    Get a driving route between two coordinates using OSRM.
    """
    coords = _format_coords(start_lat, start_lon, end_lat, end_lon)
    data = _request_route("driving", coords)

    if not data.get("routes"):
        raise RuntimeError(f"OSRM returned no routes: {data}")

    route = data["routes"][0]
    distance_km = route["distance"] / 1000.0
    duration_min = route["duration"] / 60.0

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "summary": route.get("summary", ""),
        "geometry": route.get("geometry"),  # GeoJSON LineString
    }


def osrm_route_cycling_impl(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> Dict[str, Any]:
    """
    Get a cycling route between two coordinates using OSRM.
    """
    coords = _format_coords(start_lat, start_lon, end_lat, end_lon)
    # Depending on server profile naming, you might need "bike" or "cycling".
    profile = "bike"
    data = _request_route(profile, coords)

    if not data.get("routes"):
        raise RuntimeError(f"OSRM returned no routes for cycling: {data}")

    route = data["routes"][0]
    distance_km = route["distance"] / 1000.0
    duration_min = route["duration"] / 60.0

    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "summary": route.get("summary", ""),
        "geometry": route.get("geometry"),
    }


def osrm_nearest_road_impl(lat: float, lon: float, profile: str = "driving") -> Dict[str, Any]:
    """
    Snap a coordinate to the nearest road using OSRM.
    """
    url = f"{OSRM_PARAMS.base_url}{OSRM_PARAMS.commands['nearest']}/{profile}/{lon},{lat}"
    params = {"number": 1}
    logger.debug("Calling OSRM nearest: %s %s", url, params)

    resp = requests.get(url, params=params, headers=_osrm_headers(), timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("waypoints"):
        raise RuntimeError(f"OSRM returned no waypoints: {data}")

    wp = data["waypoints"][0]
    snapped_lon, snapped_lat = wp["location"]
    distance_m = wp.get("distance")

    return {
        "snapped_lat": float(snapped_lat),
        "snapped_lon": float(snapped_lon),
        "distance_m": float(distance_m) if distance_m is not None else None,
    }


# ------------------------
# Tool-wrapped APIs
# ------------------------

@function_tool
def osrm_route_driving(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> Dict[str, Any]:
    """Tool wrapper for osrm_route_driving_impl."""
    return osrm_route_driving_impl(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
    )


@function_tool
def osrm_route_cycling(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> Dict[str, Any]:
    """Tool wrapper for osrm_route_cycling_impl."""
    return osrm_route_cycling_impl(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
    )


@function_tool
def osrm_nearest_road(lat: float, lon: float, profile: str = "driving") -> Dict[str, Any]:
    """Tool wrapper for osrm_nearest_road_impl."""
    return osrm_nearest_road_impl(lat=lat, lon=lon, profile=profile)
