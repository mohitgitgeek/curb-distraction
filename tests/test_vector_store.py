import unittest

import numpy as np

from src.rag.vector_store import VectorStore


class StubEmbeddingProvider:
    def __init__(self, query_vector, local_vector=None):
        self.query_vector = query_vector
        self.local_vector = local_vector or query_vector
        self.remote_calls = 0
        self.local_calls = 0

    def embed_query(self, query):
        self.remote_calls += 1
        return self.query_vector

    def embed_query_local(self, query):
        self.local_calls += 1
        return self.local_vector


class VectorStoreSearchTests(unittest.TestCase):
    def make_store(self, provider, documents, vectors):
        store = VectorStore()
        store.embedding_provider = provider
        store.documents = documents
        store.vectors = np.asarray(vectors, dtype=np.float32)
        return store

    def test_topic_matches_outrank_unrelated_vector_matches_and_deduplicate(self):
        relevant = {
            "id": "coding-video",
            "text": "Title: SheBuilds Code & Connect.",
            "metadata": {
                "video_id": "coding-video",
                "title": "SheBuilds | Code & Connect",
                "category": "Education",
                "tags": [],
            },
        }
        unrelated = {
            "id": "unrelated-video",
            "text": "Title: A random travel vlog.",
            "metadata": {
                "video_id": "unrelated-video",
                "title": "A random travel vlog",
                "category": "Travel",
                "tags": [],
            },
        }
        store = self.make_store(
            StubEmbeddingProvider([1.0, 0.0]),
            [relevant, dict(relevant), unrelated],
            [[0.1, 0.0], [0.1, 0.0], [0.9, 0.0]],
        )

        results = store.similarity_search("programming tutorials and system design", top_k=5)

        self.assertEqual(
            [result["metadata"]["video_id"] for result in results],
            ["coding-video"],
        )

    def test_local_index_uses_local_query_embedding(self):
        store = self.make_store(
            StubEmbeddingProvider([1.0, 0.0, 0.0], [1.0, 0.0]),
            [{
                "id": "video",
                "text": "Title: Code tutorial.",
                "metadata": {"video_id": "video", "title": "Code tutorial", "tags": []},
            }],
            [[1.0, 0.0]],
        )

        results = store.similarity_search("coding tutorial")

        self.assertEqual(len(results), 1)
        self.assertEqual(store.embedding_provider.remote_calls, 0)
        self.assertEqual(store.embedding_provider.local_calls, 1)

    def test_nonpositive_top_k_returns_no_results(self):
        store = self.make_store(StubEmbeddingProvider([1.0]), [], [])

        self.assertEqual(store.similarity_search("anything", top_k=0), [])


if __name__ == "__main__":
    unittest.main()
