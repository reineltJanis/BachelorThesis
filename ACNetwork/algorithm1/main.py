import logging, sys, time, threading, os, argparse
import numpy as np
from server import Server
from timeloop import Timeloop
from datetime import timedelta
from statistics import mean
import utility
from config import Config
from timeit import default_timer as timer


def log_status():
    logger = logging.getLogger(name="log_status")
    data = list(map(lambda s: s._j.states(), servers))
    logger.warning(" States:\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}".format(*data))
    data = list(map(lambda s: s._j.k(), servers))
    logger.warning(" with K:\t{:12d}\t{:12d}\t{:12d}\t{:12d}\t{:12d}\n".format(*data))

def check_convergence(precision = 10**-10):
    """ Checks if the algorithm has converged to a value given a certain precision.
        The precision refers to a percentage.
        precision = 0.1 == 0.1%
    """
    states = list(map(lambda s: s._j.state(), servers))
    max_diff = np.max(states) - np.min(states)

    # for i in range(1, len(states)):
    #     if states[i]- min_element > max_diff:
    #         max_diff = states[i] - min_element
        
    #     if states[i] < min_element:
    #         min_element = states[i]
    
    if max_diff <= abs(np.mean(states) * precision):
        logging.getLogger(name='check_convergence').warning(f"Converged with precision {precision:.20f} at k={servers[0]._j.k():6d} for value {mean(states):16.12f}")
        # time.sleep(99999) # Sleep long TODO: Wait until programm exits

if __name__ == "__main__":
    '''Primary simulation function for algorithm 1. see parser for more ionformation'''
    # logging.basicConfig(filename='output.log', level=logging.DEBUG) # will print debug output to file
    logger = logging.getLogger()
    logger.setLevel(logging.WARN) #more details when turned on info or debug

    np.seterr('raise')

    # parser to get input args
    parser = argparse.ArgumentParser(description=f"Run main test.")
    parser.add_argument("filename", help="Filename")
    parser.add_argument('-c', '--config', default='../config/config1.json', help='Config file.' )
    error_group = parser.add_argument_group('error')
    error_group.add_argument('-e', '--error-on', action='store_true', help='If set, error will be used on given node.')
    error_group.add_argument('-en', '--error-node-id', type=int, default=0, action='store', help='Node id, where the error occurs.')
    error_group.add_argument('-ei', '--error-start-index', type=int, default=1, action='store', help='Start at reference signal x.')

    args = parser.parse_args()

    #includes topology, neighbors etc. generated with ../config/config.py
    configs = Config.load(args.config)

    LOGGING = False
    NODES = len(configs)
    INTERVAL = 10
    DATAPATH = '../data/'
    MAX_ITERATIONS = 1200
    RESULT_PATH = '../results/'
    FILENAME = args.filename

    NETWORK_ID = 4
    m_1 = np.array([[0,1,0,0,0],[1,0,1,1,0],[0,1,0,1,1],[0,1,1,0,0],[0,0,1,0,0]], 'float')
    # u = np.array([13.,7,3,5])
    # u = np.random.rand(NODES)*100000000+7
    # u = np.random.randint(-10**10, 10**10, size=NODES)

    #load dataset
    path = os.path.abspath(os.path.join(DATAPATH,FILENAME))
    signals = np.loadtxt(path, delimiter=",", usecols=range(0, NODES))

    # last reference signal set for comparison at the end
    u = signals[-1]

    if not os.path.exists('../logs'):
        os.makedirs('../logs')
    
    outputs = []
    for i in range(NODES):
        if LOGGING:
            outputs.append(open(f'../logs/n{i}.log', 'w+'))
        else:
            outputs.append(None)

    try:
        ''' Creating nodes. '''
        servers = []
        for i in range(NODES):
            signals_on_node = signals[:,configs[i].id]
            error = False
            if args.error_on and i == args.error_node_id:
                error = True
            servers.append(Server(configs[i], signals_on_node, outputs[i], INTERVAL, 5, MAX_ITERATIONS, error, args.error_start_index, 10, network_id=NETWORK_ID))
            
        # runs timer based job for analysis
        tl = Timeloop()
        # adding analysis jobs
        # tl._add_job(log_status, timedelta(milliseconds=1200))
        # tl._add_job(check_convergence, timedelta(milliseconds=100))
        start_time = None
        end_time = None
        try:
            start_time = timer()
            for s in servers:
                s.start()

            while(True):
                data = list(map(lambda s: s._j.k(), servers))
                if(np.min(data) >= MAX_ITERATIONS):
                    break
                else:
                    time.sleep(2)
        finally:
            end_time = timer()
            for server in servers:
                server.stop()
    finally:
        time.sleep(2)
        if LOGGING:
            for output in outputs:
                output.close()
          
    # generate result csv with all state data
    if LOGGING:   
        log_matrix = np.zeros((MAX_ITERATIONS, NODES))
        for i in range(NODES):
            column = np.loadtxt(f"../logs/n{i}.log")
            print(column)
            log_matrix[:,i] = column

    if LOGGING:
        os.makedirs(RESULT_PATH, exist_ok=True)
        outpath = os.path.join(RESULT_PATH, 'res-' + FILENAME)
        np.savetxt(outpath, log_matrix, delimiter=',')
        times = open(os.path.join(RESULT_PATH, 'times.csv'), 'a')
        times.write(FILENAME + ', ' + str(end_time - start_time) + '\n')
        times.close()

    print('\n\n\n') # print final results
    print(f"Real:\t{u}\t = {np.average(u)}")
    print(f"States:\t{list(map(lambda s: s._j.state(), servers))}")
    print(f"K:\t{list(map(lambda s: s._j.k(), servers))}")
    print('\n\n\n')
    