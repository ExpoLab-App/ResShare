import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
from qdrant_client import QdrantClient

from backend.rag.chunking import chunk_text
from backend.rag.vector_store import QDrantVectorStore


class QdrantRAGManagerTest(unittest.TestCase):
    @staticmethod
    def make_manager(client):
        with patch("backend.rag.vector_store.QdrantClient", return_value=client):
            manager = QDrantVectorStore(embedding_dimension=3)
        manager.collection_name = manager.collection_name
        return manager

    def setUp(self):
        self.manager = self.make_manager(QdrantClient(":memory:"))

        def fake_embeddings(
            texts,
            embedding_model=None,
            embedding_dimensions=3,
            task_type="RETRIEVAL_DOCUMENT",
        ):
            vectors = []
            for text in texts:
                if "alpha" in text:
                    vectors.append([1.0, 0.0, 0.0])
                elif "beta" in text:
                    vectors.append([0.0, 1.0, 0.0])
                else:
                    vectors.append([0.0, 0.0, 1.0])
            return np.array(vectors, dtype=np.float32)

        embedding_patch = patch(
            "backend.rag.vector_store.generate_embeddings",
            side_effect=fake_embeddings,
        )
        embedding_patch.start()
        self.addCleanup(embedding_patch.stop)
        self.addCleanup(self.manager.qdrant_client.close)

    def chunks(self, username, document_id, filename, text):
        metadata = {
            "user_id": username,
            "document_id": document_id,
            "filename": filename,
            "cid": f"cid-{document_id}",
            "path": filename,
            "file_type": "txt",
        }
        return chunk_text(text, metadata)

    def test_search_is_isolated_by_authenticated_user(self):
        alice_document = "f922b5fe-afb6-4ab4-9f6f-b2a42b8a2cf2"
        bob_document = "f134fc1d-810f-4c76-9a56-17ddab142c07"
        self.assertTrue(
            self.manager.add_chunks(
                "alice",
                self.chunks("alice", alice_document, "alice.txt", "alpha private"),
            )
        )
        self.assertTrue(
            self.manager.add_chunks(
                "bob",
                self.chunks("bob", bob_document, "bob.txt", "alpha private"),
            )
        )

        alice_results = self.manager.search_user_vector_db("alice", "alpha", top_k=5)

        self.assertEqual(len(alice_results), 1)
        self.assertEqual(
            alice_results[0]["chunk"]["metadata"]["document_id"],
            alice_document,
        )
        self.assertEqual(alice_results[0]["chunk"]["metadata"]["user_id"], "alice")

    def test_document_delete_does_not_remove_other_users_data(self):
        shared_document_id = "221584c3-1b87-4825-9bda-7c9fb3abf75c"
        self.manager.add_chunks(
            "alice",
            self.chunks("alice", shared_document_id, "alice.txt", "alpha"),
        )
        self.manager.add_chunks(
            "bob",
            self.chunks("bob", shared_document_id, "bob.txt", "alpha"),
        )

        self.assertTrue(self.manager.delete_documents("alice", [shared_document_id]))

        self.assertEqual(self.manager.search_user_vector_db("alice", "alpha"), [])
        self.assertEqual(len(self.manager.search_user_vector_db("bob", "alpha")), 1)

    def test_reindex_replaces_old_chunks_for_same_document(self):
        document_id = "8a16566d-44b0-47d3-b201-c4053a02e91a"
        self.manager.add_chunks(
            "alice",
            self.chunks("alice", document_id, "notes.txt", "alpha"),
        )
        self.manager.add_chunks(
            "alice",
            self.chunks("alice", document_id, "notes.txt", "beta"),
        )

        alpha_results = self.manager.search_user_vector_db("alice", "alpha")
        beta_results = self.manager.search_user_vector_db("alice", "beta")

        self.assertEqual(len(alpha_results), 1)
        self.assertEqual(len(beta_results), 1)
        self.assertEqual(beta_results[0]["chunk"]["text"], "beta")

    def test_vectors_persist_when_manager_is_recreated(self):
        document_id = "2a1caabf-ee52-4bb6-91fb-03253606f71c"
        with TemporaryDirectory() as temp_dir:
            first_client = QdrantClient(path=temp_dir)
            first_manager = self.make_manager(first_client)
            self.assertTrue(
                first_manager.add_chunks(
                    "alice",
                    chunk_text(
                        "alpha",
                        {
                            "user_id": "alice",
                            "document_id": document_id,
                            "filename": "persistent.txt",
                            "cid": "persistent-cid",
                            "path": "persistent.txt",
                            "file_type": "txt",
                        },
                    ),
                )
            )
            first_client.close()

            second_client = QdrantClient(path=temp_dir)
            second_manager = self.make_manager(second_client)
            results = second_manager.search_user_vector_db("alice", "alpha")
            second_client.close()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk"]["metadata"]["document_id"], document_id)


if __name__ == "__main__":
    unittest.main()
