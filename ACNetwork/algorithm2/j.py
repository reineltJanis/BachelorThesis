import sys, utility, logging
from multiprocessing import Process, Manager, Lock, Value
import numpy as np

def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )
    cls.__str__ = __str__
    return cls

@auto_str
class J(object):
    def __init__(self, k: int, reference_signal: float, neighbors = {}, manager = Manager(), q = 0.0,):
        #iteration k
        self._k = manager.Value('i', k)
        self._state = manager.Value('f', reference_signal)
        self._reference_signal = manager.Value('f', reference_signal)
        self._last_reference_signal = manager.Value('f', reference_signal)
        self._q = manager.Value('f', q)
        self.lock = Lock()
        self.neighbors = manager.dict()
        self.neighbors.update(neighbors)
        self.__logger = logging.getLogger(name='J:')
    
    def set_state(self, state: float):
        # self._last_reference_signal.value = self._reference_signal.value
        self._state.value = state

    def state(self) -> float:
        return self._state.value
    
    def diff(self) -> float:
        with self.lock:
            return self._reference_signal.value - self._last_reference_signal.value
    
    def k(self) -> int:
        return self._k.value

    def set_k(self, val: int):
        self._k.value = int(val)

    def increment_k(self):
        with self.lock:
            self._k.value += 1

    def q(self) -> float:
        return float(self._q.value)
    
    def set_q(self, val: float):
        self._q.value = float(val)

    def reference_signal(self) -> float:
        return float(self._reference_signal.value)
    
    def set_reference_signal(self, val: float):
        logger = self.__logger.getChild('set_reference_signal: ')
        with self.lock:
            self._last_reference_signal.value = self._reference_signal.value
            self._reference_signal.value = val
        logger.debug(f"last: {self._last_reference_signal.value} \t current: {self._reference_signal.value}")
