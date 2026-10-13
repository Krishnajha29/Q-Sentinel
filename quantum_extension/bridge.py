"""
Q-Sentinel Quantum Bridge:
CLI script designed to be invoked by the Node.js backend.
Runs either QAOA or Classical baseline and outputs pure JSON to stdout.
"""

import sys
import os
import json
import argparse
import time

# Ensure src directory is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from optimization_model import create_default_scenario, ScanningOptimizationModel, BandProfile
from classical_baseline import ClassicalSolvers
from qaoa_solver import QAOASolver

def run_bridge():
    parser = argparse.ArgumentParser(description="Q-Sentinel Quantum Optimization Bridge")
    parser.add_argument("--mode", type=str, choices=["qaoa", "classical", "both"], default="both")
    parser.add_argument("--p_layers", type=int, default=1)
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--maxiter", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    model = create_default_scenario()
    classical = ClassicalSolvers(model)

    output = {
        "timestamp": time.time(),
        "problem_spec": {
            "num_bands": model.num_bands,
            "bands": [
                {
                    "id": b.band_id,
                    "name": b.name,
                    "freq": b.freq_range_mhz,
                    "priority": b.priority,
                    "urgency": b.urgency,
                    "activity": b.activity_prob,
                    "cost": b.scan_cost,
                    "net_utility": round(model.get_band_utility(b), 3)
                } for b in model.bands
            ],
            "num_slots": model.num_slots,
            "budget": model.budget,
            "qubits": model.num_qubits,
            "state_space_size": 2 ** model.num_qubits
        }
    }

    # 1. Classical Exact & Baselines
    if args.mode in ["classical", "both"]:
        t0 = time.time()
        exact_res = classical.solve_exact()
        t_exact = (time.time() - t0) * 1000

        t0 = time.time()
        greedy_res = classical.solve_greedy()
        t_greedy = (time.time() - t0) * 1000

        t0 = time.time()
        ucb1_res = classical.simulate_recency_ucb1_batch()
        t_ucb1 = (time.time() - t0) * 1000

        output["classical"] = {
            "exact": {
                "utility": exact_res["best_feasible_solution"]["pure_utility"],
                "qubo_energy": exact_res["best_feasible_solution"]["qubo_energy"],
                "bitstring": exact_res["best_feasible_solution"]["bitstring"],
                "allocated_bands": exact_res["best_feasible_solution"]["allocated_bands"],
                "feasible_rate": 1.0,
                "runtime_ms": round(t_exact, 2),
                "total_feasible_in_space": exact_res["total_feasible_count"]
            },
            "greedy": {
                "utility": greedy_res["pure_utility"],
                "bitstring": greedy_res["bitstring"],
                "allocated_bands": greedy_res["allocated_bands"],
                "feasible": greedy_res["is_feasible"],
                "runtime_ms": round(t_greedy, 2)
            },
            "ucb1": {
                "utility": ucb1_res["pure_utility"],
                "bitstring": ucb1_res["bitstring"],
                "allocated_bands": ucb1_res["allocated_bands"],
                "feasible": ucb1_res["is_feasible"],
                "runtime_ms": round(t_ucb1, 2)
            }
        }

    # 2. Qiskit QAOA
    if args.mode in ["qaoa", "both"]:
        t0 = time.time()
        qaoa = QAOASolver(model, p_layers=args.p_layers)
        qaoa_res = qaoa.solve(maxiter=args.maxiter, shots=args.shots, seed=args.seed)
        t_qaoa = time.time() - t0

        output["qaoa"] = {
            "p_layers": args.p_layers,
            "shots": args.shots,
            "runtime_sec": round(t_qaoa, 2),
            "feasible_rate": qaoa_res["feasible_rate"],
            "best_feasible_utility": qaoa_res["best_feasible_solution"]["pure_utility"] if qaoa_res["best_feasible_solution"] else None,
            "best_feasible_bitstring": qaoa_res["best_feasible_solution"]["bitstring"] if qaoa_res["best_feasible_solution"] else None,
            "best_feasible_bands": qaoa_res["best_feasible_solution"]["allocated_bands"] if qaoa_res["best_feasible_solution"] else None,
            "top_bitstrings": qaoa_res["top_bitstrings"][:4],
            "optimal_parameters": qaoa_res["optimal_parameters"],
            "execution_mode": "Local Qiskit StatevectorSampler (Simulated Quantum Circuit)"
        }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    run_bridge()
