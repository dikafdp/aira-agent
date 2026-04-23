import requests
import datetime
import re
from state import AgentState

BASE_WEBHOOK_URL = "https://flow.eraenterprise.id/webhook"

def check_schedule(state: AgentState):
    payload = {
        "dokter_id": state.get("doctor_name", ""), 
        "poli_id": state.get("poli_name", ""),
        "tanggal": state.get("booking_date", "")
    }
    
    try:
        url = f"{BASE_WEBHOOK_URL}/Jdokter-Refreshdb-copy"
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            try:
                data = res.json()
            except ValueError:
                return {"final_answer": "Maaf, format balasan dari server jadwal tidak valid/kosong."}
            
            if isinstance(data, dict) and "error" in data:
                return {"final_answer": f"Mohon maaf: {data['error']}\nSilakan sebutkan nama poli, dokter, dan tanggalnya dengan jelas."}
            
            if data:
                return {"final_answer": f"🏥 Jadwal Dokter tersedia:\n{data}"}
            else:
                return {"final_answer": "Mohon maaf, dokter sedang tidak tersedia atau tidak ada jadwal di hari tersebut."}
        else:
            return {"final_answer": f"Gagal mengecek jadwal (Error {res.status_code})."}
    except Exception as e:
        return {"final_answer": f"Terjadi kesalahan sistem: {str(e)}"}

def book_appointment(state: AgentState):
    doctor = state.get("doctor_name", "")
    poli = state.get("poli_name", "")
    patient = state.get("patient_name", "")
    date = state.get("booking_date", "")
    time = state.get("booking_time", "-")
    pembayaran = state.get("metode_pembayaran", "Umum")

    if not doctor or not poli or not patient or not date:
        return {
            "final_answer": (
                "Mohon lengkapi data booking Anda:\n"
                "- Nama Poli\n"
                "- Nama Dokter\n"
                "- Tanggal & Jam\n"
                "- Nama Pasien\n\n"
                "Silakan ulangi permintaan dengan data yang lengkap."
            )
        }

    payload = {
        "doctor_name": doctor,  
        "poli_name": poli,      
        "patient_name": patient,
        "booking_date": date,
        "booking_time": time,
        "metode_pembayaran": pembayaran
    }
    
    try:
        url = f"{BASE_WEBHOOK_URL}/buat-janji-copy"
        res = requests.post(url, json=payload)
        
        if res.status_code in [200, 400, 409]:
            try:
                raw_data = res.json()
            except ValueError:
                return {"final_answer": "Maaf, server merespons dengan format yang tidak dikenali."}

            data = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
            if not isinstance(data, dict):
                data = {}

            insert_id = data.get("insertId")
            appt_id = data.get("appointment_id")
            # FIX: Mengambil nilai 'success' atau 'ok' dari JSON n8n
            is_success = data.get("success", data.get("ok"))
            status_code = data.get("statusCode", 200)

            # FIX: Menghapus pengecekan strict insert_id yang memicu false negative
            if res.status_code in [400, 409] or status_code in [400, 409] or is_success is False:
                return {
                    "final_answer": (
                        f"Mohon maaf, jadwal dr. {doctor} di Poli {poli} untuk tanggal {date} jam {time} sudah terisi oleh pasien lain atau jadwal bentrok.\n\n"
                        f"Saran: Silakan pilih jam lain, atau cek ketersediaan dokter lain di Poli {poli}."
                    )
                }

            if is_success or status_code == 200 or insert_id or appt_id:
                return {
                    "final_answer": (
                        f"✅ Booking berhasil terdaftar.\n\n"
                        f"Detail:\n"
                        f"- Pasien: {patient}\n"
                        f"- Dokter: dr. {doctor}\n"
                        f"- Poli: {poli}\n"
                        f"- Tanggal: {date}\n"
                        f"- Jam: {time}\n"
                        f"- Pembayaran: {pembayaran}\n\n"
                        f"Terima kasih."
                    )
                }
                
            return {"final_answer": "Permintaan booking telah dikirim ke sistem."}
        else:
            return {"final_answer": f"Gagal menghubungi server rumah sakit (Error Code: {res.status_code})."}
            
    except Exception as e:
        return {"final_answer": f"Terjadi kesalahan sistem internal: {str(e)}"}

def get_clinic_info(state: AgentState):
    try:
        url = f"{BASE_WEBHOOK_URL}/data-poli-api-copy"
        res = requests.get(url) 
        
        if res.status_code == 200:
            try:
                data = res.json()
            except ValueError:
                return {"final_answer": "Maaf, server n8n mengembalikan data kosong saat mencari daftar poli."}
            
            if isinstance(data, list) and len(data) > 0:
                poli_list = "\n".join([f"⚕️ {item.get('ref_layanan_nama', 'Poli')}" for item in data])
                return {"final_answer": f"🏥 Berikut adalah daftar poli yang tersedia di RSUD kami:\n\n{poli_list}"}
            else:
                return {"final_answer": "Maaf, saat ini daftar poli tidak ditemukan."}
        else:
            return {"final_answer": f"Gagal mengambil daftar poli (Error {res.status_code})."}
            
    except Exception as e:
        return {"final_answer": f"Terjadi kesalahan saat mengambil info RSUD: {str(e)}"}

