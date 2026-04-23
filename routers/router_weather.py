import re
from state import AgentState

def _extract_location(user_input: str) -> str:
    text = user_input.strip()

    match = re.search(r"\bdi\s+(.+)", text, re.IGNORECASE)
    
    if match:
        location = match.group(1).strip(" ?!.,:")
    else:
        match_cuaca = re.search(r"\bcuaca\s+(.+)", text, re.IGNORECASE)
        if match_cuaca:
            location = match_cuaca.group(1).strip(" ?!.,:")
        else:
            return "Jakarta"

    location = re.split(
        r"\b(hari ini|besok|sekarang|minggu ini|dong|ya|please|tolong)\b",
        location,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0].strip(" ,.-")

    return location if location else "Jakarta"

def analyze_weather_intent(state: AgentState):
    user_input = state.get("user_input", "")
    location = _extract_location(user_input)

    return {
        "action": "get_weather",
        "location": location,
        "search_query": "",
        "image_prompt": "",
        "final_answer": ""
    }