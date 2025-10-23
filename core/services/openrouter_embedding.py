# src/services/huggingface_embedding.py
import logging
from chromadb.utils.embedding_functions import EmbeddingFunction
from chromadb.api.types import Documents, Embeddings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class HuggingFaceEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Embedding function using HuggingFace SentenceTransformer.
        Default model: all-MiniLM-L6-v2 (ringan & cepat).
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"HuggingFace model '{model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {str(e)}")
            raise

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for a list of texts using HuggingFace model"""
        if isinstance(input, str):
            input = [input]  # pastikan input selalu list

        try:
            embeddings = self.model.encode(input, convert_to_numpy=True).tolist()
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # fallback: kembalikan list kosong dengan panjang sesuai input
            return [[] for _ in input]
