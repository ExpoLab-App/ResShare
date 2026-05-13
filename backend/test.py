import sys, os
from node import Node
from file import File
from datetime import datetime


root = Node("root", True)
doc_dir = Node("doc", True)
pic_dir = Node("pic", True)
doc2_dir = Node("doc", True)
pic_dir.add_child(doc2_dir)
f1 = Node("file_1", False, File("file_1_cid", 20, "file_1"))
f2 = Node("file_2", False, File("file_2_cid", 22, "file_2"))
root.add_child(pic_dir)
root.add_child(f2)
doc_dir.add_child(f1)
root.add_child(doc_dir)

target_node = root.find_node_by_path("/root/pic")
print(target_node.to_json())









