import unittest
from src.rag.vector_store import AgriculturalVectorStore
from src.rag.retriever import retrieve_agricultural_evidence

class TestRAG(unittest.TestCase):
    def test_vector_store_indexing_and_retrieval(self):
        store = AgriculturalVectorStore()
        store.build_index()
        self.assertTrue(store.is_initialized)
        self.assertGreater(len(store.chunks), 0)

        results = store.similarity_search("target spots yellowing leaves", crop_filter="Tomato", top_k=2)
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top["crop"], "Tomato")
        self.assertIn("Early Blight", top["condition"])

    def test_retriever_function(self):
        evidence = retrieve_agricultural_evidence(crop="Potato", symptoms="brown lesions concentric", top_k=2)
        self.assertGreater(len(evidence), 0)
        self.assertEqual(evidence[0]["crop"], "Potato")

if __name__ == "__main__":
    unittest.main()
