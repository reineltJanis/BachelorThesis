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
    
    labels = []
    convergences = [{},{}]

    for i in [5,15,30]:
        for mode in ['default', 'error00', 'error01', 'error50', 'star', 'ring']: 
            for algorithm in range(1,3):
                if mode != 'default' and i>=15:
                    break

                base_path = Path(f"../results-a{algorithm}-{mode}-n{i:02d}")
                # print(basepath)
                if base_path.exists():
                    mode_str = mode.upper()[0] if not mode.startswith('error') else mode.upper()[0] + mode[-2:]
                    label = f"A{algorithm}\n{mode_str}\nN{i}"
                    labels.append(label)

                    #calculating first convergences
                    first_convergence_1 = []
                    first_convergence_01 = []
                    first_convergence_00001 = []
                    for run in range(1,8):
                        for dataset in range(1,6):
                            result_path = Path(f"{base_path.absolute()}/res-run-{run}-{dataset}-n{i}.csv")
                            input_path = Path(f"../data/run-{run}-{dataset}-n{i if i != 30 else 50}.csv")

                            if result_path.exists() and input_path.exists():
                                res_data = np.loadtxt(result_path.absolute(), delimiter=',')
                                
                                res_ptp = np.ptp(res_data, axis=1)
                                res_mean = np.abs(np.mean(res_data, axis=1))

                                k = np.argmax(np.dot(res_mean, 0.1) > res_ptp)
                                first_convergence_1.append(k if k > 0 else 1200)

                                k = np.argmax(np.dot(res_mean, 0.01) > res_ptp)
                                first_convergence_01.append(k if k > 0 else 1200)

                                k = np.argmax(np.dot(res_mean, 0.00001) > res_ptp)
                                first_convergence_00001.append(k if k > 0 else 1200)
                    # Adding means to data
                    if len(first_convergence_1) > 0 and len(first_convergence_01) > 0 and len(first_convergence_00001) > 0:
                        convergences[algorithm-1][label] = (int(np.round(np.mean(first_convergence_1))),int(np.round(np.mean(first_convergence_01))),int(np.round(np.mean(first_convergence_00001))))
                    else:
                        labels.remove(label)

    x = np.arange(len(labels)/2)*2

    data_1 = (list(map(lambda item: item[1][0], convergences[0].items())), list(map(lambda item: item[1][0], convergences[1].items())))
    data_01 = (list(map(lambda item: item[1][1], convergences[0].items())),list(map(lambda item: item[1][1], convergences[1].items())))
    data_00001 = (list(map(lambda item: item[1][2], convergences[0].items())),list(map(lambda item: item[1][2], convergences[1].items())))

    # if len(data_01) > 0:
    #     data_1 = np.mean(data_1)
    #     data_01 = np.mean(data_01)
    #     data_00001 = np.mean(data_00001)

    print(data_1)
    print(data_01)
    print(data_00001)
    print(labels)
    print(x)

    plt.style.use('fivethirtyeight')
    
    fig = plt.figure(1, figsize=(16,12))

    ax = fig.add_subplot(111)

    width = 0.3
    for i in range(2):
        rects = ax.bar(x+i-width, data_1[i], width=width, align='center')
        autolabel(rects, plt)
        
        rects = ax.bar(x+i, data_01[i], width=width, align='center')
        autolabel(rects, plt)
        
        rects = ax.bar(x+i+width, data_00001[i], width=width, align='center')
        autolabel(rects, plt)

    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels)
    
    
    ax.set_title('Average k until first consensus')
    ax.set_ylabel('k', size=16)
    ax.legend(labels=['A1: 0.1', 'A1: 0.01', 'A1: 0.00001','A2: 0.1', 'A2: 0.01', 'A2: 0.00001'])
    fig.savefig("graphics/total_convergence.png", dpi=300)
    plt.show()


    