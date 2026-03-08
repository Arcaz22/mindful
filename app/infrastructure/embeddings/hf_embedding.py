from sentence_transformers import SentenceTransformer
from typing import List

class HuggingFaceEmbedding:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Mengubah teks menjadi list angka (vector)"""
        embedding = self.model.encode(text)
        return embedding.tolist()
