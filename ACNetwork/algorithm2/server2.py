import random, logging, sys, struct, json, errno, time, decimal, utility, csv, requests
import numpy as np
from j import J
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from multiprocessing import Process, Manager, Lock, Value
from threading import Thread, Event
from job import Job
from datetime import timedelta
from config import Config
from datetime import datetime

@utility.auto_str
class Server(Process):
    def __init__(self, config: Config, signals: np.ndarray, output = None, interval = 1000, new_reference_signal_each_k = 5, max_iterations = 1200, max_retries = 10, beta = 1.0, error_on = False, error_start = 0, error_duration = 10, manager = None, network_id = '1'):
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

        super(Server, self).__init__()

        logger = logging.getLogger(name='Server.__init__')

        self._manager = manager if manager!= None else Manager() # used to synchronize data between processes and threads
        self._host = config.host
        self._port = config.port
        self.__address = (config.host, config.port)
        self._adjacency = config.adjacency
        self._id = config.id
        self._laplacian = utility.calculate_laplacian(self._adjacency)
        if not utility.check_laplacian(self._laplacian):
            raise BaseException("No valid laplacian")
        # self._beta = 1/np.max(np.linalg.eigvals(self._laplacian)) # calculates beta
        self._alpha = utility.calculate_beta(self._laplacian)
        self._beta = beta
        self._laplacian_proportional = np.dot(self._alpha, self._laplacian)
        self._laplacian_integral = np.dot(self._beta, self._laplacian_proportional)
        self._server_socket = socket(AF_INET, SOCK_STREAM)
        self._server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._server_socket.bind(self.__address)
        self._j = J(0, signals[0], config.out_neighbors)
        self._neighbor_states = self._manager.dict()
        self._neighbor_states_lock = Lock()
        self._interval = interval
        self._interval_sec = float(interval / 1000.0)
        self.__signals = signals
        self._new_reference_signal_each_k = new_reference_signal_each_k
        self.__output = output
        self.__max_iterations = max_iterations
        self.__running = False
        self.__neighbor_out_connections = self._manager.dict()
        self._max_retries = max_retries
        self.__error_on = error_on
        self.__error_start = error_start
        self.__error_duration = error_duration
        self.__stopped = Event()
        
        self.__API_URL = 'http://10.0.2.2:7071'
        # self.__API_URL = 'https://acmonitor.azurewebsites.net'
        self.__NETWORK_ID = network_id
        self.__API_QUEUE = manager.list()
        self.__API_QUEUE_LOCK = Lock()
        
        self.__tl = None 
        if config.instant_start:
            self.start()
        # logger.debug(self)
        logger.warn(f"Using beta {self._beta:24.20f}")

    def run(self):
        ''' Starting server, acccept process and broadcast Threads. '''
        try:
            self._server_socket.listen(500)
            self.__stopped.clear()

            self.accept_thread = Thread(target=self.accept_connections)
            self.accept_thread.daemon = True
            self.api_thread = Thread(target=self.call_api_job, args=(timedelta(milliseconds=2000),))
            self.api_thread.daemon = True

            # add initial to api queue
            with self.__API_QUEUE_LOCK:
                self.__API_QUEUE.append(
                    {
                        'nodeId': self._host,
                        'port': self._port,
                        'state': self._j.reference_signal(),
                        'neighborStates': {},
                        'iteration': '0',
                        'timestamp': datetime.utcnow().__str__(),
                        'networkId': self.__NETWORK_ID,
                        'referenceSignal': self._j.reference_signal()
                    }
                )

            self.accept_thread.start()
            self.api_thread.start()

            while not self.__stopped.wait(self._interval_sec):
                self.broadcast()
            
            if self.__output != None:
                self.__output.close()

            self.api_thread.join()

            # To empyt the queue and send all data to the api
            self.call_api()
            
            self.accept_thread.join(5)
            
        except BaseException as e:
            logging.getLogger(name='start').error(str(e))
            self.stop()

    def stop(self):
        ''' Stopping all processes and threads. '''
        self.__stopped.set()
        self._server_socket.close()

    def accept_connections(self):
        ''' Waits for new connections. Creates a handling Thread for all new connections. '''
        logger = logging.getLogger(name='Server:accept_connections')
        while not self.__stopped.is_set():
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
        while self._j.k() < self.__max_iterations and not self.__stopped.is_set():
            try:
                msg = self.receive(client)
                sender = msg[0]
                key = int(msg[2])
                state_x = msg[1]
                state_q = msg[3]

                logger.debug(f"{self._id} received:\t{msg}")

                # Only update the tuple if state is defined in message
                with self._neighbor_states_lock:
                    if (sender, key) in self._neighbor_states:
                        states_tuple = self._neighbor_states[(sender, key)]
                        if states_tuple[0] != None:
                            state_x = states_tuple[0]
                        if states_tuple[1] != None:
                            state_q = states_tuple[1]
                    self._neighbor_states[(sender, key)] = (state_x, state_q) # sample item created: ((host='127.0.0.1', k=4), (state_x=451.75, state_q=-67.6))
                
                logger.info(f"[{self._host}]: Stored [{(sender, key)}]: {str((state_x,state_q))}")
                logger.debug(f"Node {self._id} has states {self._neighbor_states}")
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
                # logging.getLogger(name='Server:broadcast').info("broadcast job current time: %s with data: %s" % (time.ctime(), str(self._neighbor_states)))
                # thread = Thread(target=self.broadcast_thread) #, args=(self._j, self._neighbor_states, self._adjacency)
                # thread.daemon = True
                # thread.start()
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
        k = self._j.k()

        logger = logging.getLogger(name='Server:broadcast_thread')

        if k == 0:
            logger.info(f"Node {self._id} initially broadcasts its value.")
            self.distribute_states(state_x = self._j.state())

        logger.debug(f"{self._id}: states: after init\t{self._neighbor_states}")

        # Check if all neighbor states of current k are known, waits otherwise for interval max. 5 tries
        for i in range(self._max_retries):
            with self._neighbor_states_lock:
                if len(dict(filter(lambda o: o[0][1] == k and o[1][0] != None, self._neighbor_states.items()))) == len(self._j.neighbors):
                    break
            if i==self._max_retries-1:
                logger.warn(f"Node {self._id}: RESETTING at position 1")
                return
            time.sleep(self._interval_sec)
        logger.debug(f"{self._id}: states: after state_x\t{self._neighbor_states}")
        
        x = np.zeros(np.shape(self._adjacency)[0])
        current_neighbor_states = {}
        with self._neighbor_states_lock:
            for neighbor_at_k_tuple, value_tuple in self._neighbor_states.items():
                id = self._j.neighbors[neighbor_at_k_tuple[0]]
                if neighbor_at_k_tuple[1] == k:
                    np.put(x, int(id), value_tuple[0])
                    current_neighbor_states[neighbor_at_k_tuple[0]] = value_tuple[0]
        
        np.put(x, self._id, self._j.state())

        # calculate state_q
        with self._j.lock:
            my_q = utility.calculate_qi(self._id, self._laplacian_integral, x, self._j.q())
            self._j.set_q(my_q)
        self.distribute_states(state_q=my_q)


        # getting qs from other states
        q = np.zeros(np.shape(x))
        np.put(q, self._id, my_q)
        # Check if values -> state_q is present at key -> k of current iteration
        for i in range(self._max_retries):
            with self._neighbor_states_lock:
                if len(dict(filter(lambda o: o[0][1] == k and o[1][1] != None, self._neighbor_states.items()))) == len(self._j.neighbors):
                    break
            if i==self._max_retries-1:
                # reset q if aborted
                with self._j.lock:
                    self._j.set_q(self._j.q() - my_q)
                logger.warn(f"Node {self._id}: RESETTING at position 2")
                return
            time.sleep(self._interval_sec)

        logger.debug(f"{self._id}: states: after state_q\t{self._neighbor_states}")
        with self._neighbor_states_lock:
            for neighbor_at_k_tuple, value_tuple in self._neighbor_states.items():
                id = self._j.neighbors[neighbor_at_k_tuple[0]]
                logger.info(f"{neighbor_at_k_tuple[0]} > {id}")
                if neighbor_at_k_tuple[1] == k:
                    np.put(q, int(id), value_tuple[1])
        # logger.info(f"{self._id}: xm: {str(x)}")
        # logger.info(f"{self._id}: qm: {str(q)}")
        # Generating q and broadcasting it
        sig_nr = int(self._j.k()/self._new_reference_signal_each_k)
        self._j.set_reference_signal(self._j.reference_signal())
        if k > 0 and sig_nr < 200:
            if k % self._new_reference_signal_each_k == 0:
                self._j.set_reference_signal(self.__signals[sig_nr])


        x_new = utility.calculate_iteration(
            self._id, 
            self._laplacian_integral, 
            self._laplacian_proportional, 
            x, 
            q, 
            self._j.reference_signal(), 
            self._j.diff(),
            self._alpha, 
            self._beta
            )
        self._j.increment_k()
        self._j.set_state(x_new)
        self.distribute_states(state_x=x_new)
        logger.debug(f" UPDATED: Node {self._id}: {self._j.state()} | Others: {self._neighbor_states}")

        # add log to api queue
        with self.__API_QUEUE_LOCK:
            self.__API_QUEUE.append(
                {
                    'nodeId': self._host,
                    'port': self._port,
                    'state': float(np.real(x_new)),
                    'neighborStates': current_neighbor_states,
                    'iteration': self._j.k(),
                    'timestamp': datetime.utcnow().__str__(),
                    'networkId': self.__NETWORK_ID,
                    'referenceSignal': self._j.reference_signal()
                }
            )

        # log to output if specified
        if self.__output != None:
            try:
                self.__output.write(str(float(self._j.state())) + '\n')
            except BaseException as e:
                logger.error("Unable to wirte to output.\n" +  str(e))
        

        ''' Removes all data from previous calculations (session_key < k). '''
        with self._neighbor_states_lock:
            states_to_remove = dict(filter(
                lambda elem: elem[0][1] < self._j.k(), # elem[0] is key of dict and consists of node name and session key k
                self._neighbor_states.items()
            ))
            
            for state in states_to_remove.items():
                try:
                    del self._neighbor_states[state[0]]
                except KeyError:
                    logger.warn(f"Key '{state[0]}' not found.")

    def distribute_states(self, state_x: float = None, state_q: float = None):
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
                if state_x != None:
                    error = 0.0
                    if self.__error_on:
                        if self._j.k() >= self.__error_start and self._j.k() < self.__error_start + self.__error_duration:
                            error = utility.calculate_error(self._j.k())
                            logging.debug(f"Adding error on node {self._id}: {error}")
                    state_x += error

                if state_x != None:
                    state_x = float(np.real(state_x))
                if state_q != None:
                    state_q = float(np.real(state_q))

                self.send(self.__neighbor_out_connections[neighbor], message=(self._host, state_x, self._j.k(), state_q))
            except OSError as e:
                logging.getLogger(name='Server:distribute_state').debug(str(e))
                try:
                    self.__neighbor_out_connections[neighbor].close()
                except Exception as e:
                    logging.getLogger(name='Server:distribute_state').error(e)
                    pass
                finally:
                    if neighbor in self.__neighbor_out_connections:
                        del self.__neighbor_out_connections[neighbor]
                        logging.getLogger(name='Server:distribute_state').warn('Deleting socket connection for ' + neighbor)
            # finally:
            #     client_socket.close()

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


    def call_api_job(self, interval: timedelta):
        while not self.__stopped.wait(interval.total_seconds()):
            try:
                self.call_api()
            except Exception as e:
                logging.getLogger(name="call_api_job").error(e)

    def call_api(self):
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