def get_doctor_list(state: AgentState):
    poli_name = state.get("poli_name", "")
    if not poli_name:
        return {"final_answer": "Mohon sebutkan nama poli untuk melihat daftar dokternya. (Contoh: 'lihat dokter di poli gigi')"}
        
    search_keyword = re.sub(r'(?i)\b(poli|RSUD)\b', '', poli_name).strip()
        
    try:
        url = f"{BASE_WEBHOOK_URL}/dokterAPI-copy"
        res = requests.post(url, json={"poli_name": search_keyword}) 
        
        if res.status_code == 200:
            try:
                raw_data = res.json()
            except ValueError:
                return {"final_answer": f"Maaf, tidak ada dokter yang ditemukan di Poli {poli_name} atau database kosong."}

            actual_doctors = []

            if isinstance(raw_data, list) and len(raw_data) > 0:
                if "data" in raw_data[0]:
                    actual_doctors = raw_data[0]["data"]
                else:
                    actual_doctors = raw_data 
            
            elif isinstance(raw_data, dict):
                actual_doctors = raw_data.get("data", [])
            
            if isinstance(actual_doctors, list) and len(actual_doctors) > 0:
                doc_list = "\n".join([f"👨‍⚕️ dr. {item.get('nama_dokter', '')}" for item in actual_doctors if item.get('nama_dokter')])
                
                return {"final_answer": f"🏥 Berikut adalah daftar dokter di Poli {poli_name}:\n\n{doc_list}\n\nSilakan sebutkan nama dokter untuk melihat jadwalnya!"}
            else:
                return {"final_answer": f"Maaf, saat ini tidak ditemukan dokter untuk poli {poli_name}."}
        else:
            return {"final_answer": f"Gagal mengambil daftar dokter (Error {res.status_code})."}
            
    except Exception as e:
        return {"final_answer": f"Terjadi kesalahan saat mengambil data dokter: {str(e)}"}

def get_doctor_schedule_list(state: AgentState):
    doctor_name = state.get("doctor_name", "")
    if not doctor_name:
        return {"final_answer": "Mohon sebutkan nama dokter untuk melihat jadwalnya. (Contoh: 'cek jadwal dr. DWI KAMARATIH')"}
        
    try:
        url = f"{BASE_WEBHOOK_URL}/get-schedule-list"
        res = requests.post(url, json={"doctor_name": doctor_name})
        
        if res.status_code == 200:
            try:
                data = res.json()
            except ValueError:
                return {"final_answer": f"Maaf, jadwal untuk dr. {doctor_name} tidak ditemukan di database server."}
                
            if isinstance(data, list) and len(data) > 0:
                days_map = {'senin':0, 'selasa':1, 'rabu':2, 'kamis':3, 'jumat':4, 'sabtu':5, 'minggu':6}
                months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agt', 'Sep', 'Okt', 'Nov', 'Des']
                today = datetime.date.today()
                
                valid_schedules = []
                
                for item in data:
                    hari = item.get('hari_praktek', '').strip()
                    jam_mulai = str(item.get('jam_praktek_mulai', ''))
                    jam_akhir = str(item.get('jam_praktek_akhir', ''))
                    poli = item.get('poli', '')
                    
                    if jam_mulai == '00:00:00' and jam_akhir == '00:00:00':
                        continue
                        
                    jm = jam_mulai[:5] if len(jam_mulai) >= 5 else jam_mulai
                    ja = jam_akhir[:5] if len(jam_akhir) >= 5 else jam_akhir
                    
                    target_day = days_map.get(hari.lower())
                    hari_str = hari
                    
                    if target_day is not None:
                        days_ahead = target_day - today.weekday()
                        if days_ahead < 0:
                            days_ahead += 7 
                            
                        date1 = today + datetime.timedelta(days=days_ahead)
                        date2 = date1 + datetime.timedelta(days=7) 
                        
                        d1_str = f"{date1.day} {months[date1.month]}"
                        d2_str = f"{date2.day} {months[date2.month]}"
                        
                        hari_str = f"{hari} (Tgl {d1_str} & {d2_str})"
                        
                    valid_schedules.append(f"📅 {hari_str}: 🕒 {jm} - {ja} (Poli: {poli})")
                
                if valid_schedules:
                    sched_list = "\n".join(valid_schedules)
                    return {"final_answer": f"🏥 Berikut adalah jadwal praktek dr. {doctor_name}:\n\n{sched_list}\n\nSilakan tentukan tanggal dan jam jika Anda ingin melakukan booking!"}
                else:
                    return {"final_answer": f"Maaf, saat ini dr. {doctor_name} belum memiliki jadwal praktek yang aktif/tersedia."}
            else:
                return {"final_answer": f"Maaf, tidak ditemukan jadwal praktek untuk dr. {doctor_name}."}
        else:
            return {"final_answer": f"Gagal mengambil jadwal (Error {res.status_code})."}
            
    except Exception as e:
        return {"final_answer": f"Terjadi kesalahan saat mengambil jadwal: {str(e)}"}