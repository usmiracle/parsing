from __future__ import annotations

class Environment:
    def __init__(self, enclosing: Environment | None = None):
        self.enclosing: Environment | None = enclosing # enclosing is the globals
        self.values: dict[str, str] = {}

    def define(self, name: str, value: str):
        """Define a new variable in the current environment."""
        self.values[name] = value

    def get(self, name: str) -> str | None:
        """Get a variable from the current environment or parent."""
        if name in self.values:
            return self.values[name]
        if self.enclosing:
            return self.enclosing.get(name)
        return None

    def assign(self, name: str, value: str) -> bool:
        """Assign an existing variable, searching in enclosing environments."""
        if name in self.values:
            self.values[name] = value
            return True
        if self.enclosing:
            return self.enclosing.assign(name, value)
        return False
