import pdfplumber
import os
from pathlib import Path
from collections import Counter
from tqdm import tqdm # Library untuk progress bar

def run_mass_discovery(input_folder, existing_schema):
    # 1. Kumpulkan semua keyword yang sudah ada agar tidak dideteksi lagi
    existing_keywords = []
    for keywords in existing_schema.values():
        existing_keywords.extend([kw.lower() for kw in keywords])

    input_path = Path(input_folder)
    pdf_files = list(input_path.rglob("*.pdf"))
    
    unmapped_candidates = Counter()

    print(f"Menganalisis {len(pdf_files)} file PDF... Ini mungkin memakan waktu beberapa menit.")

    # 2. Iterasi semua file dengan Progress Bar (tqdm)
    for pdf_file in tqdm(pdf_files):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                # Kita hanya ambil 10 halaman pertama tiap PDF untuk efisiensi (biasanya judul ada di sini)
                pages_to_scan = pdf.pages[:10] 
                
                for page in pages_to_scan:
                    text = page.extract_text()
                    if not text: continue
                    
                    lines = text.split('\n')
                    for line in lines:
                        clean = line.strip()
                        
                        # KRITERIA JUDUL: 
                        # - Panjang karakter antara 4 - 40 (tidak terlalu panjang/pendek)
                        # - Bukan angka saja
                        # - Tidak ada di schema yang sudah ada
                        if 4 < len(clean) < 40 and not clean.isdigit():
                            is_already_mapped = any(kw in clean.lower() for kw in existing_keywords)
                            
                            if not is_already_mapped:
                                # Simpan sebagai calon keyword
                                unmapped_candidates[clean] += 1
        except Exception:
            continue # Lewati jika file rusak

    # 3. Tampilkan 50 kata yang paling sering muncul
    print("\n" + "="*50)
    print("TOP 50 CALON KEYWORD BARU (Belum Ada di Schema)")
    print("="*50)
    print(f"{'KATA/FRASA':<35} | {'MUNCUL DI BERAPA PDF'}")
    print("-"*50)
    
    for word, count in unmapped_candidates.most_common(50):
        print(f"{word:<35} | {count} kali")

# --- MASUKKAN SCHEMA ANDA SAAT INI ---
MY_SCHEMA = {
    "1.1 Tujuan": ["intended use", "tujuan"],
    # ... masukkan semua schema Anda di sini
}

if __name__ == "__main__":
    # Pastikan menginstal tqdm: pip install tqdm
    run_mass_discovery("data_input", MY_SCHEMA)