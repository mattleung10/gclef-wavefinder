"""Image Math"""

import numpy as np


def get_centroid_and_variance(
    img_array: np.ndarray, bits: int, threshold: float
) -> tuple[float, float, float, float, float]:
    """Get image centroid and variance/covariance.

    Args:
        img_array: numpy array of image pixels
        bits: bits per pixel
        threshold: drop pixels with values below [threshold]% of max pixel value

    Returns:
        (u_x, u_y, var_x, var_y, covar)
    """
    x_avg, y_avg, x_var, y_var, covar = 0.0, 0.0, 0.0, 0.0, 0.0
    t_val = ((1 << bits) - 1) * threshold / 100

    # NOTE: thresholding affects original array, so make a copy
    copied = np.copy(img_array)
    copied[img_array < t_val] = 0

    # make a grid of pixel coordinates in the x and y dimensions, e.g.:
    #   xx, yy = np.meshgrid(np.arange(2), np.arange(3))
    #   xx = array([[0, 1],     yy = array([[0, 0],
    #               [0, 1],                 [1, 1],
    #               [0, 1]])                [2, 2]])
    xx, yy = np.meshgrid(np.arange(copied.shape[1]), np.arange(copied.shape[0]))

    try:
        # take the weighted average of the pixel coordinates, using the pixel values as weights
        x_avg = float(np.average(xx, weights=copied))
        y_avg = float(np.average(yy, weights=copied))
        # calculate the weighted variance and covariance
        x_var = float(np.average(np.power(xx - x_avg, 2), weights=copied))
        y_var = float(np.average(np.power(yy - y_avg, 2), weights=copied))
        covar = float(
            np.average(np.multiply((xx - x_avg), (yy - y_avg)), weights=copied)
        )
    except ZeroDivisionError:
        pass

    return (x_avg, y_avg, x_var, y_var, covar)


def variance_to_fwhm(var: float) -> float:
    """Get full width half maximum from variance"""
    const = 2.3548200450309493
    return np.sqrt(var) * const


def threshold_copy(img_array: np.ndarray, bits: int, threshold: float) -> np.ndarray:
    """Return a copy of the array with pixels below the threshold set to zero.

    Args:
        img_array: numpy array of image pixels
        bits: bits per pixel
        threshold: drop pixels with values below [threshold]% of max pixel value

    Returns:
        numpy array with pixels below the threshold set to zero
    """
    # NOTE: thresholding affects original array, so make a copy
    copied = np.copy(img_array)
    t_val = ((1 << bits) - 1) * threshold / 100
    copied[img_array < t_val] = 0
    return copied


def find_centroid(img_array: np.ndarray) -> tuple[float, float]:
    """Find image centroid.

    Args:
        img_array: numpy array of image pixels

    Returns:
        (u_x, u_y) in pixels
    """
    # make a grid of pixel coordinates in the x and y dimensions, e.g.:
    #   xx, yy = np.meshgrid(np.arange(2), np.arange(3))
    #   xx = array([[0, 1],     yy = array([[0, 0],
    #               [0, 1],                 [1, 1],
    #               [0, 1]])                [2, 2]])
    xx, yy = np.meshgrid(np.arange(img_array.shape[1]), np.arange(img_array.shape[0]))
    u_x, u_y = 0.0, 0.0

    try:
        # take the weighted average of the pixel coordinates, using the pixel values as weights
        u_x = float(np.average(xx, weights=img_array))
        u_y = float(np.average(yy, weights=img_array))
    except ZeroDivisionError:
        pass
    return (u_x, u_y)


def find_full_width_half_max(
    img_array: np.ndarray, centroid: tuple[float, float] | None = None
) -> float:
    """Find full-width half-maximum.

    Find the diameter of the circle centered at the centroid which
    encloses all pixels with values greater than
    half of the maximum value of all pixels in the image.

    Args:
        img_array: numpy array of image pixels
        centroid: tuple of (u_x, u_y) giving the centroid of the img_array

    Returns:
        diameter of full-width half-max in pixels
    """
    if centroid is None:
        centroid = find_centroid(img_array)

    half_max = np.max(img_array) / 2

    # find number of pixels greater than half max
    v_t = np.count_nonzero(img_array >= half_max)

    # find center of pixel which contains centroid and save the remainder
    # NOTE: numpy array x and y are flipped from how they are displayed
    center_pixel = (int(centroid[1] // 1), int(centroid[0] // 1))
    remainder = (centroid[1] % 1, centroid[0] % 1)

    # starting from center pixel, grow a circle one pixel at a time until
    # it contains all fwhm pixels
    d = 0
    v = 0
    while v < v_t:
        # bound circle to array
        if (
            center_pixel[0] - d < 0
            or center_pixel[1] - d < 0
            or center_pixel[0] + d >= img_array.shape[0]
            or center_pixel[1] + d >= img_array.shape[1]
        ):
            break
        # get sub-array and check how many fwhm pixels are in it
        subarray = img_array[
            center_pixel[0] - d : center_pixel[0] + d,
            center_pixel[1] - d : center_pixel[1] + d,
        ]
        v = np.count_nonzero(subarray >= half_max)
        d += 1

    fwhm = d + max(remainder) + 1
    return fwhm
