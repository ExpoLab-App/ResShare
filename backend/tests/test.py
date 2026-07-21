import unittest

from backend.models.file import File
from backend.models.node import Node

class NodePathTest(unittest.TestCase):
    def test_find_node_by_absolute_path(self):
        root = Node("root", True)
        documents = Node("documents", True)
        pictures = Node("pictures", True)
        nested = Node("nested", True)
        pictures.add_child(nested)
        documents.add_child(
            Node("notes.txt", False, File("notes-cid", 20, "notes.txt"))
        )
        root.add_child(documents)
        root.add_child(pictures)

        target_node = root.find_node_by_path("/root/pictures")

        self.assertIs(target_node, pictures)


if __name__ == "__main__":
    unittest.main()
