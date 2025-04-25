class Transistor:
    def __init__(self, gate, drain, source, type, id):
        self.gate = gate
        self.drain = drain
        self.source = source
        self.type = type
        self.id = id
        self.connections = set()
        self.gate_connections = set()

    def __str__(self):
        return f"{self.type}: {self.gate} {self.drain} {self.source}\n"