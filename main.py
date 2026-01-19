import streamlit as st
import os
import json
import google.generativeai as genai
from core.extractor import PDFExtractor
from dotenv import load_dotenv

# 1. Load API Key dari .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

# --- FUNGSI AI GEMINI ---
def normalize_with_gemini(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Tugas: Ubah teks OCR mentah dari manual book ini menjadi JSON yang rapi.
    Struktur JSON harus mencakup: 'judul_dokumen', 'spesifikasi_teknis', dan 'isi_materi'.
    Jika ada tabel, buat menjadi list of objects.
    Hanya berikan output JSON murni.

    TEKS OCR:
    {text}
    """
    response = model.generate_content(prompt)
    # Membersihkan tag markdown agar JSON bisa dibaca sistem
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return clean_json

st.set_page_config(page_title="PDF Normalizer Fix", layout="wide")
st.title("📄 PDF Normalizer - Manual Book to JSON")

# --- UI APP ---
if not api_key:
    st.warning("Silakan masukkan GOOGLE_API_KEY di file .env Anda.")
    st.stop()

uploaded_file = st.file_uploader("Upload PDF Manual", type="pdf")

if uploaded_file:
    # Simpan PDF sementara
    temp_pdf_path = os.path.join(os.getcwd(), "temp_uploaded.pdf")
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        extractor = PDFExtractor(temp_pdf_path)
        total_pages = len(extractor.doc)
        page_idx = st.number_input(f"Pilih Halaman (0-{total_pages-1})", 0, total_pages-1, 0)

        if st.button("Proses Halaman"):
            with st.spinner("Sedang memproses OCR..."):
                # Menjalankan fungsi dari extractor.py
                raw_text, image_preview_path = extractor.process_single_page(page_idx)
                
                # Simpan hasil ke session state agar tidak hilang saat tombol lain ditekan
                st.session_state['ocr_text_result'] = raw_text
                st.session_state['ocr_image_result'] = image_preview_path

        # --- TAMPILAN HASIL ---
        if 'ocr_text_result' in st.session_state:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🖼️ Preview Halaman")
                # DI SINI LETAK KODE st.image TERSEBUT
                if os.path.exists(st.session_state['ocr_image_result']):
                    st.image(st.session_state['ocr_image_result'], caption="Hasil Scan", use_container_width=True)
                else:
                    st.error("File gambar preview tidak ditemukan.")

            with col2:
                st.subheader("📝 Raw Text Terdeteksi")
                st.text_area("OCR Output:", st.session_state['ocr_text_result'], height=250)
                
                # TOMBOL NORMALISASI AI SEKARANG BERFUNGSI
                if st.button("Langkah Final: Normalisasi ke JSON"):
                    with st.spinner("AI sedang merapikan data..."):
                        try:
                            json_str = normalize_with_gemini(st.session_state['ocr_text_result'])
                            st.session_state['final_json'] = json_str
                        except Exception as e:
                            st.error(f"Gagal memproses AI: {e}")

                # Menampilkan hasil JSON jika sudah selesai
                if 'final_json' in st.session_state:
                    st.subheader("✅ Hasil JSON")
                    try:
                        parsed_json = json.loads(st.session_state['final_json'])
                        st.json(parsed_json)
                    except:
                        st.code(st.session_state['final_json'], language="json")
                    
                    st.download_button(
                        "Download JSON", 
                        st.session_state['final_json'], 
                        file_name=f"data_halaman_{page_idx}.json"
                    )

    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")