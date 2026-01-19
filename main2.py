# main.py
import streamlit as st
from core.extractor import PDFExtractor
from core.ai_handler import AIHandler
from core.generator import PDFGenerator

st.set_page_config(layout="wide", page_title="Alkes Standardizer")
st.title("📑 Standarisasi Manual Book Alkes")

# Inisialisasi AI
if 'ai' not in st.session_state:
    st.session_state.ai = AIHandler()

uploaded_file = st.file_uploader("Upload Manual Book", type="pdf")

if uploaded_file:
    col_orig, col_edit = st.columns([1, 1])

    # Sisi Kiri: PDF Asli
    with col_orig:
        st.subheader("📄 PDF Referensi")
        st.write(f"File: {uploaded_file.name}")
        # PDF Viewer sederhana
        st.download_button("Download/Buka PDF Asli", uploaded_file.getvalue(), file_name=uploaded_file.name)

    # Sisi Kanan: Form Editor hasil AI
    with col_edit:
        st.subheader("📝 Draft Struktur Standar (Dapat Diedit)")
        
        if st.button("🚀 Ekstrak & Analisis dengan AI"):
            with st.spinner("AI sedang memetakan data..."):
                # Simpan sementara untuk diekstrak
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                extractor = PDFExtractor("temp.pdf")
                raw_text = ""
                for page in extractor.doc:
                    raw_text += page.get_text()
                
                # Panggil AI
                st.session_state.data_draft = st.session_state.ai.map_content_to_chapters(raw_text)
                st.success("Analisis selesai!")

        # Form Tampilan Bab & Sub-bab
        if 'data_draft' in st.session_state:
            with st.form("final_form"):
                final_data = {}
                for bab_name, sub_chapters in st.session_state.data_draft.items():
                    with st.expander(f"📁 {bab_name}", expanded=True):
                        final_data[bab_name] = {}
                        for sub_name, content in sub_chapters.items():
                            # Input area untuk tiap sub-bab
                            edited = st.text_area(sub_name, value=content, height=150)
                            final_data[bab_name][sub_name] = edited
                
                if st.form_submit_button("✅ Simpan & Generate PDF Baru"):
                    gen = PDFGenerator(f"Standardized_{uploaded_file.name}")
                    # Fungsi generator disesuaikan untuk menerima dict nested
                    gen.create_standard_pdf(uploaded_file.name, final_data)
                    st.success("PDF Baru Berhasil Dibuat!")