import json
import os
from pathlib import Path

def run_validation(output_folder):
    output_path = Path(output_folder)
    json_files = list(output_path.rglob("*.json"))
    
    report = []
    total_files = len(json_files)
    files_with_missing_data = 0

    print(f"Memulai validasi pada {total_files} file...")

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        missing_chapters = []
        for chapter, content in data.items():
            # Jika konten kosong atau hanya berisi spasi/newline
            if not content.strip():
                missing_chapters.append(chapter)
        
        if missing_chapters:
            files_with_missing_data += 1
            report.append({
                "file": str(json_file.relative_to(output_path)),
                "status": "Incomplete",
                "missing": missing_chapters
            })
        else:
            report.append({
                "file": str(json_file.relative_to(output_path)),
                "status": "Complete",
                "missing": []
            })

    # Simpan laporan ke file teks atau JSON
    with open("validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # Tampilkan Ringkasan di Terminal
    print("\n" + "="*40)
    print("HASIL VALIDASI DATA")
    print("="*40)
    print(f"Total File Diperiksa : {total_files}")
    print(f"File Lengkap         : {total_files - files_with_missing_data}")
    print(f"File Tidak Lengkap   : {files_with_missing_data}")
    print("="*40)
    
    if files_with_missing_data > 0:
        print("\nContoh file yang perlu diperiksa (cek validation_report.json untuk detail):")
        for item in report[:5]: # Tampilkan 5 contoh saja di terminal
            if item["status"] == "Incomplete":
                print(f"- {item['file']} (Missing: {len(item['missing'])} bab)")

if __name__ == "__main__":
    run_validation("data_output")