# Gunakan tag OS yang spesifik (bookworm adalah Debian 12 terbaru yang lebih aman)
FROM python:3.12-slim-bookworm

WORKDIR /app

# [BARIS TAMBAHAN] Update package list dan upgrade semua paket OS untuk menambal CVE
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]