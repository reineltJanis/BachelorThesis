import logging, sys, time, threading, os, argparse
import numpy as np
from server2 import Server
from timeloop import Timeloop
from datetime import timedelta
from statistics import mean
import utility
from config import Config
from timeit import default_timer as timer
from multiprocessing import Manager


def log_status():
    logger = logging.getLogger(name="log_status")
    data = list(map(lambda s: s._j.state(), servers))
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
    
    if max_diff <= abs(np.mean(states) * precision):
        logging.getLogger(name='check_convergence').warning(f"Converged with precision {precision:.20f} at k={servers[0]._j.k():6d} for value {mean(states):16.12f}")
        # time.sleep(99999) # Sleep long TODO: Wait until programm exits

def insert_error(signals: np.ndarray, node_id, start_index, duration = 10):
    err = np.arange(start_index,start_index + duration, dtype=float)
    err = 2 * err
    np.cos(err,err)
    err = 10 * err
    err = err + 20
    signals[start_index:start_index+duration,node_id] += err
    return signals



if __name__ == "__main__":
    '''Primary simulation function for algorithm 2. see parser for more ionformation For more details see Doc of Algorithm 1'''
    # logging.basicConfig(filename='output.log', level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.WARN)

    np.seterr('raise')

    parser = argparse.ArgumentParser(description=f"Run main test.")
    parser.add_argument("filename", help="Filename")
    parser.add_argument('-c', '--config', default='../config/config1.json', help='Config file.' )
    error_group = parser.add_argument_group('error')
    error_group.add_argument('-e', '--error-on', action='store_true', help='If set, error will be used on given node.')
    error_group.add_argument('-en', '--error-node-id', type=int, default=0, action='store', help='Node id, where the error occurs.')
    error_group.add_argument('-ei', '--error-start-index', type=int, default=1, action='store', help='Start at reference signal x.')

    args = parser.parse_args()

    configs = Config.load(args.config)
    
    LOGGING = False
    NODES = len(configs)
    INTERVAL = 10
    DATAPATH = '../data/'
    MAX_ITERATIONS = 1200
    RESULT_PATH = '../results/'
    FILENAME = args.filename

    NETWORK_ID = 1
    m_1 = np.array([[0,1,0,0,0],[1,0,1,1,0],[0,1,0,1,1],[0,1,1,0,0],[0,0,1,0,0]], 'float')
    # u = np.array([13.,7,3,5])
    # u = np.random.rand(NODES)*100000000+7
    # u = np.random.randint(-10**10, 10**10, size=NODES)


    #load dataset
    path = os.path.abspath(os.path.join(DATAPATH,FILENAME))
    signals = np.loadtxt(path, delimiter=",")
    
    u = np.resize(signals[-1], NODES)

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
        manager = Manager()
        for i in range(NODES):
            # server of a2 has only the reference data of itself, while a1 got the whole data parsed
            signals_on_node = signals[:,configs[i].id]
            error = False
            if args.error_on and i == args.error_node_id:
                error = True
            servers.append(Server(configs[i], signals_on_node, outputs[i], INTERVAL, 5, MAX_ITERATIONS, beta=1.1, error_on=error, error_start=args.error_start_index, error_duration=10, max_retries=NODES*4, manager=manager, network_id=NETWORK_ID))

        start_time = None
        end_time = None
        try:
            tl = Timeloop()
            tl._add_job(log_status, interval=timedelta(milliseconds=5000))
            tl.start()
            start_time = timer()
            for s in servers:
                s.daemon = True
                s.start()

            while(True):
                data = list(map(lambda s: s._j.k(), servers))
                if(np.min(data) >= MAX_ITERATIONS):
                    break
                else:
                    time.sleep(1)
        finally:
            end_time = timer()
            tl.stop()
            for server in servers:
                server.join()
    finally:
        time.sleep(2)
        if LOGGING:
            for output in outputs:
                output.close()
        
    if LOGGING:   
        log_matrix = np.zeros((MAX_ITERATIONS, NODES))
        for i in range(NODES):
            column = np.loadtxt(f"../logs/n{i}.log")
            # column = np.reshape(column, MAX_ITERATIONS)
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
    