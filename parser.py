# Parse C Sharp code and extract class names
import tree_sitter_c_sharp as tscsharp

from collections.abc import Iterator
from Environment import Environment
from tree_sitter import Language, Parser, Tree, Node

from Resolver import CSEvaluator


class CSharpMethod:
    def __init__(self, node: Node, source_bytes: bytes, class_ref: 'CSharpClass'):
        self.node = node
        self.attributes = []
        self.method_name = ""
        self.class_ref = class_ref
        # Environment: enclosing is the class's environment
        self.environment = Environment(class_ref.environment)
        self._extract_attributes(source_bytes)
        self._extract_method_name()
        self._load_methodlevel_variables(source_bytes)

    def _extract_attributes(self, source_bytes: bytes):
        for child in self.node.children:
            if child.type == "attribute_list":
                attr_text = source_bytes[child.start_byte:child.end_byte].decode()
                self.attributes.append(attr_text)

    def _extract_method_name(self):
        for child in self.node.children:
            if child.type == "identifier" and child.text:
                self.method_name = child.text.decode()

    def _load_methodlevel_variables(self, source_bytes: bytes):
        # You can expand this to parse method parameters, local variables, etc.
        # For now, let's just parse parameters as variables
        for child in self.node.children:
            if child.type == "parameter_list":
                for param in child.children:
                    if param.type == "parameter":
                        var_name = None
                        for param_child in param.children:
                            if param_child.type == "identifier" and param_child.text:
                                var_name = param_child.text.decode()
                        if var_name:
                            from Environment import Type
                            # Default to string type for now
                            self.environment.define(var_name, Type("", "string"))


