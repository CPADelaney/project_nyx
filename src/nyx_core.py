# src/nyx_core.py

from src.self_analysis import main as analyze
from src.optimization_engine import generate_optimization_suggestions
from analysis.self_writer import apply_suggestions

def nyx_core_loop():
    print("NYX CORE: Beginning self-improvement cycle...")
    analyze()
    generate_optimization_suggestions()
    apply_suggestions()
    print("NYX CORE: Optimization cycle complete.")

if __name__ == "__main__":
    nyx_core_loop()
