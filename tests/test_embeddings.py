import unittest
from unittest.mock import Mock, patch

from src.rag.embeddings import EmbeddingProvider


class EmbeddingProviderTests(unittest.TestCase):
    @patch("src.rag.embeddings.requests.post")
    def test_uses_supported_gemini_model_and_retrieval_task_types(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {"embedding": {"values": [0.1, 0.2]}}
        post.return_value = response
        provider = EmbeddingProvider(api_key="test-key")

        query_embedding = provider.embed_query("programming tutorials")
        document_embeddings = provider.embed_documents(["Code tutorial"])

        self.assertEqual(query_embedding, [0.1, 0.2])
        self.assertEqual(document_embeddings, [[0.1, 0.2]])
        self.assertIn("models/gemini-embedding-001:embedContent", post.call_args_list[0].args[0])
        self.assertEqual(
            post.call_args_list[0].kwargs["json"]["taskType"],
            "RETRIEVAL_QUERY",
        )
        self.assertEqual(
            post.call_args_list[1].kwargs["json"]["taskType"],
            "RETRIEVAL_DOCUMENT",
        )


if __name__ == "__main__":
    unittest.main()
