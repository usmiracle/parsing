import os
from parser import CSharp

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    cs_file = os.path.join(current_dir, "to_parse.cs")

    with open(cs_file, "r") as file:
        to_parse = file.read()

    cs = CSharp(to_parse)
    cs.get_classes()
