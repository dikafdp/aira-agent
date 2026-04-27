import os
import sqlite3
import json
import uuid
import time
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from graph import app_graph

app = FastAPI(title="AI Agent API - Aira Kanaya & General")

class UserRequest(BaseModel):
    message: str

DB_FILE = "jobs_memory.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (job_id TEXT PRIMARY KEY, data TEXT, timestamp REAL)''')
    conn.commit()
    conn.close()

init_db()

def update_job(job_id: str, data: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("INSERT OR REPLACE INTO jobs (job_id, data, timestamp) VALUES (?, ?, ?)", 
              (job_id, json.dumps(data), time.time()))
    conn.commit()
    conn.close()

def get_job(job_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data, timestamp FROM jobs WHERE job_id = ?", (job_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        data = json.loads(row[0])
        timestamp = row[1]

        if data.get("status") == "processing" and (time.time() - timestamp) > 300:
            return {"status": "error", "pesan": "Proses AI terhenti mendadak. Server mungkin kelebihan beban."}
        
        return data
    return None

def proses_latar_belakang(job_id: str, message: str):
    """Fungsi ini berjalan di belakang layar, memproses LangGraph."""
    try:
        update_job(job_id, {"status": "processing", "pesan": "Sedang mencari informasi..."})

        result = app_graph.invoke({"user_input": message})

        update_job(job_id, {
            "status": "completed",
            "data": {
                "domain": result.get("domain", "chat"),
                "action": result.get("action", "chat"),
                "final_answer": result.get("final_answer", "Maaf, saya tidak mendapat jawaban."),
                "image_url": result.get("image_url", ""),
                "title": result.get("title", ""),
                "content": result.get("content", "")
            }
        })
    except Exception as e:
        update_job(job_id, {
            "status": "error",
            "error_message": str(e)
        })

@app.post("/agent")
def run_agent(req: UserRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    update_job(job_id, {"status": "processing", "pesan": "Permintaan diterima, Aira sedang memproses..."})

    background_tasks.add_task(proses_latar_belakang, job_id, req.message)

    return {
        "status": "processing",
        "job_id": job_id,
        "pesan": "Permintaan diterima, Aira sedang memproses..."
    }

@app.get("/cek-jawaban/{job_id}")
def cek_jawaban(job_id: str):
    job_data = get_job(job_id)
    
    if not job_data:
        return {"status": "not_found", "pesan": "Job ID tidak ditemukan di memori server."}
    
    return job_data