import requests
from state import AgentState

def execute_weather(state: AgentState):
    lokasi = state.get("location", "Jakarta")
    try:
        res = requests.get(f"https://wttr.in/{lokasi}?format=4")
        res.encoding = 'utf-8'

        if res.status_code == 200:
            answer = f"☁️ Cuaca:\n{res.text}"
        else:
            answer = "Gagal ambil cuaca"
    except:
        answer = "Error cuaca"

    return {"final_answer": answer}