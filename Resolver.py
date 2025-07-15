import re

from Environment import Environment, Type


class CSEvaluator:
    @staticmethod
    def evaluate(expression: str, environment: Environment) -> str:
        """Evaluate C# expressions and return the resolved value"""
        # var a = "abc" + "def"
        # a is stored as abcdef
        # var b = $"{a}ghi"
        # b is stored as abcdefghi
        # ...

        if not expression or not expression.strip():
            return ""
        
        expression = expression.strip()
        
        # Handle string interpolation: $"Hello {name}!"
        if expression.startswith('$"') and expression.endswith('"'):
            return CSEvaluator._resolve_string_interpolation(expression, environment)
        
        # Handle function/method call: Foo("bar")
        func_call_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', expression)
        if func_call_match:
            func_name = func_call_match.group(1)
            arg_str = func_call_match.group(2)
            args = CSEvaluator._parse_args(arg_str)
            return CSEvaluator._call_method(func_name, args, environment)

        # Handle string concatenation: "abc" + "def" or a + "def"
        if '+' in expression:
            return CSEvaluator._resolve_string_concatenation(expression, environment)
        
        # Handle simple variable reference: a
        if CSEvaluator._is_simple_identifier(expression):
            return CSEvaluator._resolve_variable_reference(expression, environment)
        
        # Handle string literals: "Hello"
        if expression.startswith('"') and expression.endswith('"'):
            return expression
        
        # Handle numeric literals: 123
        if expression.isdigit():
            return expression
        
        # Handle boolean literals
        if expression.lower() in ['true', 'false']:
            return expression.lower()
        
        return expression
    
    @staticmethod
    def _parse_args(arg_str: str):
        # This is a simple parser, does not handle nested commas or complex expressions
        args = []
        depth = 0
        current = ''
        for c in arg_str:
            if c == ',' and depth == 0:
                args.append(current.strip())
                current = ''
            else:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                current += c
        if current.strip():
            args.append(current.strip())
        return args

    @staticmethod
    def _call_method(func_name: str, args, environment: Environment) -> str:
        type_obj = environment.get(func_name)
        if type_obj is not None and hasattr(type_obj, "cstype") and type_obj.cstype == "method":
            method_obj = type_obj.value
            # Bind arguments to parameters
            param_names = []
            for child in method_obj.node.children:
                if child.type == "parameter_list":
                    for param in child.children:
                        if param.type == "parameter":
                            for param_child in param.children:
                                if param_child.type == "identifier" and param_child.text:
                                    param_names.append(param_child.text.decode())
            # Create a new environment for the call
            call_env = Environment(method_obj.environment.class_ref.environment)
            for pname, pval in zip(param_names, args):
                # Evaluate argument in the calling environment
                arg_val = CSEvaluator.evaluate(pval, environment)
                call_env.define(pname, Type(arg_val, "string"))
            # Evaluate the method's body/expression in the new environment
            # Find the arrow_expression_clause
            for child in method_obj.node.children:
                if child.type == "arrow_expression_clause":
                    expr = method_obj.source[child.start_byte:child.end_byte].decode().replace("=>", "").strip()
                    return CSEvaluator.evaluate(expr, call_env)
            # If block, you could extend to support block bodies
        print(f"UNRESOLVED FUNC CALL: {func_name}({', '.join(args)})")
        return f'"{func_name}({", ".join(args)})"'
    
    @staticmethod
    def _resolve_string_interpolation(expression: str, environment: Environment) -> str:
        """Resolve string interpolation like $"Hello {name}!" """
        # Remove the $ and outer quotes
        content = expression[2:-1]
        
        # Find all interpolation expressions {variable}
        pattern = r'\{([^}]+)\}'
        
        def replace_interpolation(match):
            expr = match.group(1).strip()
            value = CSEvaluator.evaluate(expr, environment)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value
        
        result = re.sub(pattern, replace_interpolation, content)
        return f'"{result}"'
    
    @staticmethod
    def _resolve_string_concatenation(expression: str, environment: Environment) -> str:
        """Resolve string concatenation like "abc" + "def" or a + "def" """
        parts = expression.split('+')
        resolved_parts = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Resolve each part
            resolved_part = CSEvaluator.evaluate(part, environment)
            # Remove quotes if it's a string literal
            if resolved_part.startswith('"') and resolved_part.endswith('"'):
                resolved_part = resolved_part[1:-1]
            resolved_parts.append(resolved_part)
        
        # Join all parts and wrap in quotes
        result = ''.join(resolved_parts)
        return f'"{result}"'
    
    @staticmethod
    def _resolve_variable_reference(var_name: str, environment: Environment) -> str:
        """Resolve a variable reference to its value"""
        type_obj = environment.get(var_name)
        if type_obj is not None:
            # If it's a method, return its name (or you could raise an error)
            if hasattr(type_obj, "cstype") and type_obj.cstype == "method":
                return f'"{var_name}"'
            if isinstance(type_obj.value, str):
                return type_obj.value
        print(f'\n -- -- -- -- \nUNRESOLVED VAR"{var_name}"\n -- -- -- -- \n')
        return f'"{var_name}"'  # Return as string if not found 
    
    @staticmethod
    def _is_simple_identifier(expression: str) -> bool:
        """Check if expression is a simple identifier (variable name)"""
        # Simple check: no spaces, no special characters except underscore
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', expression))
    
    @staticmethod
    def _determine_type(value: str) -> str:
        """Determine the C# type of a value"""
        if not value:
            return "unknown"
        
        # Remove quotes for string literals
        if value.startswith('"') and value.endswith('"'):
            return "string"
        
        # Check for boolean literals
        if value.lower() in ['true', 'false']:
            return "bool"
        
        # Check for numeric literals
        if value.isdigit():
            return "int"
        
        # Check for decimal numbers
        if re.match(r'^\d+\.\d+$', value):
            return "double"
        
        # Check for expressions that result in strings (contains + or $)
        if '+' in value or value.startswith('$"'):
            return "string"
        
        return "unknown"
