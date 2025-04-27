import time
from src.circuits.ElectricalСircuit import ElecrticalCircuit

start = time.time()

# 🔧 Тестируем производительность
circuit = ElecrticalCircuit("test")
circuit.load_NET("resources/input/sum.net")
circuit.compile()
circuit.graph_to_json("resources/output/el_graph.json")

end = time.time()

print(f"⏱ Выполнено за: {end - start:.5f} секунд")