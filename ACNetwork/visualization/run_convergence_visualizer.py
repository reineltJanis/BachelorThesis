import matplotlib.pyplot as plt
import numpy as np
import os, sys, csv
from pathlib import Path

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
    MODE = 'default'

    
    labels = []
    convergences = {}

    for i in [5,15,30]:
        for run in range(1,8):
            for algorithm in range(1,3):
                base_path = Path(f"../results-a{algorithm}-{MODE}-n{i:02d}")
                # print(basepath)
                if base_path.exists():
                    label = f"A{algorithm}\nType {str(run).upper()}\n{i} nodes"
                    labels.append(label)

                    #calculating first convergences
                    first_convergence_1 = []
                    first_convergence_01 = []
                    first_convergence_00001 = []
                    for dataset in range(1,6):
                        result_path = Path(f"{base_path.absolute()}/res-run-{run}-{dataset}-n{NODES}.csv")
                        input_path = Path(f"../data/run-{run}-{dataset}-n{NODES}.csv")

                        if result_path.exists() and input_path.exists():
                            res_data = np.loadtxt(result_path.absolute(), delimiter=',')
                            
                            res_ptp = np.ptp(res_data, axis=1)
                            res_mean = np.abs(np.mean(res_data, axis=1))

                            k = np.argmax(np.dot(res_mean, 0.1) > res_ptp)
                            first_convergence_1.append(k if k > 0 else 1200)

                            k = np.argmax(res_mean * 0.01 > res_ptp)
                            first_convergence_01.append(k if k > 0 else 1200)

                            k = np.argmax(res_mean * 0.00001 > res_ptp)
                            first_convergence_00001.append(k if k > 0 else 1200)
     
                    convergences[label] = (int(np.round(np.mean(first_convergence_1))),int(np.round(np.mean(first_convergence_01))),int(np.round(np.mean(first_convergence_00001))))


    x = np.arange(len(labels))

    data_1 = list(map(lambda item: item[1][0], convergences.items()))
    data_01 = list(map(lambda item: item[1][1], convergences.items()))
    data_00001 = list(map(lambda item: item[1][2], convergences.items()))

    print(data_1)
    print(data_01)
    print(data_00001)
    print(labels)
    print(x)

    plt.style.use('fivethirtyeight')
    
    fig = plt.figure(1, figsize=(16,12))

    ax = fig.add_subplot(111)

    width = 0.3

    rects = ax.bar(x-width, data_1, width=width, align='center', log=1)
    autolabel(rects, plt)
    
    rects = plt.bar(x, data_01, width=width, align='center', log=2)
    autolabel(rects, plt)
    
    rects = plt.bar(x+width, data_00001, width=width, align='center', log=3)
    autolabel(rects, plt)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    
    
    ax.set_title('Average k until first consensus')
    ax.set_ylabel('k', size=16)
    ax.legend(labels=['0.1', '0.01', '0.00001'])
    fig.savefig("graphics/run_convergence_total.png", dpi=200)
    plt.show()


    