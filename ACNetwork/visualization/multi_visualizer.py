from single_visualizer import plot_graph_single_run
import matplotlib.pyplot as plt
import numpy as np
import os, sys
from pathlib import Path
from timeit import default_timer as timer

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
    NODES = 50
    # base_path = Path(f"../results-a1-error01-n{NODES:02d}")
    base_path = Path(f"../results")
    plt.style.use('fivethirtyeight')
    if not base_path.exists():
        sys.exit(-1)
    for run in range(1,8):
        for dataset in range(1,6):
            result_path = Path(f"{base_path.absolute()}/res-run-{run}-{dataset}-n{NODES}.csv")
            input_path = Path(f"../data/run-{run}-{dataset}-n{NODES}.csv")

            if result_path.exists() and input_path.exists():
                start_time = timer()
                plot_graph_single_run(result_path, input_path, NODES)
                plt.close()
                end_time = timer()
                times = open('times.csv', 'a')
                times.write(result_path.name + ',' + str(end_time - start_time) + '\n')
                times.close()