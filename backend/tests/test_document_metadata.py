import unittest
from datetime import datetime

from backend.controller.helpers import get_indexed_file_stats
from backend.models.file import File
from backend.models.node import Node


class DocumentMetadataTest(unittest.TestCase):

    def test_file_metadata_round_trips_through_node_json(self):
        file_obj = File(
            "cid",
            100,
            "notes.txt",
            creation_date=datetime(2026, 1, 2, 3, 4, 5),
            document_id="3d159aa6-cc4f-4bd7-8406-bb037ac6f4d0",
            mime_type="text/plain",
        )
        file_obj.mark_rag_ready(3, "gemini-embedding-001")
        root = Node("root", True)
        root.add_child(Node("notes.txt", False, file_obj=file_obj))

        restored = Node.from_json(root.to_json())

        self.assertEqual(restored.children["notes.txt"].file_obj, file_obj)

    def test_stats_include_only_ready_documents(self):
        root = Node("root", True)
        ready = File("ready-cid", 10, "ready.txt")
        ready.mark_rag_ready(4, "gemini-embedding-001")
        failed = File("failed-cid", 10, "failed.txt", rag_status="failed")
        root.add_child(Node("ready.txt", False, file_obj=ready))
        root.add_child(Node("failed.txt", False, file_obj=failed))

        self.assertEqual(
            get_indexed_file_stats(root),
            {
                "total_chunks": 4,
                "total_files": 1,
                "files": ["ready.txt"],
            },
        )


if __name__ == "__main__":
    unittest.main()
