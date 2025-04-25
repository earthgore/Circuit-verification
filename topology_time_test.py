import time
from src.circuits.TopologicalCircuit import TopologicalCircuit

start = time.time()

# 🔧 Тестируем производительность
circuit = TopologicalCircuit("test", "resources/input/adder2.cif")
circuit.setUp()
circuit.graphToJSON("resources/output/graph.json")

end = time.time()

print(f"⏱ Выполнено за: {end - start:.5f} секунд")