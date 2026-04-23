from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from graph import app_graph
import uuid 

app = FastAPI(title="AI Agent API - Aira Kanaya & General")

class UserRequest(BaseModel):
    message: str

hasil_jawaban = {}

def proses_latar_belakang(job_id: str, message: str):
    """Fungsi ini berjalan di belakang layar, sehingga tidak menahan koneksi API utama."""
    try:
        hasil_jawaban[job_id] = {"status": "processing"}

        result = app_graph.invoke({"user_input": message})

        hasil_jawaban[job_id] = {
            "status": "completed",
            "data": {
                "domain": result.get("domain", "chat"),
                "action": result.get("action", "chat"),
                "final_answer": result.get("final_answer", ""),
                "image_url": result.get("image_url", ""),
                "title": result.get("title", ""),
                "content": result.get("content", "")
            }
        }
    except Exception as e:

        hasil_jawaban[job_id] = {
            "status": "error",
            "error_message": str(e)
        }

@app.post("/agent")
def run_agent(req: UserRequest, background_tasks: BackgroundTasks):
    """
    Endpoint ini akan langsung membalas dalam hitungan milidetik.
    Koneksi Appsmith/n8n tidak akan pernah timeout.
    """

    job_id = str(uuid.uuid4())

    background_tasks.add_task(proses_latar_belakang, job_id, req.message)

    return {
        "status": "processing",
        "job_id": job_id,
        "pesan": "Permintaan diterima, Aira sedang mencari informasi..."
    }

@app.get("/cek-jawaban/{job_id}")
def cek_jawaban(job_id: str):
    """
    Endpoint ini digunakan oleh Appsmith/n8n untuk bertanya:
    'Apakah job_id ini sudah ada jawabannya?'
    """
    if job_id not in hasil_jawaban:
        return {"status": "not_found", "pesan": "Job ID tidak ditemukan di memori."}
    
    return hasil_jawaban[job_id]