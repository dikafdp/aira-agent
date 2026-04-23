import requests
import base64
from state import AgentState
from config import HF_TOKEN

def generate_image(state: AgentState):
    prompt = state.get("image_prompt", "beautiful scenery")

    try:
        API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

        if response.status_code == 200:
            image_bytes = response.content
            base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
            image_data_url = f"data:image/jpeg;base64,{base64_encoded}"

            return {
                "final_answer": f"🎨 Gambar Stable Diffusion berhasil dibuat!\nPrompt: {prompt}",
                "image_url": image_data_url
            }
        else:
            try:
                error_msg = response.json()
            except:
                error_msg = response.text

            return {
                "final_answer": f"🚨 Gagal (Error {response.status_code}):\n{error_msg}"
            }

    except Exception as e:
        return {"final_answer": f"Gagal sistem Python: {str(e)}"}