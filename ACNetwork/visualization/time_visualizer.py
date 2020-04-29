import matplotlib.pyplot as plt
import numpy as np
import os, sys, csv
from pathlib import Path

def plot_time_bar(times_path: Path, nodes: int):
    # loading logged data 
    
    with open(times_path.absolute(), mode='r') as infile:
        reader = csv.reader(infile)
        times_data = {str(rows[0]):float(rows[1]) for rows in reader}


    labels = list(map(lambda k: os.path.splitext(k)[0], times_data.keys()))
    print(labels)
    values = np.array(list(times_data.values()))

    fig, axes = plt.subplots(figsize=(16,12))

    # Add bars
    rects_list = []
    # for i in range(7):
    rects = axes.bar(labels, values, align='center', alpha=0.5)
    rects_list.append(rects)
    axes.set_ylabel('time in s')
    plt.xticks(labels, rotation=90)

    # # generate parameters for plot
    # for i in range(nodes):
    #     # adding all states to plot
    #     if i ==0:
    #         axes[0].plot(k, res_data[:,i], color='blue', linewidth=.1, label='State of node')
    #     else:
    #         axes[0].plot(k, res_data[:,i], color='blue', linewidth=.1)
    #     axes[1].plot(k, res_data[:,i], color='blue', linewidth=.1)
    #     # adding input signals to plot
    #     if i == 0:
    #         axes[0].plot(k_in, in_data[:,i], color='red', marker='x', markersize=2, linewidth=0.1, label='Reference signals')
    #     else:
    #         axes[0].plot(k_in, in_data[:,i], color='red', marker='x', markersize=2, linewidth=0.1)


    # axes[1].plot(k, mean_k, 'g_', markersize=6, label='real mean')

    # axes[2].plot(k, max_rel_difference, 'k', marker='x', markersize=3, label='Max % difference (states)', linewidth=0.1)
    # axes[2].plot(k, state_mean_vs_real_mean, color='orange', label='%Error states mean', linewidth=1)
    # axes[2].plot(k, percentage_diff_state_diff_input, color='brown', label='Diff States / Diff Input', linewidth=1)

    # generate graph
    # axes.grid(True)
    # axes.set_ylabel('value', fontsize=10)

    fig.suptitle(f"{times_path.parent.name}: {times_path.stem}")
    axes.set_title('Execution time until all nodes reach state 1200', fontsize=12)
    fig.subplots_adjust(bottom=0.2)
    autolabel(rects, axes)
    fig.legend()
    os.makedirs(f"graphics/{times_path.parent.name}", exist_ok=True)
    fig.savefig(f"graphics/{times_path.parent.name}/{times_path.stem}.png", dpi=200)
    fig.show()
    plt.show()

# From https://matplotlib.org/3.1.1/gallery/lines_bars_and_markers/barchart.html#sphx-glr-gallery-lines-bars-and-markers-barchart-py
def autolabel(rects, axes):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        axes.annotate('{}'.format(int(np.round(height,0))),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


if __name__ == "__main__":
    NODES = 5
    RUN = 1
    SET = 1
    times_path = Path(f"../results-a1-default-n05/times.csv")
    # print(plt.style.available)
    plt.style.use('fivethirtyeight')
    if not times_path.exists():
        print('File not found.')
        sys.exit(-1)
    plot_time_bar(times_path, NODES)