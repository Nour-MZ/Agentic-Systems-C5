# tests/test_osm_server.py

"""
Very lightweight tests / demo calls for OSM server tools.

Here we call the pure implementation functions directly, not the tool-wrapped
objects from Agents SDK, to keep tests simple.
"""

from __future__ import annotations

from pprint import pprint

from map_servers.osm_server import (
    osm_geocode_impl,
    osm_reverse_geocode_impl,
    osm_search_poi_impl,
)


def demo_geocode() -> None:
    print("=== OSM Geocode Demo ===")
    results = osm_geocode_impl("Berlin, Germany", limit=3)
    pprint(results)


def demo_reverse_geocode() -> None:
    print("=== OSM Reverse Geocode Demo ===")
    # Approximate coordinates for Brandenburg Gate
    result = osm_reverse_geocode_impl(
        lat=52.5162746,
        lon=13.3777041,
        zoom=18,
    )
    pprint(result)


def demo_poi() -> None:
    print("=== OSM POI Search Demo ===")
    # Near Brandenburg Gate, search for cafes
    results = osm_search_poi_impl(
        lat=52.5162746,
        lon=13.3777041,
        radius_m=500,
        key="amenity",
        value="cafe",
        limit=5,
    )
    pprint(results)


if __name__ == "__main__":
    demo_geocode()
    print()
    demo_reverse_geocode()
    print()
    demo_poi()
