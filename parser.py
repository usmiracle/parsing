from __future__ import annotations

# Parse C Sharp code and extract class names
import tree_sitter_c_sharp as tscsharp

from collections.abc import Iterator
from Environment import Environment, Type
from tree_sitter import Language, Parser, Tree, Node

from Resolver import CSEvaluator



class CSharpMethod:
    def __init__(self, node: Node, source_bytes: bytes, class_ref: 'CSharpClass'):
        self.node = node
        self.source = source_bytes
        self.attributes = []
        self.method_name = ""
        self.class_ref = class_ref
        self.environment = Environment(class_ref.environment)
        self.parameters = []  # <-- Add this
        self._extract_attributes(source_bytes)
        self._extract_method_name()
        self._load_methodlevel_variables(source_bytes)
        self._parse_local_methods()  # NEW

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
        # Parse parameters as variables
        for child in self.node.children:
            if child.type == "parameter_list":
                for param in child.children:
                    if param.type == "parameter":
                        var_name = None
                        for param_child in param.children:
                            if param_child.type == "identifier" and param_child.text:
                                var_name = param_child.text.decode()
                        if var_name:
                            self.parameters.append(var_name)  # <-- Track parameter name
                            self.environment.define(var_name, Type("", "string"))
        # Parse local variable declarations in the method body
        for child in self.node.children:
            if child.type == "block":
                self._parse_block_variables(child, source_bytes)

    def _parse_block_variables(self, block_node: Node, source_bytes: bytes):
        # Recursively parse for local variable declarations and local functions
        for child in block_node.children:
            if child.type == "local_declaration_statement":
                for grandchild in child.children:
                    if grandchild.type == "variable_declaration":
                        var_type = None
                        for decl_child in grandchild.children:
                            if decl_child.type == "predefined_type":
                                var_type = source_bytes[decl_child.start_byte:decl_child.end_byte].decode().strip()
                            elif decl_child.type == "variable_declarator":
                                var_name = None
                                var_value = ""
                                for item in decl_child.children:
                                    if item.type == "identifier":
                                        var_name = source_bytes[item.start_byte:item.end_byte].decode()
                                    elif item.type == "equals_value_clause":
                                        value_text = source_bytes[item.start_byte:item.end_byte].decode()
                                        value_text = value_text.lstrip('=').strip()
                                        var_value = CSEvaluator.evaluate(value_text, self.environment)
                                if var_name:
                                    cstype = var_type if var_type else "string"
                                    self.environment.define(var_name, Type(var_value, cstype))
            elif child.type == "local_function_statement":
                # Local function: treat like a method
                local_method = CSharpMethod(child, source_bytes, self.class_ref)
                self.environment.define(local_method.method_name, Type(local_method, "method"))
            elif child.type == "block":
                # Nested block: recurse
                self._parse_block_variables(child, source_bytes)

    def _parse_local_methods(self):
        # Already handled in _parse_block_variables for local functions
        pass

    def get_methods(self):
        """
        Yield all local methods in the method, in the order they were added to the environment.
        """
        for value in self.environment.values.values():
            if isinstance(value, Type) and value.cstype == "method":
                yield value.value

    def call(self, args, calling_env):
        # Create a new environment for the call, with the class environment as enclosing
        call_env = Environment(self.class_ref.environment)
        for pname, pval in zip(self.parameters, args):
            arg_val = CSEvaluator.evaluate(pval, calling_env)
            call_env.define(pname, Type(arg_val, "string"))
        # Find the arrow_expression_clause
        for child in self.node.children:
            if child.type == "arrow_expression_clause":
                expr = self.source[child.start_byte:child.end_byte].decode().replace("=>", "").strip()
                return CSEvaluator.evaluate(expr, call_env)
        # (Optional: handle block bodies)
        return None


