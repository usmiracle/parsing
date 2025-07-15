import re

from Environment import Environment


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
    def _resolve_string_interpolation(expression: str, environment: Environment) -> str:
        """Resolve string interpolation like $"Hello {name}!" """
        # Remove the $ and outer quotes
        content = expression[2:-1]
        
        # Find all interpolation expressions {variable}
        pattern = r'\{([^}]+)\}'
        
        def replace_interpolation(match):
            var_name = match.group(1).strip()
            # Resolve the variable value
            value = CSEvaluator._resolve_variable_reference(var_name, environment)
            # Remove quotes if it's a string literal
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