class CSharpClass:
    node: Node
    attributes: list[str]
    class_name: str
    environment: Environment

    def __init__(self, node: Node, source_bytes: bytes, globals: Environment | None = None):
        self.node = node
        self.source = source_bytes  # Add this line
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
            if child.type == "identifier" and child.text:
                self.class_name = child.text.decode()

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
                if child.type == "field_declaration":
                    for inner in child.children:
                        # Variable declaration
                        if inner.type == "variable_declaration":
                            var_name = ""
                            var_value = ""
                            for declarator in inner.children:
                                # declarator can be predefined_type or implicit_type (var)

                                if declarator.type == "predefined_type":
                                    predef_type = source_bytes[declarator.start_byte:declarator.end_byte].decode().strip()
                                    match predef_type:
                                        case "string":
                                            var_value = ""
                                        case "int":
                                            var_value = "0"
                                        case "bool":
                                            var_value = "false"
                                elif declarator.type == "implicit_type":
                                    # For var declarations, we need to look at the initializer to determine the value
                                    var_value = ""  # Default for var without initializer

                                if declarator.type != "variable_declarator" and declarator.type != "identifier":
                                    continue

                                if declarator.type == "variable_declarator":
                                    for item in declarator.children:
                                        if item.type == "identifier":
                                            var_name = source_bytes[item.start_byte:item.end_byte].decode()
                                        elif item.type == "=":
                                            # Get the value after '='
                                            # Find the next sibling or look ahead for the value
                                            equals_pos = item.end_byte
                                            # Look for the value after the equals sign
                                            remaining_text = source_bytes[equals_pos:inner.end_byte].decode().strip()
                                            if remaining_text:
                                                # Resolve the expression using the evaluator
                                                var_value = CSEvaluator.evaluate(remaining_text, self.environment)
                                    else:
                                        # Check if this item has a value (like literal expressions)
                                        if hasattr(item, 'text') and item.text:
                                            var_value = item.text.decode()

                                    if var_name:
                                        # Create a Type object for the value
                                        from Environment import Type
                                        cstype = CSEvaluator._determine_type(var_value)
                                        type_obj = Type(var_value, cstype)
                                        print(self.environment.define(var_name, type_obj))
                                        print(f"defined: {var_name} {var_value}")
                                else:
                                    # assignment
                                    var_name = source_bytes[declarator.start_byte:declarator.end_byte].decode()
                                    raw_value = source_bytes[declarator.end_byte:inner.end_byte].decode().strip().lstrip("=").strip()
                                    # Resolve the expression using the evaluator
                                    var_value = CSEvaluator.evaluate(raw_value, self.environment)
                                    
                                    if var_name:
                                        # Create a Type object for the value
                                        from Environment import Type
                                        cstype = CSEvaluator._determine_type(var_value)
                                        type_obj = Type(var_value, cstype)
                                        print(self.environment.assign(var_name, type_obj))
                                        print(f"assigned: {var_name} {var_value}")
                
                elif child.type == "property_declaration":
                    # Handle property declarations with arrow expressions
                    self._parse_property_declaration(child, source_bytes)
                
                elif child.type == "method_declaration":
                    # Handle method declarations with arrow expressions
                    self._parse_method_declaration(child, source_bytes)
                else:
                    pass

    def _parse_property_declaration(self, node: Node, source_bytes: bytes):
        """Parse property declarations with arrow expressions"""
        var_name = ""
        var_value = ""
        
        for child in node.children:
            if child.type == "identifier":
                var_name = source_bytes[child.start_byte:child.end_byte].decode()
            elif child.type == "arrow_expression_clause":
                # Extract the expression after =>
                expression_text = source_bytes[child.start_byte:child.end_byte].decode()
                # Remove the "=>" part
                var_value = expression_text.replace("=>", "").strip()
                break
        
        if var_name and var_value:
            try:
                # Try to resolve the expression
                resolved_value = CSEvaluator.evaluate(var_value, self.environment)
                from Environment import Type
                cstype = CSEvaluator._determine_type(resolved_value)
                type_obj = Type(resolved_value, cstype)
                print(self.environment.define(var_name, type_obj))
                print(f"defined property: {var_name} {resolved_value}")
            except Exception as e:
                print(f"COULD NOT BE RESOLVED: {var_name} = {var_value}")
                print(f"Error: {e}")
                # Store the unresolved value
                from Environment import Type
                type_obj = Type(var_value, "unknown")
                print(self.environment.define(var_name, type_obj))
    
    def _parse_method_declaration(self, node: Node, source_bytes: bytes):
        """Parse method declarations with arrow expressions"""
        var_name = ""
        var_value = ""
        
        for child in node.children:
            if child.type == "identifier":
                var_name = source_bytes[child.start_byte:child.end_byte].decode()
            elif child.type == "arrow_expression_clause":
                # Extract the expression after =>
                expression_text = source_bytes[child.start_byte:child.end_byte].decode()
                # Remove the "=>" part
                var_value = expression_text.replace("=>", "").strip()
                break
        
        if var_name and var_value:
            try:
                # Try to resolve the expression
                resolved_value = CSEvaluator.evaluate(var_value, self.environment)
                from Environment import Type
                cstype = CSEvaluator._determine_type(resolved_value)
                type_obj = Type(resolved_value, cstype)
                print(self.environment.define(var_name, type_obj))
                print(f"defined method: {var_name} {resolved_value}")
            except Exception as e:
                print(f"COULD NOT BE RESOLVED: {var_name} = {var_value}")
                print(f"Error: {e}")
                # Store the unresolved value
                from Environment import Type
                type_obj = Type(var_value, "unknown")
                print(self.environment.define(var_name, type_obj))

    def resolve_all(self):
        for var_name, type_obj in self.environment.values.items():
            resolved = CSEvaluator.evaluate(type_obj.value, self.environment)
            type_obj.value = resolved

    def get_methods(self) -> Iterator['CSharpMethod']:
        for child in self.node.children:
            if child.type == "declaration_list":
                for member in child.children:
                    if member.type == "method_declaration":
                        yield CSharpMethod(member, self.source, self)

class CSharp:
    var_decl_types = ["field_declaration", "property_declaration", "method_declaration"] # , "event_field_declaration" ## support not needed now

    language = Language(tscsharp.language())
    parser = Parser(language)

    def __init__(self, source_code: str, globals: Environment | None = None):
        self.source = source_code.encode()
        self.tree: Tree = self.parser.parse(self.source)
        self.globals = globals # globals for classes within

    def get_classes(self) -> Iterator[CSharpClass]:
        for node in self._traverse():
            if node.type == "class_declaration":
                yield CSharpClass(node, self.source, self.globals)

    def _traverse(self) -> Iterator[Node]:
        cursor = self.tree.walk()
    
        reached_root = False
        while reached_root == False:
            if cursor.node: yield cursor.node
    
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
    
