import pdfplumber
import json
import os
import re
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from langdetect import detect, DetectorFactory

# Memastikan hasil deteksi bahasa konsisten
DetectorFactory.seed = 0

# ==========================================
# 1. TRANSLATION MAP (Kamus Terjemahan Label)
# ==========================================
TRANSLATION_MAP = {
    "1.1 Tujuan Produk/Definisi": {"ID": "1.1 Tujuan Produk/Definisi", "EN": "1.1 Intended Use/Definition"},
    "1.2 Panduan Keamanan": {"ID": "1.2 Panduan Keamanan", "EN": "1.2 Safety Guidelines"},
    "1.3 Penjelasan Simbol": {"ID": "1.3 Penjelasan Simbol", "EN": "1.3 Explanation of Symbols"},
    "1.4 Singkatan": {"ID": "1.4 Singkatan", "EN": "1.4 Abbreviations"},
    "2.0 Instalasi": {"ID": "2.0 Instalasi", "EN": "2.0 Installation"},
    "3.1 Antarmuka Pengguna": {"ID": "3.1 Antarmuka Pengguna", "EN": "3.1 User Interface"},
    "3.2 Overview": {"ID": "3.2 Overview", "EN": "3.2 Overview"},
    "3.3 Manajemen Pengguna": {"ID": "3.3 Manajemen Pengguna", "EN": "3.3 User Management"},
    "3.4 Prosedur Pemantauan": {"ID": "3.4 Prosedur Pemantauan", "EN": "3.4 Monitoring Procedure"},
    "3.5 Perhitungan Medis": {"ID": "3.5 Perhitungan Medis", "EN": "3.5 Medical Calculation"},
    "3.6 Manajemen Rekaman & Tinjauan Hasil": {"ID": "3.6 Manajemen Rekaman & Tinjauan Hasil", "EN": "3.6 Record Management & Review"},
    "4.1 Inspeksi Umum": {"ID": "4.1 Inspeksi Umum", "EN": "4.1 General Inspection"},
    "4.2 Pemeliharaan": {"ID": "4.2 Pemeliharaan", "EN": "4.2 Maintenance"},
    "4.3 Perawatan": {"ID": "4.3 Perawatan", "EN": "4.3 Care"},
    "4.4 Pembersihan": {"ID": "4.4 Pembersihan", "EN": "4.4 Cleaning"},
    "5.0 Pemecahan Masalah": {"ID": "5.0 Pemecahan Masalah", "EN": "5.0 Troubleshooting"},
    "6.1 Spesifikasi": {"ID": "6.1 Spesifikasi", "EN": "6.1 Specification"},
    "6.2 Kepatuhan Standar": {"ID": "6.2 Kepatuhan Standar", "EN": "6.2 Standard Compliance"},
    "7.1 Garansi": {"ID": "7.1 Garansi", "EN": "7.1 Warranty"},
    "7.2 Informasi Kontak": {"ID": "7.2 Informasi Kontak", "EN": "7.2 Contact Information"}
}

