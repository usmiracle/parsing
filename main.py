import os
from Parser import CSharp

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    cs_file = os.path.join(current_dir, "to_parse.cs")

    with open(cs_file, "r") as file:
        to_parse = file.read()

    cs = CSharp(to_parse)
    for _class in cs.get_classes():
        print(_class.class_name)
        print(_class.attributes)
        print(_class.environment.values)

    print()
    
    # Test resolver functionality
    resolver_test = """
public class ResolverTest {
    var a = "abc" + "def";
    var b = a + "fjk";
    var c = $"{b}lmn";
    int anumber = 10;
    int somenumber = a + 10;
    var somebool = true;
    string greeting = "Hello";
    string name = "World";
    string message = greeting + " " + name;
    string interpolated = $"Welcome {name}!";
    
    // Expression-bodied members
    var GlobalLabShare = "https://global-lab.com";
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/share";
    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}/recipients";
}
"""
    cs = CSharp(resolver_test)
    for _class in cs.get_classes():
        _class.resolve_all()
        print(f"Class: {_class.class_name}")
        print(f"Attributes: {_class.attributes}")
        print("Environment values:")
        for var_name, type_obj in _class.environment.values.items():
            print(f"  {var_name}: {type_obj.value} (type: {type_obj.cstype})")
        print()
