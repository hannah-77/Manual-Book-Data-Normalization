import os
import re
import pytesseract
from pdf2image import convert_from_path

# --- KONFIGURASI PATH ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\ENG-7B\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
PATH_POPPLER = r'C:\poppler-24.08.0\Library\bin'

def detect_language_by_content(pdf_path):
    """Membaca halaman 1 PDF untuk deteksi bahasa"""
    try:
        # Ambil hanya halaman 1 saja
        images = convert_from_path(pdf_path, first_page=1, last_page=1, poppler_path=PATH_POPPLER)
        if not images:
            return "unknown"
        
        # OCR halaman 1
        text = pytesseract.image_to_string(images[0], lang='ind+eng').lower()
        
        # Kata kunci pendeteksi
        id_keywords = ['buku', 'manual', 'spesifikasi', 'daftar', 'isi', 'perangkat', 'keselamatan']
        en_keywords = ['user', 'guide', 'specifications', 'contents', 'device', 'safety', 'warning']
        
        id_score = sum(1 for word in id_keywords if word in text)
        en_score = sum(1 for word in en_keywords if word in text)
        
        if id_score > en_score:
            return "id"
        elif en_score > id_score:
            return "en"
        return "unknown"
    except:
        return "unknown"

def rename_hybrid(base_path):
    print(f"--- Memulai Rename Hybrid (Nama File + Isi PDF) ---")
    
    id_keywords = ['idn', 'id', 'indonesia', 'indo', 'ind']
    en_keywords = ['eng', 'en', 'english', 'inggris']

    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path): continue

        files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        
        for filename in files:
            old_path = os.path.join(folder_path, filename)
            name_lower = filename.lower()
            lang_suffix = ""

            # 1. Coba deteksi via Nama File
            if any(key in name_lower for key in id_keywords):
                lang_suffix = "id"
            elif any(key in name_lower for key in en_keywords):
                lang_suffix = "en"
            
            # 2. Jika gagal, coba deteksi via Isi PDF (OCR)
            if lang_suffix == "":
                print(f"[OCR] Memeriksa isi file: {filename}...")
                lang_suffix = detect_language_by_content(old_path)

            # 3. Tentukan Nama Baru
            file_ext = os.path.splitext(filename)[1]
            new_filename_base = f"manual_{folder_name.lower()}_{lang_suffix}"
            new_filename = f"{new_filename_base}{file_ext}"
            new_path = os.path.join(folder_path, new_filename)

            if old_path == new_path: continue

            # 4. Logika Penomoran agar tidak bentrok
            counter = 1
            while os.path.exists(new_path):
                new_filename = f"{new_filename_base}_{counter}{file_ext}"
                new_path = os.path.join(folder_path, new_filename)
                counter += 1

            # 5. Eksekusi
            try:
                os.rename(old_path, new_path)
                print(f"[Sukses] {filename} -> {new_filename}")
            except Exception as e:
                print(f"[Gagal] {filename}: {e}")

if __name__ == "__main__":
    rename_hybrid('data_input')