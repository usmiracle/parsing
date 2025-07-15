from Parser import CSharpClass, CSharpMethod, CSharpFile
from helper import create_globals, globals

def print_environment(env, indent=0):
    for var_name, type_obj in env.values.items():
        prefix = " " * indent
        if hasattr(type_obj, "cstype") and type_obj.cstype == "method":
            print(f"{prefix}{var_name}: <method>")
            # Recursively print local methods' environments
            method_obj = type_obj.value
            print(f"{prefix}  Parameters/Locals:")
            print_environment(method_obj.environment, indent + 4)
            # Print inner methods
            for inner_method in getattr(method_obj, "get_methods", lambda: [])():
                print(f"{prefix}  Inner Method: {inner_method.method_name}")
                print_environment(inner_method.environment, indent + 6)
        else:
            print(f"{prefix}{var_name}: {type_obj} (type: {type_obj.cstype})")

if __name__ == "__main__":
    test_code = """
public class OuterClass {
    int classVar = 42;
    string classString = "hello";
    public void TopLevelMethod(int param1, string param2) {
        int localVar = param1 + 1;
        string localString = param2 + " world";
        var result = HelperFunction(localVar, localString);

        int HelperFunction(int x, string y) {
            int innerVar = x * 2;
            return innerVar;
        }
    }
}
"""
    globals_env = create_globals(globals)
    cs = CSharpFile(test_code, globals=globals_env)
    for _class in cs.get_classes():
        print(f"Class: {_class.class_name}")
        print(f"Attributes: {_class.attributes}")
        print("Class Environment:")
        print_environment(_class.environment, indent=2)
        print("Methods:")
        for method in _class.get_methods():
            print(f"  Method: {method.method_name}")
            print(f"    Attributes: {method.attributes}")
            print(f"    Method Environment:")
            print_environment(method.environment, indent=6)
            # Print inner methods
            for inner_method in method.get_methods():
                assert(isinstance(inner_method, CSharpMethod))
                print(f"      Inner Method: {inner_method.method_name}")
                print_environment(inner_method.environment, indent=10)
        print()