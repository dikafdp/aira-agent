from typing import TypedDict

class AgentState(TypedDict, total=False):
    user_input: str
    domain: str        # medical, weather, search, image, chat
    action: str
    title: str
    content: str
    final_answer: str

    # --- Fitur General ---
    location: str
    search_query: str
    search_mode: str   # answer | news | links
    search_results: list
    image_prompt: str
    image_url: str

    # --- Fitur Medical ---
    doctor_name: str
    poli_name: str
    booking_date: str
    booking_time: str
    patient_name: str
    metode_pembayaran: str