class CSharpClass:
    node: Node
    attributes: list[str]
    class_name: str
    super_class_name: str  # <-- Add this
    environment: Environment

    def __init__(self, node: Node, source_bytes: bytes, globals: Environment | None = None):
        self.node = node
        self.source = source_bytes  # Add this line
        self.attributes = []
        self.class_name = ""
        self.super_class_name = ""  # <-- Initialize
        self.environment = Environment(globals)
        self._extract_attributes(source_bytes)
        self._extract_class_name()
        self._extract_super_class_name(source_bytes)  # <-- Add this
        self._load_classlevel_variables(source_bytes)
        self._parse_method_declarations()  # NEW

    def _extract_attributes(self, source_bytes: bytes):
        for child in self.node.children:
            if child.type == "attribute_list":
                attr_text = source_bytes[child.start_byte:child.end_byte].decode()
                self.attributes.append(attr_text)

    def _extract_class_name(self):
        for child in self.node.children:
            if child.type == "identifier" and child.text:
                self.class_name = child.text.decode()

    def _extract_super_class_name(self, source_bytes: bytes):
        for child in self.node.children:
            if child.type == "base_list":
                # base_list: ':' base_type (',' base_type)*
                for base_child in child.children:
                    # The first identifier under base_list is usually the superclass
                    if base_child.type == "identifier" and base_child.text:
                        self.super_class_name = base_child.text.decode()
                        return
                    # Fallback: check for base_type → identifier
                    if base_child.type == "base_type":
                        for t in base_child.children:
                            if t.type == "identifier" and t.text:
                                self.super_class_name = t.text.decode()
                                return

    def _load_classlevel_variables(self, source_bytes: bytes):
        var_decls_types = CSharpFile.var_decl_types

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
                                        type_obj = Type(var_name, cstype)
                                        self.environment.define(var_name, type_obj)
                                        f"defined: {var_name} {var_value}"
                                else:
                                    # assignment
                                    var_name = source_bytes[declarator.start_byte:declarator.end_byte].decode()
                                    raw_value = source_bytes[declarator.end_byte:inner.end_byte].decode().strip().lstrip("=").strip()
                                    # Resolve the expression using the evaluator
                                    var_value = CSEvaluator.evaluate(raw_value, self.environment)
                                    
                                    if var_name:
                                        # Create a Type object for the value
                                        cstype = CSEvaluator._determine_type(var_value)
                                        type_obj = Type(var_name, cstype)
                                        self.environment.assign(var_name, type_obj)
                
                elif child.type == "property_declaration":
                    # Handle property declarations with arrow expressions
                    self._parse_property_declaration(child, source_bytes)
                
                elif child.type == "method_declaration":
                    # Handle method declarations with arrow expressions
                    self._parse_method_declaration(child, source_bytes)
                else:
                    pass

    def _parse_method_declarations(self):
        """
        Parse all method_declaration nodes in the class and add them to the environment.
        """
        for child in self.node.children:
            if child.type == "declaration_list":
                for member in child.children:
                    if member.type == "method_declaration":
                        method = CSharpMethod(member, self.source, self)
                        self.environment.define(method.method_name, Type(method, "method"))

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
                self.environment.define(var_name, type_obj)
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
        parameter_env = Environment()
        
        for child in node.children:
            child_token_name = source_bytes[child.start_byte:child.end_byte].decode()
            if child.type == "identifier":
                var_name = source_bytes[child.start_byte:child.end_byte].decode()
            elif child.type == "arrow_expression_clause":
                # Extract the expression after =>
                expression_text = source_bytes[child.start_byte:child.end_byte].decode()
                # Remove the "=>" part
                var_value = expression_text.replace("=>", "").strip()
                break
            elif child.type == "parameter_list":
                for grandChild in child.children:
                    grandChildType = grandChild.type
                    if grandChildType == "parameter":
                        param = source_bytes[grandChild.start_byte:grandChild.end_byte].decode()
                        from Environment import Type
                        parameter_env.define(param, Type(None, ""))

        
        if var_name and var_value:
            try:
                # Try to resolve the expression
                resolved_value = CSEvaluator.evaluate(var_value, self.environment)
                from Environment import Type
                cstype = CSEvaluator._determine_type(resolved_value)
                type_obj = Type(resolved_value, cstype)
                self.environment.define(var_name, type_obj)
            except Exception as e:
                print(f"COULD NOT BE RESOLVED: {var_name} = {var_value}")
                print(f"Error: {e}")
                # Store the unresolved value
                from Environment import Type
                type_obj = Type(var_value, "unknown")
                print(self.environment.define(var_name, type_obj))

    def resolve_all(self):
        for var_name, type_obj in self.environment.values.items():
            assert(isinstance(type_obj.value, str))
            resolved = CSEvaluator.evaluate(type_obj.value, self.environment)
            type_obj.value = resolved

    def get_methods(self) -> Iterator['CSharpMethod']:
        """
        Yield all methods in the class, in the order they were added to the environment.
        """
        for value in self.environment.values.values():
            if isinstance(value, Type) and isinstance(value.value, CSharpMethod):
                yield value.value

