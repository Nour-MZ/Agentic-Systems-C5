# tests/test_osrm_server.py

"""
Very lightweight tests / demo calls for OSRM server tools.

We again call the pure implementation functions directly.
"""

from __future__ import annotations

from pprint import pprint

from map_servers.osrm_server import (
    osrm_route_driving_impl,
    osrm_route_cycling_impl,
    osrm_nearest_road_impl,
)


def demo_route_driving() -> None:
    print("=== OSRM Driving Route Demo ===")
    # Berlin Brandenburg Airport -> Alexanderplatz (approx.)
    result = osrm_route_driving_impl(
        start_lat=52.3667,
        start_lon=13.5033,
        end_lat=52.5219,
        end_lon=13.4132,
    )
    pprint(result)


def demo_route_cycling() -> None:
    print("=== OSRM Cycling Route Demo ===")
    # Short route in central Berlin
    result = osrm_route_cycling_impl(
        start_lat=52.5200,
        start_lon=13.4050,
        end_lat=52.5246,
        end_lon=13.4098,
    )
    pprint(result)


def demo_nearest_road() -> None:
    print("=== OSRM Nearest Road Demo ===")
    # Near the Eiffel Tower
    result = osrm_nearest_road_impl(
        lat=48.8582602,
        lon=2.2944991,
        profile="driving",
    )
    pprint(result)


if __name__ == "__main__":
    demo_route_driving()
    print()
    demo_route_cycling()
    print()
    demo_nearest_road()
