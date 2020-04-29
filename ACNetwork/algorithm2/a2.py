import numpy as np
import time

def calculate_iteration(x, q):
    d_u = u - u_last
    d_q = - np.dot(l_i, x)
    q += d_q
    # print(f"d_q:\t\t\t\t{d_q}")
    # print(f"q: \t\t\t\t{q}")
    # print(f"np.dot(alpha, x - u): \t\t{-np.dot(alpha, x - u)}")
    # print(f"np.dot(l_p, x): \t\t{-np.dot(l_p, x)}")
    # print(f"np.dot(np.transpose(l_i), q):\t{np.dot(np.transpose(l_i), q)}")
    # print(f"d_u:\t\t\t\t{d_u}")
    
    d_x = - np.dot(alpha, x - u) - np.dot(l_p, x) + np.dot(np.transpose(l_i), q) + d_u
    # print(f"d_x:\t\t\t\t{d_x}")
    x += d_x
    return x


def calculate_laplacian(adjacency: np.array) -> np.array:
    out_degree = np.diag(np.sum(adjacency, axis=1))
    laplacian = np.subtract(out_degree, adjacency)
    return laplacian

if __name__ == "__main__":
    """ Simplified version of the algorithm to check the mathematical correctness"""

    NODES = 5
    signals = np.loadtxt('../data/run-1-1-n5.csv', delimiter=',')

    # adjacency = np.ones((NODES,NODES))
    # adjacency[:,0] = np.zeros(NODES)
    # adjacency[0,:] = np.zeros(NODES)
    # np.fill_diagonal(adjacency, 0)
    # adjacency[0,1] = 1
    # adjacency[1,0] = 1
    adjacency = [[0.0, 1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 1.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0, 1.0], [0.0, 1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0, 0.0]]

    print(adjacency)

    laplacian = calculate_laplacian(adjacency)

    print(laplacian)

    alpha = 1/np.max(np.real(np.linalg.eigvals(laplacian)))
    beta = 1.1

    l_p = np.dot(alpha, laplacian)
    l_i = np.dot(beta, l_p)

    print(l_i)
    print(l_p)

    # u = np.dot(np.random.randint(-10, 10, NODES), 1.0)
    u = signals[0]
    u_last = np.copy(u)
    d_u = np.zeros(np.shape(u))

    q = np.zeros(NODES)
    x = np.copy(u)

    print(u)
    print()
    print(alpha)
    print(beta)
    print()
    print(np.mean(u))
    time.sleep(4)
    for i in range(1200):
        u_last = np.copy(u)
        if i%5 == 0 and i/5 < 200 and i>0:
            u = signals[int(i/5)]
            if i/5+1 == 200:
                print(str(u) + ' <---')
                print(signals[-1])
        # print()
        # print(f"######################   {i}  ######################")
        x = calculate_iteration(x, q)
        print(f"{i}\t:{x}\t{u-u_last}")
        # time.sleep(1)
    print(np.mean(signals[-1]))
    print(signals[-1])
