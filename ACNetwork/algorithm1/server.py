import random, logging, sys, struct, json, errno, time, decimal, utility, csv, requests
import numpy as np
from j import J
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from multiprocessing import Process, Manager, Lock, Value
from threading import Thread
from timeloop import Timeloop
from datetime import timedelta
from config import Config
from datetime import datetime

@utility.auto_str
class Server(object):
    def __init__(self, config: Config, signals: np.ndarray, output = None, interval = 1000, new_reference_signal_each_k = 5, max_iterations = 1200, error_on = False, error_start = 0, error_duration = 10, network_id = 2):
        """
            Creates a Server object using:
            str:host\t host address
            int:port\t port where server runs
            int:id\t ID of the Server (used in numpy to locate position in matrix)
            np.array: adjacency\t Adjacency matrix of the whole/sub system
            int:signal\t Initial value for the node to start
            dict:out_neighbors\t contains all outneighbor host addresses in key property
            bool: instant_start\t whether the server should start immediately

            Returns: Server(object).
        """

        logger = logging.getLogger(name='Server.__init__')

        manager = Manager() # used to synchronize data between processes and threads
        self._host = config.host
        self._port = config.port
        self.__address = (config.host, config.port)
        self._adjacency = config.adjacency
        self._id = config.id
        self._laplacian = utility.calculate_laplacian(self._adjacency)
        if not utility.check_laplacian(self._laplacian):
            raise BaseException("No valid laplacian")
        # self._beta = 1/np.max(np.linalg.eigvals(self._laplacian)) # calculates beta, moved to utility
        self._beta = utility.calculate_beta(self._laplacian)
        self._server_socket = socket(AF_INET, SOCK_STREAM)
        self._server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._server_socket.bind(self.__address)
        self._j = J(0, signals[0], config.out_neighbors, manager)
        self._neighbor_states = manager.dict()
        self._interval = interval
        self._interval_sec = float(interval / 1000.0)
        self.__signals = signals
        self._new_reference_signal_each_k = new_reference_signal_each_k
        self.__output = output
        self.__max_iterations = max_iterations
        self.__running = False
        self.__neighbor_out_connections = manager.dict()
        self.__error_on = error_on
        self.__error_start = error_start
        self.__error_duration = error_duration
        self.__API_URL = 'http://10.0.2.2:7071'
        self.__NETWORK_ID = network_id
        self.__API_QUEUE = manager.list()
        self.__API_QUEUE_LOCK = Lock()
        
        self.__tl = Timeloop() # allows to start recurring threads in a given time interval
        if config.instant_start:
            self.start()
        # logger.debug(self)
        logger.warn(f"Using beta {self._beta:24.20f}")

    def start(self):
        ''' Starting server, acccept process and broadcast Threads. '''
        if self.__running:
            return
        try:
            self.__running = True
            self._server_socket.listen(500)
            self.accept_process = Process(target=self.accept_connections)
            self.accept_process.daemon = True
            self.accept_process.start()
            self.__tl._add_job(self.broadcast, interval=timedelta(milliseconds=self._interval))
            self.__tl._add_job(self.callApi, interval=timedelta(seconds=2))
            self.__tl.start()
        except BaseException as e:
            logging.getLogger(name='start').error(str(e))
            self.stop()

    def stop(self):
        ''' Stopping all processes and threads. '''
        if not self.__running:
            return
        self.__running = False
        # self.accept_process.terminate()
        self.accept_process.join(2)
        self._server_socket.close()

    def accept_connections(self):
        ''' Waits for new connections. Creates a handling Thread for all new connections. '''
        logger = logging.getLogger(name='Server:accept_connections')
        while True:
            try:
                logger.info("Waiting for new connection...")
                client, client_address = self._server_socket.accept()
                if self._j.k() < self.__max_iterations:
                    thread = Thread(target=self.handle_connection, args=(client,client_address))
                    thread.daemon = True
                    logger.info(f"Retrieving information from\t{client_address}\tat host {self.__address}")
                    thread.start()
                else:
                    return
            except IOError as e:
                if e.errno == errno.EPIPE:
                    return
                logger.error(str(e))

    def handle_connection(self, client: socket, client_address:(str, int)):
        ''' Handles each incomming connection and stores the message. '''
        logger = logging.getLogger(name='Server:handle_connection')
        while True:
            try:
                msg = self.receive(client)
                sender = msg[0]
                key = msg[2]
                state = msg[1]

                self._neighbor_states[(sender, key)] = state # sample item created: (('127.0.0.1', 4), 451.75)
                
                logger.info(f"[{self._host}]: Stored [{(sender, key)}]: {str(state)}")
                logger.debug(f"Node {self._id} has states {self._neighbor_states}")
                if key == self.__max_iterations:
                    break
            except OSError as e:
                if e.errno == errno.EPIPE:
                    break
                else:
                    logger.error(e)

    # @self.__tl.job(interval=timedelta(milliseconds=args.time))
    def broadcast(self):
        ''' Gets called by the Timeloop class. Creates a Thread which handles computation of new state and broadcasting. '''
        try:
            if self._j.k() < self.__max_iterations:
                # use the following to start the broadcast function as a new threat -> timeloop will continoue immediately and does not wait until finished
                # logging.getLogger(name='Server:broadcast').info("broadcast job current time: %s with data: %s" % (time.ctime(), str(self._neighbor_states)))
                # thread = Thread(target=self.broadcast_thread) #, args=(self._j, self._neighbor_states, self._adjacency)
                # thread.daemon = True
                # thread.start()
                # use this to have only one broadcast thread at once
                self.broadcast_thread()
            else:
                self.stop()
        except OSError as e:
            if e.errno == errno.EPIPE or e.errno == errno.ECONNRESET:
                self.stop()
            else:
                raise e

    def broadcast_thread(self):
        ''' Initially sends message to all neighbor nodes. Calculates new state each round and distributes it. '''
        logger = logging.getLogger(name='Server:broadcast_thread')
        relevant_states = dict(filter(
            lambda elem: elem[0][1] == self._j.k(),
            self._neighbor_states.items()
        )) # states with same k as own state 
        relevant_states = dict(map(
            lambda elem: (elem[0][0],float(elem[1])),
            relevant_states.items()
        )) # map dict to remove k from key variable (tuple): ((str, int), float) -> (str, float)

        if self._j.k() == 0:
            logger.info(f"Node {self._id} initially broadcasts its value.")
            self.distribute_state()

        x = np.zeros(np.shape(self._adjacency)[0])
        if len(relevant_states) == len(self._j.neighbors):
            logger.debug(f"{self._j.neighbors.items()}")
            for neighbor in relevant_states.keys():
                i = self._j.neighbors[neighbor]
                logger.info(f"{neighbor} > {i}")
                np.put(x, int(i), relevant_states[neighbor])

            np.put(x, self._id, self._j.state())

            # loading new reference signals
            sig_nr = int(self._j.k()/self._new_reference_signal_each_k)
            if self._j.k() > 0 and sig_nr < 200:
                if self._j.k() % self._new_reference_signal_each_k == 0:
                    self._j.set_reference_signal(self.__signals[sig_nr])
                else:
                    self._j.set_reference_signal(self._j.reference_signal())

            # calculating new state
            x_new = utility.calculate_iteration(self._id, self._laplacian, x, self._j.diff(), self._beta)
            self._j.increment_k()
            self._j.set_state(x_new)
            self.distribute_state()
            
            # add log to api queue
            with self.__API_QUEUE_LOCK:
                self.__API_QUEUE.append(
                    {
                        'nodeId': self._host,
                        'port': self._port,
                        'state': float(np.real(x_new)),
                        'neighborStates': relevant_states,
                        'iteration': self._j.k(),
                        'timestamp': datetime.utcnow().__str__(),
                        'networkId': self.__NETWORK_ID,
                        'referenceSignal': self._j.reference_signal()
                    }
                )
            

            logger.debug(f" UPDATED: Node {self._id}: {self._j.state()} | Others: {self._neighbor_states}")

            # log to output if specified
            if self.__output != None:
                try:
                    self.__output.write(str(float(self._j.state())) + '\n')
                except BaseException as e:
                    logger.error("Unable to wirte to output.\n" +  str(e))
        else:
            logger.info('Rebroadcasting on node: ' + self._host)
            self.distribute_state() # sends the new state to the neighbor nodes
            time.sleep(self._interval_sec)
        

        ''' Removes all data from previous calculations (session_key < k). '''
        states_to_remove = dict(filter(
            lambda elem: elem[0][1] < self._j.k(), # elem[0] is key of dict and consists of node name and session key k
            self._neighbor_states.items()
        ))
        
        for state in states_to_remove.items():
            try:
                del self._neighbor_states[state[0]]
            except KeyError:
                logger.warn(f"Key '{state[0]}' not found.")

    def distribute_state(self):
        ''' Sends the current state to all neighbor nodes. '''
        if self._j.k() >= self.__max_iterations:
            return
        for neighbor in self._j.neighbors.keys():
            try:
                if neighbor not in self.__neighbor_out_connections:
                    if (neighbor, self.__max_iterations) not in self._neighbor_states:
                        client_socket = socket(AF_INET, SOCK_STREAM)
                        client_socket.connect((neighbor, self._port))
                        self.__neighbor_out_connections[neighbor] = client_socket
                    else:
                        continue

                # adding error to own signal if selected
                error = 0.0
                if self.__error_on:
                    if self._j.k() >= self.__error_start and self._j.k() < self.__error_duration:
                        error = utility.calculate_error(self._j.k())
                        logging.debug(f"Adding error on node {self._id}: {error}")
                self.send(self.__neighbor_out_connections[neighbor], message=(self._host, float(self._j.state()+error), self._j.k()))
            except Exception as e:
                logging.getLogger(name='Server:distribute_state').debug(str(e))
                try:
                    self.__neighbor_out_connections[neighbor].close()
                except Exception as e:
                    pass
                finally:
                    del self.__neighbor_out_connections[neighbor]
                    logging.getLogger(name='Server:distribute_state').warn('Deleting sockeet connection for ' + neighbor)


    def send(self, channel: socket, message: object ):
        ''' Sends a message to another socket using JSON. '''
        try:
            msg = json.dumps(message)
            logging.info(f"sending data from {self._host}:\t{msg}")
            channel.send(struct.pack("i", len(msg)) + bytes(msg, "utf8"))
            return True
        except OSError as e:
            logging.error(e)
            return False

    def receive(self, channel: socket ) -> (str, float, int):
        ''' Receives a message from another socket using JSON. '''
        recv = channel.recv(struct.calcsize("i"))
        if len(recv) < 4:
            raise OSError(errno.EPIPE, 'Empyt message size', str(len(recv)))
        size = struct.unpack("i", recv)[0]
        data = ""
        while len(data) < size:
            msg = channel.recv(size - len(data))
            if not msg:
                return None
            data += msg.decode("utf8")
        logging.info(f"receiving data at {self._host}:\t{str(data)}")
        return json.loads( data.strip() )

    def callApi(self):
        try:
            with self.__API_QUEUE_LOCK:
                data = list(self.__API_QUEUE)
                self.__API_QUEUE[:] = []
            if len(data) > 0:
                requests.post(f"{self.__API_URL}/api/log", json=data)
        except ValueError as ve:
            logging.getLogger(name='callApi: ').error(ve)
        except ConnectionError as ce:
            logging.getLogger(name='callApi: ').error(ce)
        except TimeoutError as te:
            logging.getLogger(name='callApi: ').error(te)
        except requests.exceptions.RequestException as re:
            logging.getLogger(name='callApi: ').error(re)

