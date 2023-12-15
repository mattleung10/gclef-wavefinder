"""Image Math"""

import numpy as np


def get_centroid_and_variance(img_array: np.ndarray, threshold: float)-> tuple[float, float, float, float, float]:
    """Get image centroid and variance/covariance as (u_x, u_y, var_x, var_y, covar)"""
    x_avg, y_avg, x_var, y_var, covar = 0.0, 0.0, 0.0, 0.0, 0.0
    t_val = np.iinfo(img_array.dtype).max * threshold / 100
    img_array[img_array < t_val] = 0

    # make a grid of pixel coordinates in the x and y dimensions, e.g.:
    #   xx, yy = np.meshgrid(np.arange(2), np.arange(3))
    #   xx = array([[0, 1],     yy = array([[0, 0],
    #               [0, 1],                 [1, 1],
    #               [0, 1]])                [2, 2]])
    xx, yy = np.meshgrid(np.arange(img_array.shape[1]), np.arange(img_array.shape[0]))

    try:
        # take the weighted average of the pixel coordinates, using the pixel values as weights
        x_avg = float(np.average(xx, weights=img_array))
        y_avg = float(np.average(yy, weights=img_array))
        # calculate the weighted variance and covariance
        x_var = float(np.average(np.power(xx - x_avg, 2), weights=img_array))
        y_var = float(np.average(np.power(yy - y_avg, 2), weights=img_array))
        covar = float(np.average(np.multiply((xx - x_avg),(yy - y_avg)), weights=img_array))
    except ZeroDivisionError:
        pass

    return (x_avg, y_avg, x_var, y_var, covar)

def variance_to_fwhm(var: float) -> float:
    """Get full width half maximum from variance"""
    const = 2.3548200450309493
    return np.sqrt(var) * const