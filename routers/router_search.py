import re
from state import AgentState


def _extract_search_query(user_input: str) -> str:
    query = re.sub(
        r"^(tolong\s+)?(tolong carikan|carikan|coba cari|cari|search|browse)\s*",
        "",
        user_input.strip(),
        flags=re.IGNORECASE
    ).strip(" ?!.,:")

    return query if query else user_input.strip()


def _detect_search_mode(user_input: str) -> str:
    text = user_input.lower()

    link_keywords = [
        "link", "tautan", "url", "sumber", "referensi",
        "website", "web", "laman", "artikel asli"
    ]

    news_keywords = [
        "carikan berita", "berita terkini", "berita terbaru",
        "headline", "daftar berita", "kumpulan berita",
        "berita hari ini"
    ]

    if any(keyword in text for keyword in link_keywords):
        return "links"

    if any(keyword in text for keyword in news_keywords):
        return "news"

    return "answer"


def analyze_search_intent(state: AgentState):
    user_input = state.get("user_input", "").strip()
    query = _extract_search_query(user_input)
    mode = _detect_search_mode(user_input)

    return {
        "action": "web_search",
        "location": "",
        "search_query": query,
        "search_mode": mode,
        "search_results": [],
        "image_prompt": "",
        "final_answer": ""
    }