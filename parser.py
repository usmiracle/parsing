# Parse C Sharp code and extract class names
import tree_sitter_c_sharp as tscsharp

from collections.abc import Iterator
from Environment import Environment
from tree_sitter import Language, Parser, Tree, Node

class CSEvaluator:
    @staticmethod
    def evaluate(expression: any):
        pass


class CSharpClass:
    node: Node
    attributes: list[str]
    class_name: str
    environment: Environment

    def __init__(self, node: Node, source_bytes: bytes, globals: Environment | None = None):
        self.node = node
        self.attributes = []
        self.class_name = ""
        self.environment = Environment(globals)
        self._extract_attributes(source_bytes)
        self._extract_class_name()
        self._load_classlevel_variables(source_bytes)

    def _extract_attributes(self, source_bytes: bytes):
        for child in self.node.children:
            if child.type == "attribute_list":
                attr_text = source_bytes[child.start_byte:child.end_byte].decode()
                self.attributes.append(attr_text)

    def _extract_class_name(self):
        for child in self.node.children:
            if child.type == "identifier":
                self.class_name = child.text.decode("utf-8")

    def _load_classlevel_variables(self, source_bytes: bytes):
        var_decls_types = CSharp.var_decl_types

        class_body: Node | None = None
        for child in self.node.children:
            if child.type == "declaration_list":
                class_body = child
                break

        if class_body is None:
            raise Exception(f"No Class Body in {self.class_name}")

        for child in class_body.children:
            # Handle block scoping (if needed, e.g., in method parsing)
            # if child.type == "{":
            #     self.environment = Environment()
            # elif child.type == "}":
            #     if self.environment.enclosing:
            #         self.environment = self.environment.enclosing

            if child.type in var_decls_types:
                for inner in child.children:
                    # Variable declaration
                    if inner.type == "variable_declaration":
                        var_name = ""
                        var_value = ""
                        for declarator in inner.children:
                            # declarator can be predefined_type

                            if declarator.type == "predefined_type":
                                predef_type = source_bytes[declarator.start_byte:declarator.end_byte].decode().strip()
                                match predef_type:
                                    case "string":
                                        var_value = ""
                                    case "int":
                                        var_value = "0"
                                    case "bool":
                                        var_value = "false"

                            if declarator.type != "variable_declarator" and declarator.type != "identifier":
                                continue

                            if declarator.type == "variable_declarator":
                                for item in declarator.children:
                                    if item.type == "identifier":
                                        var_name = source_bytes[item.start_byte:item.end_byte].decode()
                                    elif item.type == "=":
                                        # Get full text after '='
                                        continue
                                        var_value = source_bytes[item.start_byte:inner.end_byte].decode()
                                        var_value = var_value.strip().lstrip('=').strip()
                                    else:
                                        pass
                                        # var_value = resolve()

                                if var_name:
                                    print(self.environment.define(var_name, var_value))
                                    print(f"defined: {var_name} {var_value}")
                            else:
                                # assignement
                                var_name = source_bytes[declarator.start_byte:declarator.end_byte].decode()
                                var_value = source_bytes[declarator.end_byte:inner.end_byte].decode().strip().lstrip("=").strip()
                                
                                if var_name:
                                    print(self.environment.assign(var_name, var_value))
                                    print(f"assigned: {var_name} {var_value}")

class CSharp:
    var_decl_types = ["field_declaration"] # , "event_field_declaration" ## support not needed now

    language = Language(tscsharp.language())
    parser = Parser(language)

    def __init__(self, source_code: str):
        self.source = source_code.encode()
        self.tree: Tree = self.parser.parse(self.source)

    def get_classes(self) -> Iterator[CSharpClass]:
        for node in self._traverse():
            if node.type == "class_declaration":
                yield CSharpClass(node, self.source)

    def _traverse(self) -> Iterator[Node]:
        cursor = self.tree.walk()
    
        reached_root = False
        while reached_root == False:
            yield cursor.node
    
            if cursor.goto_first_child():
                continue
    
            if cursor.goto_next_sibling():
                continue
    
            retracing = True
            while retracing:
                if not cursor.goto_parent():
                    retracing = False
                    reached_root = True
    
                if cursor.goto_next_sibling():
                    retracing = False
    
