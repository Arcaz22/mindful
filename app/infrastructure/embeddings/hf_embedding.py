from typing import List

from sentence_transformers import SentenceTransformer


class HuggingFaceEmbedding:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Mengubah teks menjadi list angka (vector)"""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
