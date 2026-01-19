import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Mencari model yang tersedia...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ Gunakan nama ini: {m.name}")