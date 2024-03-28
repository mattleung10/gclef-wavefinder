"""Image Math"""

import numpy as np


def image_math(
    image_array: np.ndarray, bits: int, threshold: float, fwhm_method: str
) -> tuple[tuple[float, float], float, int, int]:
    """Calculate all image statistics

    Args:
        img_array: numpy array of image pixels
        bits: bits per pixel
        threshold: drop pixels with values below [threshold]% of max pixel value
        fwhm_method: full-width half-maximum calculation method, defaults to "variance"
                        other choices are: "encircled_pixels", "encircled_energy",
                        "weighted_encircled_energy"

    Returns:
        centroid, fwhm, max_value, n_saturated
    """
    image_copy = threshold_copy(image_array, bits, threshold)
    centroid = find_centroid(image_copy)
    fwhm = find_full_width_half_max(image_copy, centroid, fwhm_method)
    max_value = int(np.max(image_array))
    n_saturated = np.count_nonzero(image_array == (1 << bits) - 1)
    return centroid, fwhm, max_value, n_saturated


def roi_copy(image_array: np.ndarray, roi_size: tuple[int, int]) -> np.ndarray:
    """Return a copy of the array cropped to the region of interest

    Args:
        img_array: numpy array of image pixels
        roi_size: (x_size, y_size) of region of interest
    """
    copied = np.copy(image_array)
    # remember numpy arrays are flipped x & y
    box = get_roi_box((copied.shape[1], copied.shape[0]), roi_size)
    return copied[box[1] : box[3], box[0] : box[2]]


