# agent_app.py

"""
Interactive CLI demo: Map Assistant using Hugging Face Inference + your map servers.

- Uses huggingface_hub.InferenceClient instead of OpenAI/Gemini.
- Calls your map server implementation functions as "tools".
- One-step tool use: LLM chooses a tool, we call it, then LLM explains result.

Usage (recommended):
    PowerShell:

        py agent_app.py
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Callable

from huggingface_hub import InferenceClient

from map_servers.osm_server import (
    osm_geocode_impl,
    osm_reverse_geocode_impl,
    osm_search_poi_impl,
)
from map_servers.osrm_server import (
    osrm_route_driving_impl,
    osrm_route_cycling_impl,
    osrm_nearest_road_impl,
)

# ----------------------------------------------------------------------
# 1. Configure Hugging Face Inference LLM
# ----------------------------------------------------------------------

# OPTION A (recommended): read from environment variable
HF_TOKEN = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

# OPTION B (for local testing only): hard-code here


if not HF_TOKEN:
    raise RuntimeError(
        "Please set HUGGINGFACEHUB_API_TOKEN as an environment variable or "
        "hard-code it in agent_app.py before running."
    )

# Choose a chat-capable model – adjust if needed.
# This is just an example; any chat model supported by HF Inference Providers works.
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

client = InferenceClient(api_key=HF_TOKEN)


def _hf_chat(messages: list[Dict[str, str]], max_tokens: int = 512) -> str:
    """
    Call Hugging Face chat completion API and return the assistant text.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    """
    completion = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        max_tokens=max_tokens,
    )
    # OpenAI-style output: choices[0].message.content
    return completion.choices[0].message.content


# ----------------------------------------------------------------------
# 2. Tool registry: names -> description + Python callables
# ----------------------------------------------------------------------

def _tool_schema() -> Dict[str, Dict[str, Any]]:
    """
    Describe tools in natural language + argument info.
    This is what the LLM sees when deciding which tool to call.
    """
    return {
        "osm_geocode": {
            "description": "Forward geocode a free-text place or address using OpenStreetMap Nominatim.",
            "args": {
                "query": "string (required) - address or place name, e.g. 'Berlin, Germany'.",
                "limit": "integer (optional, default=5) - max number of results (1-10).",
            },
        },
        "osm_reverse_geocode": {
            "description": "Reverse geocode coordinates to an address using OpenStreetMap Nominatim.",
            "args": {
                "lat": "float (required) - latitude in decimal degrees.",
                "lon": "float (required) - longitude in decimal degrees.",
                "zoom": "integer (optional, default=18) - detail level (3-18).",
            },
        },
        "osm_search_poi": {
            "description": "Search points-of-interest (POI) around a coordinate using Overpass API.",
            "args": {
                "lat": "float (required) - center latitude.",
                "lon": "float (required) - center longitude.",
                "radius_m": "integer (optional, default=500) - radius in meters (50-5000).",
                "key": "string (optional, default='amenity') - OSM tag key.",
                "value": "string (optional, default='restaurant') - OSM tag value.",
                "limit": "integer (optional, default=20) - max results (1-50).",
            },
        },
        "osrm_route_driving": {
            "description": "Get a driving route between two coordinates using OSRM.",
            "args": {
                "start_lat": "float (required)",
                "start_lon": "float (required)",
                "end_lat": "float (required)",
                "end_lon": "float (required)",
            },
        },
        "osrm_route_cycling": {
            "description": "Get a cycling route between two coordinates using OSRM.",
            "args": {
                "start_lat": "float (required)",
                "start_lon": "float (required)",
                "end_lat": "float (required)",
                "end_lon": "float (required)",
            },
        },
        "osrm_nearest_road": {
            "description": "Snap a coordinate to the nearest road using OSRM.",
            "args": {
                "lat": "float (required)",
                "lon": "float (required)",
                "profile": "string (optional, default='driving') - OSRM profile (driving, bike, foot).",
            },
        },
    }


TOOL_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "osm_geocode": osm_geocode_impl,
    "osm_reverse_geocode": osm_reverse_geocode_impl,
    "osm_search_poi": osm_search_poi_impl,
    "osrm_route_driving": osrm_route_driving_impl,
    "osrm_route_cycling": osrm_route_cycling_impl,
    "osrm_nearest_road": osrm_nearest_road_impl,
}


# ----------------------------------------------------------------------
# 3. Agent logic: decide tool vs direct answer, then explain
# ----------------------------------------------------------------------

def build_system_prompt() -> str:
    tools_desc = _tool_schema()
    tools_text_parts = []
    for name, spec in tools_desc.items():
        tools_text_parts.append(
            f"- {name}:\n"
            f"  description: {spec['description']}\n"
            f"  args: {json.dumps(spec['args'], indent=2)}"
        )
    tools_text = "\n".join(tools_text_parts)

    return (
        "You are a geospatial assistant that can call a set of tools (map servers).\n"
        "Tools available:\n"
        f"{tools_text}\n\n"
        "You MUST decide if you need to call a tool.\n"
        "If you need a tool, respond ONLY with a JSON object of the form:\n"
        '{\n'
        '  \"tool\": \"<tool_name>\",\n'
        '  \"args\": { ... }\n'
        '}\n'
        "where <tool_name> is one of the tools above, and args contains only simple JSON types.\n"
        "If you can answer directly without tools (e.g., conceptual explanation), respond ONLY with:\n"
        '{ \"answer\": \"<your natural language answer>\" }\n'
        "Do not add any extra text outside the JSON. The JSON must be the entire response."
    )


def ask_llm_for_tool_or_answer(user_message: str) -> Dict[str, Any]:
    """
    Step 1: ask the LLM whether to call a tool, and which one.

    Returns parsed JSON dict, either:
      { "answer": "..." }
    or
      { "tool": "<name>", "args": { ... } }
    """
    system_prompt = build_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    text = _hf_chat(messages, max_tokens=512).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: wrap whatever the model said as a direct answer
        data = {"answer": text}

    return data


def ask_llm_to_explain_result(
    user_message: str,
    tool_name: str,
    args: Dict[str, Any],
    result: Any,
) -> str:
    """
    Step 3: after calling the tool, ask the LLM to explain the result.
    """
    tool_desc = _tool_schema().get(tool_name, {})
    prompt = (
        "You are a geospatial assistant. A tool has been called on behalf of the user.\n\n"
        f"User message:\n{user_message}\n\n"
        f"Tool used: {tool_name}\n"
        f"Tool description: {tool_desc.get('description', '')}\n"
        f"Arguments: {json.dumps(args, indent=2)}\n\n"
        f"Raw tool result (JSON):\n{json.dumps(result, indent=2)}\n\n"
        "Now explain the result to the user in clear natural language. "
        "Summarize key distances, durations, coordinates, and any useful POI details. "
        "Do not show the raw JSON, just a human-readable explanation."
    )

    messages = [
        {"role": "system", "content": "You are a helpful geospatial assistant."},
        {"role": "user", "content": prompt},
    ]

    return _hf_chat(messages, max_tokens=512).strip()


def handle_user_message(user_message: str) -> str:
    """
    Full agent flow for one user message:
    1. Ask LLM whether to use a tool or answer directly.
    2. If tool: run the Python function, then ask LLM to explain result.
    """
    decision = ask_llm_for_tool_or_answer(user_message)

    # Direct answer path
    if "answer" in decision and "tool" not in decision:
        return decision["answer"]

    # Tool path
    tool_name = decision.get("tool")
    args = decision.get("args", {}) or {}

    if tool_name not in TOOL_FUNCTIONS:
        return f"I tried to call an unknown tool '{tool_name}'. Please refine your request."

    tool_fn = TOOL_FUNCTIONS[tool_name]

    try:
        result = tool_fn(**args)
    except TypeError as e:
        return f"There was an error calling tool '{tool_name}' with arguments {args}: {e}"
    except Exception as e:
        return f"Tool '{tool_name}' failed with an exception: {e}"

    return ask_llm_to_explain_result(user_message, tool_name, args, result)


# ----------------------------------------------------------------------
# 4. Simple REPL
# ----------------------------------------------------------------------

def main() -> None:
    print(f"Map Assistant (Hugging Face model: {MODEL_ID})")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return

        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye.")
            return

        if not user_input:
            continue

        answer = handle_user_message(user_input)
        print("\nAssistant:\n")
        print(answer)
        print("\n---\n")


if __name__ == "__main__":
    main()
