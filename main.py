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
    
    another_test = """
public class MyClass {
    int x = 10;
    x = 11;
    string name = "Alice";
    bool flag;
    //event EventHandler OnSomething;
}
"""
    cs = CSharp(another_test)
    for _class in cs.get_classes():
        print(_class.class_name)
        print(_class.attributes)
        print(_class.environment.enclosing)
        print(_class.environment.values)
