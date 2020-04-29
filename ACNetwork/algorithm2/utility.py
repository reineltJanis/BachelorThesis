import json, struct, logging, math
from j import J
import numpy as np

def calculate_iteration(i: int, laplacian_integral: np.ndarray, laplacian_proportional: np.ndarray,  x: np.ndarray, q: np.ndarray, u_i: float, du_i: float, alpha=0.2, beta = 1) -> float:
    # new_state = state - delta * (laplacian * states)_i + difference_of_ref_signal
    np.seterr(all='raise')
    try:
        d_x_i = - np.dot(alpha, x[i] - u_i) - np.dot(laplacian_proportional, x)[i] + np.dot(np.transpose(laplacian_integral), q)[i] + du_i
        # logging.warn(f"{i}:d_x_i\t{d_x_i}")
        x_i_new = x[i] + d_x_i
        # logging.warn(f"{i}:d_x_new\t{x_i_new}")
        return np.real(x_i_new)
        # x_i = x[i] - np.dot(beta, np.dot(laplacian, x))[i]
        # x_i = x_i + dx_i
        # logging.debug(f"{dx_i}-->{x_i}")
        # return float(x_i)
    except FloatingPointError as e:
        logger = logging.getLogger(name='utility:calculate_iteration: ')
        logger.error(e)

def calculate_qi(i: int, laplacian_integral: np.ndarray, x: np.ndarray, q_i: float) -> float:
    d_q = - np.dot(laplacian_integral, x)
    # logging.warn(f"{i}:d_q\t{d_q}")
    q_i += d_q[i]
    # logging.warn(f"{i}:q\t{q_i}")
    return np.real(q_i)

def check_laplacian(laplacian: np.array) -> bool:
        laplacian_dot_one = np.dot(laplacian, np.ones(np.shape(laplacian)))
        return np.count_nonzero(laplacian_dot_one) == 0

def check_balanced(matrix: np.array) -> bool:
    one_t_dot_laplacian = np.dot(np.transpose(np.ones(np.shape(matrix))), matrix)
    return np.count_nonzero(one_t_dot_laplacian) == 0

def calculate_laplacian(adjacency: np.array) -> np.array:
    out_degree = np.diag(np.sum(adjacency, axis=1))
    laplacian = np.subtract(out_degree, adjacency)
    return laplacian

def calculate_beta(laplacian: np.array) -> np.float64:
    # eigv = np.linalg.eigvals(laplacian)
    # logging.warn(eigv)
    # condition = np.where()
    # condition = np.where(np.asarray(eigv) > 0, True, True)
    # eigv_greater_zero = np.extract(condition, eigv)
    # logging.warn(eigv_greater_zero)
    # beta = 1/np.max(eigv)
    # beta = 0.39
    beta = 1/np.max(np.linalg.eigvals(laplacian))
    # logging.warn(beta)
    return beta

def calculate_error(k: int):
    err = k
    err = 2 * err
    err = math.cos(err)
    err = 10 * err
    err = err + 20
    return err

    

def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )
    cls.__str__ = __str__
    return cls