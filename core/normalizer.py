import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def normalize_text_to_json(raw_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are a data normalization expert. Convert the following messy OCR text from a manual book into a clean JSON format.
    
    Rules:
    1. Identify titles, section headers, and values.
    2. If there are tables, represent them as a list of objects.
    3. Use Indonesian or English keys based on the context.
    4. Return ONLY valid JSON.

    OCR TEXT:
    {raw_text}
    """
    
    response = model.generate_content(prompt)
    
    # Clean up markdown if the model wraps it in ```json
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)