from single_visualizer import plot_graph_single_run
import matplotlib.pyplot as plt
import numpy as np
import os, sys
from pathlib import Path

def plot_covergence_graph(base_path):
    for run in range(1,8):
        for dataset in range(1,6):
            result_path = Path(f"{base_path.absolute()}/res-run-{run}-{dataset}-n{50}.csv")
            input_path = Path(f"../data/run-{run}-{dataset}-n{50}.csv")

            if result_path.exists() and input_path.exists():
                plot_graph_single_run(result_path, input_path, NODES)
                plt.close()



if __name__ == "__main__":
    ''' Creates the single visualizations for each run in a given base_path'''
    NODES = 5
    # base_path = Path(f"../results-a1-error01-n{NODES:02d}")
    base_path = Path(f"../results-a1-error50-n05")
    plt.style.use('fivethirtyeight')
    if not base_path.exists():
        sys.exit(-1)
    for run in range(1,8):
        for dataset in range(1,6):
            result_path = Path(f"{base_path.absolute()}/res-run-{run}-{dataset}-n{NODES}.csv")
            input_path = Path(f"../data/run-{run}-{dataset}-n{NODES}.csv")

            if result_path.exists() and input_path.exists():
                plot_graph_single_run(result_path, input_path, NODES)
                plt.close()