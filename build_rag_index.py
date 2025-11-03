import os
import logging
from core.services.rag_service import rag_service

# --- Konfigurasi Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Skrip ini akan memuat kitab.pdf, memprosesnya, dan menyimpannya ke dalam
    database vektor ChromaDB. Ini adalah langkah setup satu kali.
    """
    pdf_path = os.path.join(os.path.dirname(__file__), "common", "data", "kitab.pdf")
    
    if not os.path.exists(pdf_path):
        logger.error(f"File PDF tidak ditemukan di: {pdf_path}")
        logger.error("Pastikan file 'kitab.pdf' ada di dalam folder 'common/data/'.")
        return

    logger.info("Memulai proses embedding kitab.pdf ke ChromaDB...")
    
    # Membangun atau membangun ulang indeks
    chunk_count = rag_service.build_index(pdf_path)
    
    if chunk_count > 0:
        logger.info(f"✅ Berhasil! {chunk_count} potongan teks telah di-embed dan disimpan ke ChromaDB.")
    else:
        logger.error("❌ Gagal memproses atau meng-embed file PDF.")

if __name__ == "__main__":
    # Nonaktifkan telemetri ChromaDB untuk menghindari error saat menjalankan skrip ini
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    main()