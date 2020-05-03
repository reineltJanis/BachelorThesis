import matplotlib.pyplot as plt
import numpy as np
import os, sys, math
from pathlib import Path
from timeit import default_timer as timer

MAX_ITERATIONS = 1200

def plot_graph_single_run(res_path: Path, in_path: Path, nodes, display=False):

    # loading logged data 
    res_data = np.loadtxt(res_path.absolute(), delimiter=',')
    in_data = np.loadtxt(in_path.absolute(), delimiter=',', usecols=range(0,np.shape(res_data)[1]))
    in_data_k = np.repeat(in_data, np.append(np.repeat(5, np.shape(in_data)[0]-1), 205), axis = 0)
    mean = np.mean(in_data, axis=1)
    mean_k = np.repeat(mean, np.append(np.repeat(5, np.shape(mean)[0]-1), 205), axis = 0)
    # max_error = np.dot(np.abs(np.max(np.abs(res_data - np.resize(mean_k, np.shape(res_data))),axis=1)/mean_k), 100)

    nodes = np.shape(res_data)[1]

    # % Difference
    # max_rel_difference= np.dot(np.ptp(res_data, axis=1)/(np.abs(max_value_at_k) + np.abs(min_value_at_k)),100)
    max_rel_difference = np.abs(np.ptp(res_data, axis=1)/(np.max(res_data, axis=1) + np.min(res_data, axis=1)))
    for r , val in np.ndenumerate(max_rel_difference):
        if val > 1:
            max_rel_difference[r] = np.reciprocal(val)

    max_rel_difference = np.dot(max_rel_difference, 200)

    # %Error    
    state_mean_vs_real_mean = np.dot(np.abs((np.mean(res_data, axis=1) - mean_k)/mean_k), 100)

    convergence_rates = np.full(np.shape(res_data), np.nan)
    # Convergence Rate
    for index, state in np.ndenumerate(res_data):
        row_index = index[0]
        column_index = index[1]
        if row_index%5<2 or row_index%5 > 3:
            continue
        if not (res_data[row_index-2, column_index] == res_data[row_index-1, column_index]
        or res_data[row_index-1, column_index] == res_data[row_index, column_index]):
            convergence_rates[row_index, column_index] = (
                np.log(
                    np.abs(
                        (res_data[row_index+1, column_index] - state) / (state - res_data[row_index-1, column_index])
                    )) 
                / np.log(
                    np.abs(
                        (state - res_data[row_index-1, column_index]) / (res_data[row_index-1, column_index] - res_data[row_index-2, column_index])
                    )
                )
            )
    
    convergence_rates = np.nanmean(convergence_rates, axis=1)

    convergence_means = {}

    for index, mean in enumerate(convergence_rates):
        if(not np.isnan(mean)):
            convergence_means[index] = mean
                


    # percentage_diff_state_diff_input = np.dot(np.divide(np.ptp(res_data, axis=1), np.ptp(in_data_k, axis=1)), 100.0)
    print(np.ptp(in_data_k[:12,:], axis=1))
    print(np.ptp(res_data[:12,:], axis=1))

    fig, axes = plt.subplots(3,1, sharex=True, figsize=(16,12))


    # for x-axis : k
    k = np.arange(start=0, stop=np.shape(res_data)[0])
    # for in_data ( only 200 lines, new data at each k%5==0)
    k_in = np.arange(start=0, stop=np.shape(in_data)[0]*5, step=5)

    # generate parameters for plot
    for i in range(nodes):
        # adding all states to plot
        if i ==0:
            axes[0].plot(k, res_data[:,i], color='blue', linewidth=.1, label='State of node')
        else:
            axes[0].plot(k, res_data[:,i], color='blue', linewidth=.1)
        axes[1].plot(k, res_data[:,i], color='blue', linewidth=.2)
        # adding input signals to plot
        if i == 0:
            axes[0].plot(k_in, in_data[:,i], color='red', marker='x', markersize=2, linewidth=0.1, label='Reference signals')
        else:
            axes[0].plot(k_in, in_data[:,i], color='red', marker='x', markersize=2, linewidth=0.1)


    axes[1].plot(k, mean_k, 'g_', markersize=6, label='real mean')

    axes[2].plot(k, max_rel_difference, 'k', marker='x', markersize=3, label='Max % difference (states)', linewidth=0.3)
    axes[2].plot(k, state_mean_vs_real_mean, color='orange', label='%Error states mean', linewidth=1)
    # axes[2].plot(k, percentage_diff_state_diff_input, color='brown', label='Diff States / Diff Input', linewidth=1)
    axes[2].plot(list(convergence_means.keys()), list(convergence_means.values()), color='brown', label='Convergence', linewidth=1)

    # generate graph
    fig.suptitle(f"{res_path.parent.name}: {in_path.stem}")
    axes[0].grid(True)
    axes[2].grid(True)
    axes[0].set_ylabel('value', fontsize=10)
    axes[0].set_title('States and reference signals vs k', fontsize=12)
    axes[1].set_ylabel('value', fontsize=10)
    axes[1].set_title('Reference signals and true average vs k', fontsize=12)
    axes[2].set_xlabel('k', fontsize=10)
    axes[2].set_ylabel('%', fontsize=10)
    axes[2].set_title('Deviations', fontsize=12)
    axes[2].set_ylim(-10,110)

    legend = fig.legend()
    os.makedirs(f"graphics/{res_path.parent.name}", exist_ok=True)
    fig.savefig(f"graphics/{res_path.parent.name}/{res_path.stem}.png", dpi=500)
    axes[2].set_xlim(-5,120)
    fig.set_size_inches(8,8)
    legend.remove()
    # fig.savefig(f"graphics/{res_path.parent.name}/{res_path.stem}.start.png", dpi=300)
    if display:
        fig.show()
        plt.show()



if __name__ == "__main__":
    ''' The time recording was performed by the multi_visualizer! '''
    NODES = 15
    RUN = 2
    SET = 4
    result_path = Path(f"../results/res-run-{RUN}-{SET}-n{50}.csv")
    input_path = Path(f"../data/run-{RUN}-{SET}-n{50}.csv")
    # print(plt.style.available)
    plt.style.use('fivethirtyeight')
    if not result_path.exists() or not input_path.exists():
        print('File does not exist.')
        sys.exit(-1)
    plot_graph_single_run(result_path, input_path, NODES, False)
