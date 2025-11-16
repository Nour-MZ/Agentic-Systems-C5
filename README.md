# Map Agents with OpenAI Agents SDK & MCP-style Map Servers

This project implements two custom "map servers" using the OpenAI Agents SDK in Python.  
Each server is exposed to the agent as a set of tools, following Model Context Protocol (MCP) style conventions (ServerParams describing commands/endpoints).

## Map Servers

### 1. `osm_server` (OpenStreetMap / Nominatim / Overpass)

Operations (tools):
- `osm_geocode` — forward geocoding using Nominatim.
- `osm_reverse_geocode` — reverse geocoding using Nominatim.
- `osm_search_poi` — point-of-interest search around a coordinate using Overpass API.

### 2. `osrm_server` (Open Source Routing Machine demo server)

Operations (tools):
- `osrm_route_driving` — driving route between two coordinates.
- `osrm_route_cycling` — cycling route between two coordinates.
- `osrm_nearest_road` — snap a coordinate to the nearest road.

All tools are decorated with `@function_tool` from the Agents SDK and registered on a single map assistant agent.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
export HUGGINGFACEHUB_API_TOKEN="YOUR_API_KEY_HERE"

OR Hardcode the key in the agent_app.py file
