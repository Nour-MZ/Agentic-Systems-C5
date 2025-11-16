# ui_app.py

"""
Gradio web UI for your Map Assistant (Hugging Face + custom map servers).

This reuses the LLM + tool logic from agent_app.handle_user_message
and exposes it as a chat interface in the browser.

Usage:
    PowerShell:
        $env:HUGGINGFACEHUB_API_TOKEN = "hf_XXXXXXXXXXXXXXXXXXXXXXXX"
        py ui_app.py

Then open the local URL that Gradio prints (usually http://127.0.0.1:7860).
"""

from __future__ import annotations

import gradio as gr

from agent_app import handle_user_message, MODEL_ID  # reuse your existing logic


def chat_fn(message: str, history: list[tuple[str, str]]) -> str:
    """
    Gradio ChatInterface callback.

    message: latest user message
    history: list of (user, assistant) message pairs (we don't need it here)
    """
    # Simply delegate to your agent logic
    return handle_user_message(message)


def main() -> None:
    demo = gr.ChatInterface(
        fn=chat_fn,
        title=f"Map Assistant (Model: {MODEL_ID})",
        description=(
            "Ask for geocoding, reverse geocoding, POI search, driving/cycling routes, "
            "or nearest road queries. The assistant uses OpenStreetMap, Overpass, and "
            "OSRM tools under the hood."
        ),
        textbox=gr.Textbox(
            placeholder="Ask something like: 'Geocode the Eiffel Tower' or 'Driving route from 52.3667,13.5033 to 52.5219,13.4132'",
            lines=2,
        ),
        theme="soft",
    )

    demo.launch()


if __name__ == "__main__":
    main()
