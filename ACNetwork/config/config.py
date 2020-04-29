import json, os, sys
import numpy as np

class Config(object):
    def __init__(self, host: str, port: int, id: int, adjacency: np.ndarray, out_neighbors = {}, instant_start = False):
        self.host = host
        self.port = port
        self.id = id
        self.out_neighbors = out_neighbors
        self.instant_start = instant_start
        self.adjacency = np.array(adjacency, dtype=float)

    @classmethod
    def from_json(cls, string: str):
        data = json.loads(string)
        config = Config(**data)
        return config
    
    @classmethod
    def serialize_array(cls, arr: []) -> str:
        print(arr)
        return json.dumps(arr, default=lambda elem: elem if type(elem) != Config else json.loads(elem.to_json()))

    @classmethod
    def deserialize_array(cls, string):
        arr = json.loads(string)
        arr = list(map(lambda elem: Config(**elem), arr))
        return arr

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=lambda o: o if type(o) is not np.ndarray else o.tolist())

    @classmethod
    def store(cls, arr: list, path: str):
        path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f = open(path, "w")
        try:
            data = Config.serialize_array(arr)
            f.write(data)
        finally:
            f.close()
    
    @classmethod
    def load(cls, path):
        path = os.path.abspath(path)
        if os.path.exists(path):
            f = open(path, "r")
            data = f.readline()
            arr = Config.deserialize_array(data)
            return arr
        else:
            raise BaseException(f"File not found. {path}")

def create_adjacency_default(nodes: int):
    # adjacency = np.array([[0,1,0,0,0],[1,0,1,1,0],[0,1,0,1,1],[0,1,1,0,0],[0,0,1,0,0]], 'float')
    adjacency = np.ones((nodes,nodes))
    np.fill_diagonal(adjacency, 0)
    # generating solo connection on one side
    adjacency[:,0] = 0
    adjacency[0,:] = 0
    adjacency[1,0] = 1
    adjacency[0,1] = 1
    # generating it on the other side
    adjacency[:,-1] = 0
    adjacency[-1,:] = 0
    adjacency[-1,-2] = 1
    adjacency[-2,-1] = 1

    return adjacency

def create_adjacency_ring(nodes: int):
    adjacency = np.zeros((nodes, nodes))
    for i in range(nodes):
        adjacency[i, (i-1)%nodes] = 1
        adjacency[i, (i+1)%nodes] = 1

    return adjacency

def create_adjacency_star(nodes: int):
    adjacency = np.zeros((nodes,nodes))
    # node 0 is the center node -> connected to all others
    adjacency[0] = np.ones(nodes)
    adjacency[:,0] = np.ones(nodes)
    adjacency[0,0] = 0
    return adjacency


if __name__ == "__main__":
    
    NODES = 30
    adjacency = create_adjacency_default(NODES)
    arr = []
    for r in range(np.shape(adjacency)[0]):
        out_neighbors = {}
        for c in range(np.shape(adjacency)[1]):
            if(adjacency[r,c]==1):
                out_neighbors[f"127.0.0.{c+1}"] = c
        arr.append(
            Config(f"127.0.0.{r+1}", 33100, r, adjacency, out_neighbors)
        )

    # arr = [
    #     Config('127.0.0.1', 33100, 0, adjacency, {'127.0.0.2': 1}),
    #     Config('127.0.0.2', 33100, 1, adjacency, {'127.0.0.1': 0, '127.0.0.3': 2, '127.0.0.4': 3}),
    #     Config('127.0.0.3', 33100, 2, adjacency, {'127.0.0.2': 1, '127.0.0.4': 3, '127.0.0.5': 4}),
    #     Config('127.0.0.4', 33100, 3, adjacency, {'127.0.0.2': 1, '127.0.0.3': 2}),
    #     Config('127.0.0.5', 33100, 4, adjacency, {'127.0.0.3': 2})
    #     ]

    arr_serialzed = Config.serialize_array(arr)
    print(arr_serialzed)
    arr_deserialized = Config.deserialize_array(arr_serialzed)
    print(arr_deserialized)
    Config.store(arr, f"../config/config1-n{NODES}.json")