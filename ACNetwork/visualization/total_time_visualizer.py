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
    
    plt.style.use('fivethirtyeight')
    
    fig = plt.figure(1, figsize=(16,12))
    labels = []

    width = .9
    for i in [5,15,30,50]:
        for mode in ['default', 'error00', 'error01', 'error50', 'star', 'ring']:
            for algorithm in range(1,3):
                if i >= 15 and mode != 'default':
                    break
                times_path = Path(f"../results-a{algorithm}-{mode}-n{i:02d}/times.csv")
                print(times_path)
                if times_path.exists():
                    label = f"A{algorithm}\n{str(mode).upper()}\n{i} nodes"
                    labels.append(label)
                    data = np.loadtxt(times_path.absolute(), usecols=1, delimiter=', ')

                    rects = plt.bar(label, np.mean(data)/i, width=width, align='center')
                    autolabel(rects, plt)

    fig.suptitle('Average runtime per node (35 datasets)')
    plt.xticks(labels, rotation=0, size=8)
    plt.ylabel('time in s', size=16)
    fig.subplots_adjust(bottom=0.1)
    fig.savefig(f"graphics/total_times.png", dpi=200)
    plt.show()

