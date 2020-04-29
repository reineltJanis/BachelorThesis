import argparse, sys, time, datetime, os, errno, csv, random, io
from pathlib import Path
from enum import Enum
import numpy as np

class Topology(Enum):
    DEFAULT     = 1
    STAR        = 2
    RING        = 3
    COMPLETE    = 4
    LIST        = 5

    def __str__(self) -> str:
        return self.name

DEFAULT_DEVIATION = 0.0
DEFAULT_MAX_VALUE = 1
DEFAULT_MIN_VALUE = -1
DEFAULT_MAX_DELTA = 0.75

def parse(name):
    parser = argparse.ArgumentParser(description=f"Run {name} example")
    parser.add_argument(
        "-n",
        "--nodes",
        type=int,
        help="Amount of nodes."
    )
    parser.add_argument(
        "-t",
        "--topology",
        type=lambda topology: Topology[topology],
        choices=list(Topology),
        default=Topology.DEFAULT,
        help=f"Topology used for the generation. Default: {Topology.DEFAULT}",
    )
    parser.add_argument(
        "-b",
        "--deviation",
        type=float,
        default=DEFAULT_DEVIATION,
        help=f"Maximum deviation from the general delta for each agent. Default: {DEFAULT_DEVIATION}",
    )
    parser.add_argument(
        "-d",
        "--delta",
        type=float,
        default=0.33,
        help=f"Maximum delta at the beginning (Max percentage from original max/min ). Defaults to '{DEFAULT_MAX_DELTA}'."
    ),
    parser.add_argument(
        "-max",
        "--max",
        type=float,
        default=DEFAULT_MAX_VALUE,
        help=f"Maximum delta for the mean of all nodes at each new cycle (Max percentage from original max/min ). Defaults to '{DEFAULT_MAX_DELTA}'."
    ),
    parser.add_argument(
        "-min",
        "--min",
        type=float,
        default=DEFAULT_MIN_VALUE,
        help=f"Minimum value for the reference signals. Defaults to '{DEFAULT_MIN_VALUE}'."
    ),
    parser.add_argument(
        "--float",
        help="If this flag is set max and min will be ignored. Distribution between -1 and 1."
    )
    parser.add_argument(
        "filepath",
        help="Uses the given filepath to create aa csv file at the specified location."
    )

    args = parser.parse_args()

    # args.file_path = os.path.join(args.log_dir, f"node_{args.host}.log")

    if args.nodes < 1:
        parser.error(f"Invalid amount of nodes (must be at least 1): {args.nodes}")
    if args.delta < 0:
        parser.error(f"invalid delta: {args.delta}")
    if args.deviation < 0:
        parser.error(f"invalid deviation: {args.deviation}")
    if args.delta > 1:
        parser.error(f"invalid delta: {args.delta}")
    try:
        directory = os.path.dirname(os.path.abspath(args.filepath))
        os.makedirs(directory)
        # f = open(os.path.abspath(args.filepath), "w+")
        # f.close()
    except OSError as e:
        if e.errno != errno.EEXIST:
            parser.error(f"Not able to create logile. Check permissions and path.\n{args.filepath}")

    return args

def write_values(writer: csv.DictWriter, file, data: np.ndarray):
    writer.writerow()

if __name__ == "__main__":
    """
    Generates new values randomly. Delta and Deviation can be parsed into the generation process.
    Max and min values are only the bounds for the initial reference signals, except force-bounds flag is set
    """
    args = parse("Random dataset generator")

    max_delta_each_k = 0.2

    max_difference = abs(args.max) + abs(args.min)

    #generate initial values
    last_row = np.random.uniform(args.min*args.delta, args.max*args.delta, size=(1,args.nodes))
    values = np.copy(last_row)
    delta_list = []
    deviation_list = np.zeros((1, args.nodes))
    while np.shape(values)[0] < 200:

        # generate delta for this cycle
        delta = np.random.uniform(-max_difference / 2, max_difference / 2) * max_delta_each_k
        delta_list.append(delta)

        # generate individual deviation for each agent
        deviation = args.deviation * np.random.uniform(-max_difference / 2, max_difference / 2, size=(1,args.nodes))
        deviation_list = np.concatenate((deviation_list, deviation))

        # calculate new row
        new_row = delta * np.ones(shape=(1,args.nodes)) + last_row + deviation

        if np.max(new_row) > args.max or np.min(new_row) < args.min:
            for val in np.nditer(new_row, op_flags = ['readwrite']):
                if val > args.max:
                    val[...] = args.max
                elif val < args.min:
                    val[...] = args.min
            
        # append new row to the the values
        values = np.concatenate((values, new_row))
        last_row = new_row

    np.savetxt(args.filepath + '.csv', values, delimiter=",")
    np.savetxt(args.filepath + '.delta.csv', delta_list, delimiter=",")
    np.savetxt(args.filepath + '.deviation.csv', deviation_list, delimiter=",")
    print(np.shape(values)[0])