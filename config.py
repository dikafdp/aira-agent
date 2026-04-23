from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama
#from langchain_community.utilities import SearxSearchWrapper

load_dotenv("secrets/.env")
load_dotenv("secrets/.env", override=True)

HF_TOKEN = os.getenv("HF_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.253.29:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.0
)
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080").rstrip("/")
SEARXNG_TIMEOUT = int(os.getenv("SEARXNG_TIMEOUT", "30"))

SEARXNG_HEADERS = {}
if "ngrok" in SEARXNG_URL:
    SEARXNG_HEADERS["ngrok-skip-browser-warning"] = "true"

#SEARXNG_URL = os.getenv("SEARXNG_URL", "")
#search_tool = SearxSearchWrapper(searx_host=SEARXNG_URL)