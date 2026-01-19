# Lokasi: core/ai_handler.py
import requests
import json

class AIHandler:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        # Ganti llama3 menjadi phi3 agar tidak berat di RAM
        self.model = "phi3" 

    def get_single_chapter(self, chapter_title, text_context):
        # Kita kurangi konteks teks sedikit agar proses lebih ringan
        prompt = f"""
        Identifikasi informasi untuk "{chapter_title}" dari teks di bawah.
        Salin teks asli tanpa diringkas. Jika tidak ada, isi "KOSONG".
        Data: {text_context[:5000]}
        """
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            response = requests.post(self.url, json=payload, timeout=120)
            return response.json().get('response', 'KOSONG').strip()
        except:
            return "KOSONG"