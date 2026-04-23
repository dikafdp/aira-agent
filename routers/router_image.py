import re
from state import AgentState

def _extract_image_prompt(user_input: str) -> str:
    prompt = user_input.strip()

    patterns = [
        r"^(tolong\s+)?(buat|bikin|generate|buatkan)\s+(gambar|image|ilustrasi)\s*",
        r"^(tolong\s+)?(lukis|ilustrasikan)\s*",
        r"^(tolong\s+)?(stable diffusion|stabble difusion)\s*"
    ]

    for pattern in patterns:
        prompt = re.sub(pattern, "", prompt, flags=re.IGNORECASE).strip(" ?!.,:")

    return prompt if prompt else user_input.strip()

def analyze_image_intent(state: AgentState):
    user_input = state.get("user_input", "")
    image_prompt = _extract_image_prompt(user_input)

    return {
        "action": "generate_image",
        "location": "",
        "search_query": "",
        "image_prompt": image_prompt,
        "final_answer": ""
    }