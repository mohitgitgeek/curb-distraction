import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from src.config import VECTOR_INDEX_PATH
from src.rag.embeddings import EmbeddingProvider

class VectorStore:
    """In-memory and file-persisted vector store with cosine similarity retrieval."""

    def __init__(self, index_file: Path = VECTOR_INDEX_PATH):
        self.index_file = index_file
        self.embedding_provider = EmbeddingProvider()
        self.documents: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.empty((0, 128), dtype=np.float32)

    def build_from_records(self, records: List[Dict[str, Any]]) -> int:
        """Indexes watch history records into the vector database."""
        docs = []
        texts = []

        for r in records:
            title = r.get("title", "")
            cat = r.get("category", "")
            channel = r.get("channel", "")
            query = r.get("search_query", "")
            tags = " ".join(r.get("tags", []))

            # Composite rich document representation
            doc_text = f"Title: {title}. Channel: {channel}. Category: {cat}."
            if query:
                doc_text += f" Search Query: {query}."
            if tags:
                doc_text += f" Tags: {tags[:200]}."

            texts.append(doc_text)
            docs.append({
                "id": r.get("video_id") or r.get("url"),
                "text": doc_text,
                "metadata": r
            })

        if not texts:
            return 0

        embeddings = self.embedding_provider.embed_batch(texts)
        self.documents = docs
        self.vectors = np.array(embeddings, dtype=np.float32)

        self.save()
        return len(docs)

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Finds most relevant watched items for a natural language query."""
        if len(self.documents) == 0 or self.vectors.shape[0] == 0:
            return []

        query_vec = np.array(self.embedding_provider.embed_query(query), dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm > 1e-6:
            query_vec = query_vec / q_norm

        # Compute cosine similarities
        scores = np.dot(self.vectors, query_vec)

        # Pair with documents
        results = []
        for idx, score in enumerate(scores):
            doc = self.documents[idx]
            if category and doc["metadata"].get("category") != category:
                continue
            results.append({
                "score": float(round(score, 4)),
                "document": doc["text"],
                "metadata": doc["metadata"]
            })

        # Sort descending by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def save(self):
        """Persist index and metadata to disk."""
        data = {
            "documents": self.documents,
            "vectors": self.vectors.tolist()
        }
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self) -> bool:
        """Load index from disk if available."""
        if not self.index_file.exists():
            return False
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.documents = data.get("documents", [])
            self.vectors = np.array(data.get("vectors", []), dtype=np.float32)
            return True
        except Exception as e:
            print(f"[Warning] Failed to load vector store from disk: {e}")
            return False
