from __future__ import annotations

class Type:
    value: str
    cstype: str

    def __init__(self, value: str, cstype: str):
        self.value = value
        self.cstype = cstype
    

class Environment:
    def __init__(self, enclosing: Environment | None = None):
        self.enclosing: Environment | None = enclosing # enclosing is the globals
        self.values: dict[str, Type] = {}

    def define(self, name: str, value: Type):
        """Define a new variable in the current environment."""
        self.values[name] = value

    def get(self, name: str) -> Type | None:
        """Get a variable from the current environment or parent."""
        if name in self.values:
            return self.values[name]
        if self.enclosing:
            return self.enclosing.get(name)
        return None

    def assign(self, name: str, value: Type) -> bool:
        """Assign an existing variable, searching in enclosing environments."""
        if name in self.values:
            self.values[name] = value
            return True
        if self.enclosing:
            return self.enclosing.assign(name, value)
        return False