def get_roi_box(
    image_size: tuple[int, int], roi_size: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Return the (left, lower, right, upper) box representing the region of interest

    Args:
        image_size: (x_size, y_size) full image size
        roi_size: (x_size, y_size) region of interest size
    """
    size_x = roi_size[0]
    size_y = roi_size[1]
    f_size_x = image_size[0]
    f_size_y = image_size[1]
    left = f_size_x // 2 - size_x // 2
    lower = f_size_y // 2 - size_y // 2
    box = (left, lower, left + size_x, lower + size_y)
    return box


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
        (u_x, u_y) in pixels or (NaN, NaN) if does not exist
    """

    # if image is all dark, fwhm does not exist
    if np.sum(img_array) == 0:
        return (np.nan, np.nan)

    # make a grid of pixel coordinates in the x and y dimensions, e.g.:
    #   xx, yy = np.meshgrid(np.arange(2), np.arange(3))
    #   xx = array([[0, 1],     yy = array([[0, 0],
    #               [0, 1],                 [1, 1],
    #               [0, 1]])                [2, 2]])
    xx, yy = np.meshgrid(np.arange(img_array.shape[1]), np.arange(img_array.shape[0]))
    try:
        # take the weighted average of the pixel coordinates, using the pixel values as weights
        u_x = float(np.average(xx, weights=img_array))
        u_y = float(np.average(yy, weights=img_array))
        return (u_x, u_y)
    except ZeroDivisionError:
        return (np.nan, np.nan)


def find_full_width_half_max(
    img_array: np.ndarray,
    centroid: tuple[float, float] | None = None,
    method: str = "variance",
) -> float:
    """Find full-width half-maximum.

    Multiple methods are implemented, and one can be selected here.

    Args:
        img_array: numpy array of image pixels
        centroid: tuple of (u_x, u_y) giving the centroid of the img_array
        method: fwhm calculation method, defaults to "variance"
                other choices are: "encircled_pixels", "encircled_energy",
                "weighted_encircled_energy"

    Returns:
        diameter of full-width half-max in pixels
    """

    # if image is all dark, fwhm does not exist
    if np.sum(img_array) == 0:
        return np.nan

    # get centroid if not provided; return NaN if centroid is NaN
    if centroid is None:
        centroid = find_centroid(img_array)
    if np.isnan(centroid[0]) or np.isnan(centroid[1]):
        return np.nan

    # select fwhm method
    match method:
        case "variance":
            fwhm = fwhm_by_variance(img_array, centroid)
        case "encircled_pixels":
            fwhm = fwhm_by_encircled_pixels(img_array, centroid)
        case "encircled_energy":
            fwhm = fwhm_by_encircled_energy(img_array, centroid)
        case "weighted_encircled_energy":
            fwhm = fwhm_by_weighted_encircled_energy(img_array, centroid)
        case _:
            fwhm = fwhm_by_variance(img_array, centroid)
    return fwhm


def fwhm_by_variance(img_array: np.ndarray, centroid: tuple[float, float]) -> float:
    """Calculate the variance and then use that to get full-width half-max."""
    # make a grid of pixel coordinates in the x and y dimensions, e.g.:
    #   xx, yy = np.meshgrid(np.arange(2), np.arange(3))
    #   xx = array([[0, 1],     yy = array([[0, 0],
    #               [0, 1],                 [1, 1],
    #               [0, 1]])                [2, 2]])
    # NOTE: numpy array x and y are flipped from how they are displayed
    xx, yy = np.meshgrid(np.arange(img_array.shape[1]), np.arange(img_array.shape[0]))
    x_var, y_var = 0, 0
    try:
        # calculate the weighted variance and covariance
        x_var = float(np.average(np.power(xx - centroid[0], 2), weights=img_array))
        y_var = float(np.average(np.power(yy - centroid[1], 2), weights=img_array))
    except ZeroDivisionError:
        pass
    # return the maximum fwhm (either in x or y direction)
    # fwhm for a gaussian is 2 * sqrt(2 * ln(2)) * [std. dev.]
    # 2 * sqrt(2 * ln(2)) ~= 2.3548200450309493
    # add one for center pixel
    return 1 + np.sqrt(max(x_var, y_var)) * 2.3548200450309493


def fwhm_by_encircled_pixels(
    img_array: np.ndarray, centroid: tuple[float, float]
) -> float:
    """Find the diameter of the circle centered at the centroid which encloses
    all pixels with values greater than half of the maximum value of all pixels
    in the image.
    """
    half_max = np.max(img_array) / 2

    # find number of pixels greater than half max
    v_t = np.count_nonzero(img_array >= half_max)

    # find center of pixel which contains centroid and save the remainder
    # NOTE: numpy array x and y are flipped from how they are displayed
    center_pixel = (int(centroid[1] // 1), int(centroid[0] // 1))
    remainder = (centroid[1] % 1, centroid[0] % 1)

    # starting from center pixel, grow a circle one pixel at a time until
    # it contains all fwhm pixels or we hit the edge of the array
    radius = 0
    while (
        center_pixel[0] - radius >= 0
        and center_pixel[1] - radius >= 0
        and center_pixel[0] + radius + 1 < img_array.shape[0]
        and center_pixel[1] + radius + 1 < img_array.shape[1]
    ):
        # get sub-array and check how many fwhm pixels are in it
        subarray = img_array[
            center_pixel[0] - radius : center_pixel[0] + radius + 1,
            center_pixel[1] - radius : center_pixel[1] + radius + 1,
        ]
        if np.count_nonzero(subarray >= half_max) >= v_t:
            break
        radius += 1

    # [center pixel]
    # + 2 * ([additional pixels to capture all half-max pixels]
    #        + [maximum distance in x or y from the centroid to the position of the center pixel])
    fwhm = 1 + 2 * (radius + max(remainder))
    return fwhm


def fwhm_by_encircled_energy(
    img_array: np.ndarray, centroid: tuple[float, float]
) -> float:
    """Find the diameter of the circle centered at the centroid which encloses
    pixels with a summed value greater than half of the total value of all pixels
    in the image.
    """

    # total energy in image
    total_e = np.sum(img_array)

    # find center of pixel which contains centroid and save the remainder
    # NOTE: numpy array x and y are flipped from how they are displayed
    center_pixel = (int(centroid[1] // 1), int(centroid[0] // 1))
    remainder = (centroid[1] % 1, centroid[0] % 1)

    # starting from center pixel, grow a circle one pixel at a time until
    # it contains all fwhm pixels or we hit the edge of the array
    radius = 0
    while (
        center_pixel[0] - radius >= 0
        and center_pixel[1] - radius >= 0
        and center_pixel[0] + radius + 1 < img_array.shape[0]
        and center_pixel[1] + radius + 1 < img_array.shape[1]
    ):
        # get sub-array and check how much energy it contains
        subarray = img_array[
            center_pixel[0] - radius : center_pixel[0] + radius + 1,
            center_pixel[1] - radius : center_pixel[1] + radius + 1,
        ]
        if np.sum(subarray) >= total_e / 2:
            break
        radius += 1

    # [center pixel]
    # + 2 * ([additional pixels to capture enough energy]
    #        + [maximum distance in x or y from the centroid to the position of the center pixel])
    fwhm = 1 + 2 * (radius + max(remainder))
    return fwhm


def fwhm_by_weighted_encircled_energy(
    img_array: np.ndarray, centroid: tuple[float, float]
) -> float:
    """Find the diameter of the circle centered at the centroid which encloses
    pixels with a weighted summed value greater than half of the total value of
    all pixels in the image.
    """

    # total energy in image, can't be zero
    total_e = np.sum(img_array)
    if total_e == 0:
        return np.nan

    # find center of pixel which contains centroid and save the remainder
    # NOTE: numpy array x and y are flipped from how they are displayed
    center_pixel = (int(centroid[1] // 1), int(centroid[0] // 1))
    remainder = (centroid[1] % 1, centroid[0] % 1)

    # starting from center pixel, grow a circle one pixel at a time until
    # it contains all fwhm pixels or we hit the edge of the array
    radius = 0
    subarray_e = 0
    while (
        center_pixel[0] - radius >= 0
        and center_pixel[1] - radius >= 0
        and center_pixel[0] + radius + 1 < img_array.shape[0]
        and center_pixel[1] + radius + 1 < img_array.shape[1]
    ):
        # get sub-array and check how much energy it contains
        subarray = img_array[
            center_pixel[0] - radius : center_pixel[0] + radius + 1,
            center_pixel[1] - radius : center_pixel[1] + radius + 1,
        ]
        subarray_e = np.sum(subarray)
        if subarray_e >= total_e / 2:
            break
        radius += 1

    # [center pixel]
    # + 2 * ([additional pixels to capture enough energy]
    #        + [maximum distance in x or y from the centroid to the position of the center pixel])
    fwhm = 1 + 2 * (radius + max(remainder))

    # weight by the proportion of energy enclosed
    # if all energy is enclosed, then we divide by 1; if half, divide by 0.5, etc.
    return fwhm / (subarray_e / total_e)
