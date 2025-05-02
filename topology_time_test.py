import time
from src.circuits.TopologicalCircuit import TopologicalCircuit

start = time.time()

# 🔧 Тестируем производительность
circuit = TopologicalCircuit("test")
circuit.load_CIF("resources/input/adder2.cif")
circuit.compile()
circuit.graph_to_json("resources/output/graph_summin.json")

end = time.time()
circuit.visualize_trans([])
print(f"⏱ Выполнено за: {end - start:.5f} секунд")