class CSharpFile:
    """
    Intakes a CS file's source code and global environment with variables defined outside of the file.
    Evaluates variables and methods outside of the class within the file.
    Hands Class Nodes to a CSharpClass (but stores the class in the environment).
    Skips the evaluation of Class Nodes to let CSharpClass handle it.

    Functionality to return all the classes within the file.
    """
    var_decl_types = ["field_declaration", "property_declaration", "method_declaration"]  # , "event_field_declaration" ## support not needed now

    language = Language(tscsharp.language())
    parser = Parser(language)

    def __init__(self, source_code: str, globals: Environment | None = None):
        self.source = source_code.encode()
        self.tree: Tree = self.parser.parse(self.source)
        self.environment = Environment(globals)  # file-level environment
        self._parse_file_level_declarations()

    def _parse_file_level_declarations(self):
        """
        Parse the file for top-level variable and method declarations (outside any class).
        When a class is found, instantiate it and add to the environment.
        """
        for node in self._traverse():
            if node.type == "class_declaration":
                csharp_class = CSharpClass(node, self.source, self.environment)
                self.environment.define(csharp_class.class_name, Type(csharp_class, "class"))
            elif node.type == "field_declaration":
                self._parse_variable_declaration(node)
            # You can add support for property_declaration or method_declaration at file level if needed

    def _parse_variable_declaration(self, node: Node):
        """
        Parse a field_declaration node at the file level and add variables to the environment.
        """
        for child in node.children:
            if child.type == "variable_declaration":
                var_type = None
                for decl_child in child.children:
                    if decl_child.type == "predefined_type":
                        var_type = self.source[decl_child.start_byte:decl_child.end_byte].decode().strip()
                    elif decl_child.type == "variable_declarator":
                        var_name = None
                        var_value = ""
                        for item in decl_child.children:
                            if item.type == "identifier":
                                var_name = self.source[item.start_byte:item.end_byte].decode()
                            elif item.type == "equals_value_clause":
                                # Get the value after '='
                                value_text = self.source[item.start_byte:item.end_byte].decode()
                                # Remove '=' and whitespace
                                value_text = value_text.lstrip('=').strip()
                                # Evaluate the value using CSEvaluator if needed
                                from Resolver import CSEvaluator
                                var_value = CSEvaluator.evaluate(value_text, self.environment)
                        if var_name:
                            # Default to string type if not found
                            cstype = var_type if var_type else "string"
                            self.environment.define(var_name, Type(var_value, cstype))

    def _extract_class_name(self, node: Node) -> str:
        for child in node.children:
            if child.type == "identifier" and child.text:
                return child.text.decode()
        return ""

    def get_classes(self) -> Iterator['CSharpClass']:
        """
        Yield all classes in the file, in the order they were added to the environment.
        """
        for value in self.environment.values.values():
            if isinstance(value, Type) and isinstance(value.value, CSharpClass):
                yield value.value

    def _traverse(self) -> Iterator[Node]:
        cursor = self.tree.walk()
        reached_root = False
        while not reached_root:
            if cursor.node:
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
    
