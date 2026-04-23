import re
from state import AgentState

def classify_domain(state: AgentState):
    user_input = state.get("user_input", "").strip()
    text_lower = user_input.lower()

    if not user_input:
        return {
            "domain": "chat",
            "final_answer": "Pesan kosong. Silakan tulis kebutuhan Anda."
        }

    def contains_keyword(text, keywords):
        pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
        return bool(re.search(pattern, text))

    # ----------------------------
    # PRIORITAS 1: Image Generation (Paling spesifik kalimatnya)
    # ----------------------------
    image_keywords = [
        "buat gambar", "bikin gambar", "generate gambar", "buatkan gambar",
        "gambarin", "lukis", "ilustrasikan", "buat ilustrasi", 
        "stable diffusion", "stabble difusion", "image generator", "bikinin gambar",
        "tolong gambar", "sketsa", "potret", "gambarkan", "bikin ilustrasi", "flux"
    ]
    if contains_keyword(text_lower, image_keywords) or text_lower.startswith("gambar"):
        return {"domain": "image"}

    # ----------------------------
    # PRIORITAS 2: Medical
    # ----------------------------
    medical_keywords = [
        "dokter", "poli", "jadwal", "booking", "janji", "buat janji",
        "klinik", "rsud", "pasien", "bpjs", "rawat jalan", "pendaftaran",
        "spesialis", "periksa", "berobat", "antrian", "antrean", "nomor antrean",
        "rujukan", "igd", "ugd", "rawat inap", "kamar", "obat", "resep",
        "tebus obat", "sakit", "keluhan", "batal janji", "kanaya", "registrasi"
    ]
    if contains_keyword(text_lower, medical_keywords):
        return {"domain": "medical"}

    # ----------------------------
    # PRIORITAS 3: Weather
    # ----------------------------
    weather_keywords = [
        "cuaca", "suhu", "hujan", "panas", "mendung", "gerimis", "badai", 
        "weather", "forecast", "prakiraan", "iklim", "cerah", "banjir",
        "bmkg", "derajat", "celcius", "celsius"
    ]
    if contains_keyword(text_lower, weather_keywords):
        return {"domain": "weather"}

    # ----------------------------
    # PRIORITAS 4: Search / Browsing
    # ----------------------------
    search_keywords = [
        "cari", "search", "browse", "berita", "informasi", "artikel",
        "info", "siapa", "apa itu", "apa", "kapan", "googling", "searxng",
        "dimana", "kenapa", "bagaimana", "jelaskan", "tolong cari", "carikan",
        "cariin", "pengertian", "definisi", "tolong jelaskan", "maksud dari",
        "tolong carikan"
    ]
    is_question = text_lower.endswith("?")
    
    if contains_keyword(text_lower, search_keywords) or is_question:
        return {"domain": "search"}

    # ----------------------------
    # Default: Chat
    # ----------------------------
    greetings = [
        "halo", "hai", "hi", "selamat pagi", "selamat siang", "selamat sore", 
        "selamat malam", "ping", "p", "assalamualaikum", "bot", 
        "aira", "test", "tes", "halo aira"
    ]
    if any(text_lower.startswith(g) for g in greetings):
        return {
            "domain": "chat",
            "final_answer": "Halo! Aira siap membantu untuk pendaftaran jadwal dokter, cek cuaca, browsing informasi, hingga membuat gambar. Ada yang bisa dibantu?"
        }

    return {
        "domain": "chat",
        "final_answer": "Maaf, Aira kurang paham. Anda bisa meminta Aira untuk cek jadwal dokter, melihat cuaca, mencari informasi, atau membuat gambar."
    }