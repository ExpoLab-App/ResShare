import unittest

from backend.utils.error import ErrorCode
from backend.models.node import Node
from backend.services.share_manager import ShareManager


class ShareManagerResolveForClientTest(unittest.TestCase):
    def test_resolved_nodes_keep_the_canonical_shared_path(self):
        root = Node("root", True)
        projects = Node("projects", True)
        shared_folder = Node("damn", True)
        projects.add_child(shared_folder)
        root.add_child(projects)

        manager = ShareManager()
        result = manager.receive("test_user_2", "projects/damn", True)

        self.assertEqual(result, ErrorCode.SUCCESS)

        resolved = manager.resolve_for_client(
            lambda username: root if username == "test_user_2" else None
        )

        shared_item = resolved["test_user_2"][0]
        self.assertEqual(shared_item["name"], "damn")
        self.assertEqual(shared_item["shared_path"], "projects/damn")

    def test_resolved_nodes_distinguish_duplicate_leaf_names(self):
        root = Node("root", True)
        first_parent = Node("first", True)
        second_parent = Node("second", True)
        first_parent.add_child(Node("damn", True))
        second_parent.add_child(Node("damn", True))
        root.add_child(first_parent)
        root.add_child(second_parent)

        manager = ShareManager()
        manager.receive("test_user_2", "first/damn", True)
        manager.receive("test_user_2", "second/damn", True)

        resolved = manager.resolve_for_client(
            lambda username: root if username == "test_user_2" else None
        )

        shared_paths = {
            item["shared_path"]
            for item in resolved["test_user_2"]
        }
        self.assertEqual(shared_paths, {"first/damn", "second/damn"})


if __name__ == "__main__":
    unittest.main()
