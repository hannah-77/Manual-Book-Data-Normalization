import os
import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import logging

# Matikan semua log sistem agar tidak bentrok dengan Streamlit
logging.getLogger("ppocr").setLevel(logging.ERROR)

# --- FLAG STABILITAS MUTLAK (Wajib untuk Windows + Python 3.13) ---
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit' # Memperbaiki masalah memori

class PDFExtractor:
    def __init__(self, pdf_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")
        
        self.doc = fitz.open(pdf_path)
        
        # Inisialisasi hanya dengan parameter paling dasar
        # Jangan tambahkan use_gpu atau show_log di sini
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True, 
                lang='id',
                enable_mkldnn=False
            )
        except Exception as e:
            print(f"Gagal inisialisasi PaddleOCR: {e}")

    def process_single_page(self, page_num, scale=2.5):
        temp_dir = os.path.join(os.getcwd(), "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 1. Render PDF ke Gambar
        page = self.doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        img_path = os.path.join(temp_dir, f"ocr_page_{page_num}.png")
        pix.save(img_path)

        # 2. Jalankan OCR dengan penanganan error ketat
        page_text = ""
        try:
            # Panggil fungsi ocr tanpa parameter tambahan apa pun
            result = self.ocr.ocr(img_path)
            
            if result and result[0]:
                for line in result[0]:
                    # Mengambil teks (indeks 1, elemen 0)
                    if line and len(line) > 1:
                        page_text += str(line[1][0]) + " "
            else:
                page_text = "[Tidak ada teks terdeteksi]"
        except Exception as e:
            page_text = f"[Error OCR: {str(e)}]"
        
        return page_text.strip(), img_path