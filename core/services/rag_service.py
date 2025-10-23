# src/services/rag_service.py
import os
import chromadb
from common.data.kitab_loader import kitab_loader
from core.services.openrouter_embedding import HuggingFaceEmbeddingFunction


CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../data/chromadb")

class RagService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = None
        # Pakai custom embedding function via OpenRouter
        self.embedding_fn = HuggingFaceEmbeddingFunction()

    def build_index(self, file_path: str):
        """Load kitab.pdf lalu simpan ke ChromaDB"""
        paragraphs = kitab_loader.load_docx(file_path)
        if not paragraphs:
            return 0

        # kalau collection sudah ada, hapus total
        try:
            self.client.delete_collection("kitab_psikolog")
        except:
            pass  # kalau belum ada, abaikan

        self.collection = self.client.create_collection(
            name="kitab_psikolog",
            embedding_function=self.embedding_fn
        )

        # Chunking sederhana
        chunks = self.chunk_texts(paragraphs, chunk_size=500)
        ids = [f"chunk_{i}" for i in range(len(chunks))]

        self.collection.add(documents=chunks, ids=ids)
        return len(chunks)


    def get_context_for_question(self, question: str, top_k: int = 5, max_chars: int = 1500) -> str:
        if not self.collection:
            self.collection = self.client.get_or_create_collection(
                name="kitab_psikolog",
                embedding_function=self.embedding_fn
            )

        results = self.collection.query(query_texts=[question], n_results=top_k)
        docs = results["documents"][0]

        # gabungkan context
        context = "\n".join(docs)
        return context[:max_chars]

    def chunk_texts(self, texts, chunk_size=500):
        chunks, current = [], ""
        for txt in texts:
            if len(current) + len(txt) < chunk_size:
                current += " " + txt
            else:
                chunks.append(current.strip())
                current = txt
        if current:
            chunks.append(current.strip())
        return chunks

# singleton
rag_service = RagService()