# ==========================================
# 2. CLASS SEMANTIC NORMALIZER
# ==========================================
class SemanticNormalizer:
    def __init__(self, schema_labels):
        print("Memuat model AI Multilingual...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.labels = schema_labels
        self.label_keys = list(schema_labels.keys())
        
        # Buat deskripsi kaya (Key + Keywords) agar AI lebih akurat
        rich_descriptions = []
        for key, value in schema_labels.items():
            combined_text = f"{key} " + " ".join(value["keywords"])
            rich_descriptions.append(combined_text)
            
        self.label_embeddings = self.model.encode(rich_descriptions, convert_to_tensor=True)
        self.threshold = 0.50 

    def detect_language(self, pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                sample_text = ""
                for page in pdf.pages[:2]:
                    extracted = page.extract_text()
                    if extracted: sample_text += extracted + " "
                lang = detect(sample_text)
                return "Indonesia" if lang == 'id' else "English"
        except:
            return "English"

    def process_pdf(self, pdf_path):
        lang_detected = self.detect_language(pdf_path)
        lang_code = "ID" if lang_detected == "Indonesia" else "EN"

        output_data = {
            "metadata": {"file_name": pdf_path.name, "detected_language": lang_detected},
            "content": {},
            "detected_headings": {} # Tracking sub-bab asli untuk summary
        }
        
        current_section_internal = None
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text: continue
                
                blocks = text.split('\n')
                for block in blocks:
                    clean_block = block.strip()
                    if len(clean_block) < 5: continue 

                    # A. Pre-processing (Hapus angka romawi/bab dari input AI)
                    process_text = re.sub(r'^\b[IVXLCDM]+\b\.?\s*', '', clean_block, flags=re.IGNORECASE)
                    process_text = re.sub(r'^\d+(\.\d+)*\s*', '', process_text).strip()
                    if not process_text: process_text = clean_block

                    matched_internal_key = None
                    best_score = 0

                    # B. Logika 1: Hard Match (Mengecek Keywords manual)
                    for key, val in self.labels.items():
                        if any(kw.lower() in clean_block.lower() for kw in val["keywords"]):
                            matched_internal_key = key
                            best_score = 0.95 
                            break

                    # C. Logika 2: Semantic Match (Jika Hard Match tidak kena)
                    if not matched_internal_key:
                        block_emb = self.model.encode(process_text, convert_to_tensor=True)
                        scores = util.cos_sim(block_emb, self.label_embeddings)[0]
                        top_indices = torch.argsort(scores, descending=True)

                        for idx in top_indices:
                            idx = idx.item()
                            temp_key = self.label_keys[idx]
                            temp_score = scores[idx].item()
                            
                            # Cek Exclude List
                            excludes = self.labels[temp_key].get("exclude", [])
                            if not any(ex.lower() in clean_block.lower() for ex in excludes):
                                matched_internal_key = temp_key
                                best_score = temp_score
                                break

                    # D. Update Section & Audit Record
                    if len(clean_block) < 60 and best_score > self.threshold:
                        current_section_internal = matched_internal_key
                        
                        # Simpan asal sub-bab untuk master summary
                        if matched_internal_key not in output_data["detected_headings"]:
                            output_data["detected_headings"][matched_internal_key] = []
                        
                        heading_info = f"{clean_block} (Hal. {page_num})"
                        if heading_info not in output_data["detected_headings"][matched_internal_key]:
                            output_data["detected_headings"][matched_internal_key].append(heading_info)

                        # Output Terminal
                        translated = TRANSLATION_MAP.get(matched_internal_key, {}).get(lang_code, matched_internal_key)
                        print(f"[AUDIT] Halaman {page_num}:")
                        print(f"   Judul di PDF   : '{clean_block}'")
                        print(f"   Masuk ke Schema: '{translated}'")
                        print(f"   Tingkat Cocok  : {best_score:.2f}\n")

                    # E. Simpan Konten Teks
                    if current_section_internal:
                        final_key = TRANSLATION_MAP.get(current_section_internal, {}).get(lang_code, current_section_internal)
                        if final_key not in output_data["content"]:
                            output_data["content"][final_key] = ""
                        output_data["content"][final_key] += clean_block + " "

        return output_data

# ==========================================
# 3. SCHEMA LABELS
# ==========================================
MY_SCHEMA_LABELS = {
    "1.1 Tujuan Produk/Definisi": {
        "keywords": ["tujuan produk", "definisi", "intended use", "product overview"],
        "exclude": []
    },
    "1.2 Panduan Keamanan": {
        "keywords": ["keamanan", "safety guidelines", "warning", "caution", "peringatan"],
        "exclude": []
    },
    "1.3 Penjelasan Simbol": {
        "keywords": ["simbol", "explanation of symbols", "simbol alat"],
        "exclude": []
    },
    "1.4 Singkatan": {
        "keywords": ["singkatan", "abbreviations", "daftar singkatan"],
        "exclude": ["XIII", "XII", "XI", "Garansi", "Warranty", "Bab"] 
    },
    "2.0 Instalasi": {
        "keywords": ["instalasi", "pemasangan", "setup", "unboxing"],
        "exclude": []
    },
    "3.1 Antarmuka Pengguna": {
        "keywords": ["user interface", "display", "tampilan", "layar", "tombol"],
        "exclude": []
    },
    "3.2 Overview": {
        "keywords": ["overview", "gambaran umum", "product overview", "accessories", "aksesoris", "controls"],
        "exclude": ["spesifikasi", "specification"]
    },
    "3.3 Manajemen Pengguna": {
        "keywords": ["manajemen pengguna", "data pengguna", "patient record", "user management", "pengaturan", "data pasien"],
        "exclude": []
    },
    "3.4 Prosedur Pemantauan": {
        "keywords": ["prosedur pemantauan", "monitoring procedure", "langkah pemantauan"],
        "exclude": []
    },
    "3.5 Perhitungan Medis": {
        "keywords": ["medical calculation", "perhitungan medis", "kalkulasi dosis"],
        "exclude": []
    },
    "3.6 Manajemen Rekaman & Tinjauan Hasil": {
        "keywords": ["manajemen rekaman", "tinjauan hasil", "historical data", "logbook"],
        "exclude": []
    },
    "4.1 Inspeksi Umum": {
        "keywords": ["inspeksi umum", "general inspection", "pemeriksaan fisik"],
        "exclude": ["Untuk memulai pengukuran manual", "Langkah-langkah pengukuran", "Instruksi pengukuran"]
    },
    "4.2 Pemeliharaan": {
        "keywords": ["maintenance", "pemeliharaan", "kalibrasi", "pengecekan teknis", "servis berkala", "penggantian suku cadang"],
        "exclude": ["penyimpanan", "cara membawa", "care of device"]
    },
    "4.3 Perawatan": {
        "keywords": ["perawatan", "care of device", "penyimpanan", "storage", "penanganan alat", "cara menjaga"],
        "exclude": ["kalibrasi", "servis", "suku cadang", "technical check"]
    },
    "4.4 Pembersihan": {
        "keywords": ["pembersihan", "cleaning", "disinfection", "sterilisasi"],
        "exclude": []
    },
    "5.0 Pemecahan Masalah": {
        "keywords": ["troubleshooting", "error codes", "solusi masalah"],
        "exclude": []
    },
    "6.1 Spesifikasi": {
        "keywords": ["spesifikasi", "specification", "technical data", "berat", "dimensi", "daya"],
        "exclude": ["accessories", "aksesoris", "1.5"] 
    },
    "6.2 Kepatuhan Standar": {
        "keywords": ["IEC", "EMC", "ISO", "standar kepatuhan"],
        "exclude": []
    },
    "7.1 Garansi": {
        "keywords": ["garansi", "warranty", "purna jual"],
        "exclude": ["IEC", "EMC", "ISO"] 
    },
    "7.2 Informasi Kontak": {
        "keywords": ["kontak", "service contact", "layanan pelanggan", "telepon", "alamat"],
        "exclude": []
    }
}

# ==========================================
# 4. RUNNER
# ==========================================
def run_process_limited(input_dir, output_dir, limit=10):
    normalizer = SemanticNormalizer(MY_SCHEMA_LABELS)
    input_path = Path(input_dir)
    pdf_files = list(input_path.rglob("*.pdf"))
    
    # Inisialisasi Master Summary
    master_summary = {key: {} for key in MY_SCHEMA_LABELS.keys()}
    
    count = 0 
    for pdf in pdf_files:
        if count >= limit: break
            
        print(f"\n[{count + 1}/{limit}] Memproses: {pdf.name}")
        result = normalizer.process_pdf(pdf)
        
        # Masukkan hasil deteksi ke Master Summary
        for schema_key, headings in result.get("detected_headings", {}).items():
            master_summary[schema_key][pdf.name] = headings
        
        # Simpan JSON individual
        rel_path = pdf.relative_to(input_path)
        out_file = Path(output_dir) / rel_path.with_suffix(".json")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        count += 1

    # SIMPAN MASTER AUDIT SUMMARY (Rangkuman Semua PDF)
    summary_file = Path(output_dir) / "master_audit_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(master_summary, f, indent=4, ensure_ascii=False)
    
    print(f"\n[DONE] Proses selesai.")
    print(f"[INFO] Master summary disimpan di: {summary_file}")

if __name__ == "__main__":
    if not os.path.exists("data_input"):
        os.makedirs("data_input")
    run_process_limited("data_input", "data_output", limit=10)