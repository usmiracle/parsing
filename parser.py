# Parse C Sharp code and extract class names
import tree_sitter_c_sharp as tscsharp
from tree_sitter import Language, Node, Parser, Tree


class CSharpClass:
    def __init__(self, node: Node):
        self.name = "hi"


class CSharp:
    language = Language(tscsharp.language())
    parser = Parser(language)

    class_query = language.query(
        """
(class_declaration
  (identifier) @class_name
  (base_list
    (identifier) @base_name)+
)
"""
    )

    def __init__(self, source_code: str):
        self.tree: Tree = self.parser.parse(source_code.encode(encoding="utf8"))

    def get_classes(self):
        all_classes = self.class_query.captures(self.tree.root_node)
        class_names = all_classes.get('class_name', [])
        base_names = all_classes.get('base_name', [])

        # Print each class and its direct super class(es)
        for i, class_node in enumerate(class_names):
            class_name = class_node.text.decode('utf-8') if class_node.text else ''
            # For each class, print its name and its base(s) if present
            if base_names:
                super_class_names = [n.text.decode('utf-8') if n.text else '' for n in base_names]
                print(class_name, *super_class_names)
            else:
                print(class_name)
