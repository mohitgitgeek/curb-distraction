import math
import re
import requests
import numpy as np
from typing import List, Dict, Any, Optional
from src.config import GEMINI_API_KEY

class EmbeddingProvider:
    """Provides vector embeddings using Gemini API or a high-performance local subword vectorizer."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"
        self._vocab = {}
        self._idf = {}
        self._dimension = 128

    def embed_query(self, text: str) -> List[float]:
        """Embed a single search query or statement."""
        vectors = self._embed_batch([text], task_type="RETRIEVAL_QUERY")
        return vectors[0] if vectors else [0.0] * self._dimension

    def embed_query_local(self, text: str) -> List[float]:
        """Embed a query with the local vectorizer, independent of API settings."""
        vectors = self._local_dense_vectorize([text])
        return vectors[0] if vectors else [0.0] * self._dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed indexed documents for semantic retrieval."""
        return self._embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text strings."""
        return self._embed_batch(texts)

    def _embed_batch(
        self,
        texts: List[str],
        task_type: Optional[str] = None,
    ) -> List[List[float]]:
        if not texts:
            return []

        # If Gemini API key is configured, attempt remote embedding
        if self.api_key:
            try:
                embeddings = []
                for text in texts:
                    emb = self._call_gemini_embedding(text, task_type=task_type)
                    embeddings.append(emb)
                return embeddings
            except Exception as e:
                print(f"[Info] Gemini Embedding API unavailable ({e}), using local dense vectorizer.")

        # Fallback: High quality normalized dense subword vectorizer
        return self._local_dense_vectorize(texts)

    def _call_gemini_embedding(
        self,
        text: str,
        task_type: Optional[str] = None,
    ) -> List[float]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": text[:1000]}]}
        }
        if task_type:
            payload["taskType"] = task_type
        resp = requests.post(f"{self.gemini_url}?key={self.api_key}", json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("embedding", {}).get("values", [])
        raise RuntimeError(f"Gemini API Error {resp.status_code}: {resp.text}")

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = cleaned.split()
        # Add character tri-grams for subword matching (e.g. 'code' -> 'cod', 'ode')
        trigrams = []
        for tok in tokens:
            if len(tok) >= 3:
                for i in range(len(tok) - 2):
                    trigrams.append(tok[i:i+3])
        return tokens + trigrams

    def _local_dense_vectorize(self, texts: List[str]) -> List[List[float]]:
        """Hashes n-grams and tokens into a dense normalized fixed-size embedding vector."""
        vectors = []
        dim = self._dimension

        for text in texts:
            tokens = self._tokenize(text)
            vec = np.zeros(dim, dtype=np.float32)
            if not tokens:
                vectors.append(vec.tolist())
                continue

            for tok in tokens:
                # Deterministic polynomial hash
                h = 0
                for ch in tok:
                    h = (h * 31 + ord(ch)) % 0xFFFFFFFF
                idx = h % dim
                # Direction hash to reduce collisions
                sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
                vec[idx] += sign

            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 1e-6:
                vec = vec / norm
            vectors.append(vec.tolist())

        return vectors
