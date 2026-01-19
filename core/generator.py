from fpdf import FPDF
import os

class PDFGenerator:
    def __init__(self, output_filename):
        self.output_filename = output_filename
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)

    def create_standard_pdf(self, original_name, final_data, manual_crops, session_state):
        self.pdf.add_page()
        # Judul Dokumen
        self.pdf.set_font("Arial", 'B', 16)
        self.pdf.cell(0, 10, txt=f"STANDARISASI: {original_name.upper()}", ln=True, align='C')
        self.pdf.ln(10)

        for bab, content in final_data.items():
            # Nama Bab
            self.pdf.set_font("Arial", 'B', 14)
            self.pdf.set_fill_color(240, 240, 240)
            self.pdf.cell(0, 10, txt=bab, ln=True, fill=True)
            self.pdf.ln(5)

            # Isi Teks
            self.pdf.set_font("Arial", '', 11)
            self.pdf.multi_cell(0, 7, txt=content)
            self.pdf.ln(5)

            # Cek Gambar yang dicentang untuk Bab ini
            for idx, img_path in enumerate(manual_crops):
                # ID Checkbox: chk_{bab}_{idx}
                if session_state.get(f"chk_{bab}_{idx}"):
                    if os.path.exists(img_path):
                        # Ukuran gambar otomatis 120mm lebar
                        self.pdf.image(img_path, w=120)
                        self.pdf.ln(5)
        
        self.pdf.output(self.output_filename)