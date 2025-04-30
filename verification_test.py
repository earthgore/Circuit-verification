from src.circuits.verification import verification

if __name__ == "__main__":
    verification("resources/input/sum.net", "sum", "resources/input/adder2_broken.cif", "sum")