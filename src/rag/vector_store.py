import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from src.config import VECTOR_INDEX_PATH
from src.rag.embeddings import EmbeddingProvider

SEARCH_CONCEPTS = {
    "programming": ("programming", "coding", "code", "software", "developer", "development"),
    "tutorials": (
        "tutorial",
        "tutorials",
        "lesson",
        "lessons",
        "course",
        "courses",
        "walkthrough",
        "walkthroughs",
    ),
    "system design": (
        "system design",
        "software architecture",
        "distributed systems",
        "architecture",
        "scalability",
        "backend design",
    ),
}
STOP_WORDS = {"a", "an", "and", "for", "in", "of", "on", "or", "the", "to", "with"}


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _query_concepts(query: str) -> List[Tuple[str, ...]]:
    query = query.casefold()
    concepts = []
    covered_query_terms = set()

    for aliases in SEARCH_CONCEPTS.values():
        query_aliases = [alias for alias in aliases if _contains_term(query, alias)]
        if query_aliases:
            concepts.append(aliases)
            for alias in query_aliases:
                covered_query_terms.update(re.findall(r"\w+", alias))

    for term in re.findall(r"\w+", query):
        if term not in STOP_WORDS and term not in covered_query_terms:
            concepts.append((term,))

    return concepts


def _lexical_relevance(query: str, text: str) -> float:
    concepts = _query_concepts(query)
    if not concepts:
        return 0.0
    text = text.casefold()
    matched = sum(any(_contains_term(text, alias) for alias in aliases) for aliases in concepts)
    return matched / len(concepts)


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
            description = r.get("description", "")

            # Composite rich document representation
            doc_text = f"Title: {title}. Channel: {channel}. Category: {cat}."
            if query:
                doc_text += f" Search Query: {query}."
            if tags:
                doc_text += f" Tags: {tags[:200]}."
            if description:
                doc_text += f" Description: {description[:1000]}."

            texts.append(doc_text)
            docs.append({
                "id": r.get("video_id") or r.get("url"),
                "text": doc_text,
                "metadata": r
            })

        if not texts:
            return 0

        embeddings = self.embedding_provider.embed_documents(texts)
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
        if top_k <= 0:
            return []
        if len(self.documents) == 0 or self.vectors.shape[0] == 0:
            return []

        local_query_vec = np.array(
            self.embedding_provider.embed_query_local(query),
            dtype=np.float32,
        )
        using_local_index = self.vectors.shape[1] == local_query_vec.size
        if using_local_index:
            query_vec = local_query_vec
        else:
            query_vec = np.array(self.embedding_provider.embed_query(query), dtype=np.float32)
        if query_vec.size != self.vectors.shape[1]:
            print(
                "[Info] Query embedding dimension does not match the saved index; "
                "using the local query vectorizer."
            )
            query_vec = np.array(
                self.embedding_provider.embed_query_local(query),
                dtype=np.float32,
            )
        if query_vec.size != self.vectors.shape[1]:
            raise ValueError(
                "Query and index embeddings use incompatible dimensions. "
                "Rebuild the index with `python run_cli.py sync`."
            )

        q_norm = np.linalg.norm(query_vec)
        if q_norm > 1e-6:
            query_vec = query_vec / q_norm

        # Compute cosine similarities
        scores = np.dot(self.vectors, query_vec)

        # Local hash similarities are noisy, so use them only as a tie-breaker
        # and omit unrelated results when topic matches exist.
        results = []
        for idx, score in enumerate(scores):
            doc = self.documents[idx]
            if category and doc["metadata"].get("category") != category:
                continue
            metadata = doc["metadata"]
            searchable_text = " ".join(
                str(value)
                for value in (
                    doc.get("text", ""),
                    metadata.get("title", ""),
                    metadata.get("description", ""),
                    metadata.get("channel", ""),
                    metadata.get("category", ""),
                    metadata.get("search_query", ""),
                    " ".join(metadata.get("tags", []))
                    if isinstance(metadata.get("tags"), list)
                    else metadata.get("tags", ""),
                )
                if value
            )
            lexical_score = _lexical_relevance(query, searchable_text)
            vector_score = max(0.0, min(1.0, float(score)))
            if using_local_index:
                combined_score = 0.75 * lexical_score + 0.25 * vector_score
            else:
                combined_score = 0.5 * lexical_score + 0.5 * vector_score
            results.append({
                "score": float(round(combined_score, 4)),
                "document": doc["text"],
                "metadata": metadata,
                "id": doc.get("id"),
                "lexical_score": lexical_score,
            })

        if using_local_index and any(result["lexical_score"] > 0 for result in results):
            results = [result for result in results if result["lexical_score"] > 0]

        # Sort descending by relevance and avoid returning the same video repeatedly.
        results.sort(key=lambda x: x["score"], reverse=True)
        unique_results = []
        seen_ids = set()
        for result in results:
            metadata = result["metadata"]
            result_id = (
                result.get("id")
                or metadata.get("video_id")
                or metadata.get("url")
                or id(result)
            )
            if result_id in seen_ids:
                continue
            seen_ids.add(result_id)
            result.pop("id", None)
            result.pop("lexical_score", None)
            unique_results.append(result)
            if len(unique_results) == top_k:
                break
        return unique_results

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
