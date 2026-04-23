import json
import re
import datetime
from state import AgentState
from config import llm

def analyze_medical_intent(state: AgentState):
    user_input = state["user_input"]
    
    prompt = f"""Kamu adalah AI Router khusus Layanan Medis. Analisis input user dan hasilkan JSON.

TUGAS:
Baca input user dan kembalikan JSON VALID.

ATURAN:
1. Tanya jadwal dokter SECARA SPESIFIK TANGGALNYA → action="check_schedule"
2. Buat Janji/Booking → action="book_appointment"
3. Tanya DAFTAR POLI / Info RSUD → action="get_clinic_info"
4. Tanya DAFTAR DOKTER di poli tertentu → action="get_doctor_list"
5. Tanya JADWAL PRAKTEK DOKTER → action="get_doctor_schedule_list"
6. Tanya di luar layanan medis → action="chat"

FORMAT WAJIB JSON:
{{
"action": "...",
"doctor_name": "...",
"poli_name": "...",
"booking_date": "...",
"booking_time": "...",
"patient_name": "...",
"metode_pembayaran": "..."
}}

Input: {user_input}
OUTPUT JSON SAJA:
"""

    try:
        res = llm.invoke(prompt).content
        clean = res.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
    except:
        data = {"action": "chat"}

    action = data.get("action", "chat")
    text_lower = user_input.lower()

    # --- 1. OVERRIDE INTENT KATA KUNCI  ---
    if "booking" in text_lower or "janji" in text_lower:
        action = "book_appointment"
    elif any(k in text_lower for k in ["list poli", "daftar poli", "poli apa"]):
        action = "get_clinic_info"
    elif any(k in text_lower for k in ["cek dokter", "lihat dokter", "daftar dokter", "dokter di poli", "siapa dokter", "dokter poli", "nama dokter di", "list dokter"]):
        action = "get_doctor_list"
    elif "jadwal" in text_lower or "dr." in text_lower or "dokter" in text_lower:
        if action != "book_appointment": 
            action = "get_doctor_schedule_list"

    # --- 2. PEMBERSIH & PENANGKAP NAMA POLI  ---
    if action == "get_doctor_list":
        match_poli = re.search(r'(?i)poli\s+([a-zA-Z\s]+)', user_input)
        if match_poli:
            extracted_poli = match_poli.group(1).strip()
            extracted_poli = re.sub(r'(?i)\b(dokter|di|cek|lihat|daftar|untuk)\b', '', extracted_poli).strip()
            data["poli_name"] = extracted_poli
        data["doctor_name"] = ""

    # --- 3. PEMOTONG NAMA POLI UMUM ---
    pol_name = data.get("poli_name", "")
    if pol_name:
        pol_name = re.sub(r'(?i)\b(poli|klinik|rsud|dokter|di|cek)\b', '', pol_name).strip()
        data["poli_name"] = pol_name

    # --- 4. PEMOTONG GELAR DOKTER ---
    doc_name = data.get("doctor_name", "")
    if doc_name:
        doc_name = re.sub(r'(?i)^(dr\.|drg\.|dr\s|drg\s|dokter\s)', '', doc_name).strip()
        doc_name = doc_name.split(',')[0].strip()
        data["doctor_name"] = doc_name

    # --- 5. KALENDER PINTAR & KOREKSI ---
    b_date = data.get("booking_date", "")
    if "2023" in b_date or "1970" in b_date:
        data["booking_date"] = ""
        b_date = ""

    if action == "check_schedule" and not b_date:
        action = "get_doctor_schedule_list"

    if action == "book_appointment":
        today = datetime.date.today()
        if not b_date or not re.match(r'^\d{4}-\d{2}-\d{2}$', b_date):
            days_map = {'senin':0, 'selasa':1, 'rabu':2, 'kamis':3, 'jumat':4, 'sabtu':5, 'minggu':6}
            found_day = None
            for day_name, day_idx in days_map.items():
                if day_name in text_lower:
                    found_day = day_idx
                    break
            
            if found_day is not None:
                days_ahead = found_day - today.weekday()
                if days_ahead < 0:  
                    days_ahead += 7
                data["booking_date"] = (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            elif "besok" in text_lower:
                data["booking_date"] = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif "lusa" in text_lower:
                data["booking_date"] = (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            else:
                data["booking_date"] = today.strftime("%Y-%m-%d")

    return {
        "action": action, 
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "doctor_name": data.get("doctor_name", ""),
        "poli_name": data.get("poli_name", ""),
        "booking_date": data.get("booking_date", ""),
        "booking_time": data.get("booking_time", ""),
        "patient_name": data.get("patient_name", ""),
        "metode_pembayaran": data.get("metode_pembayaran", "Umum"),
        "final_answer": ""
    }