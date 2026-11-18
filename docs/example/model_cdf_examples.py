from numba import njit
from numba_stats import truncnorm
import numpy as np

#@njit(parallel=True, fastmath=True)
def peaks(x, x0, separation, σ0, σ1, totalarea, ratio, slope, offset, xmin, xmax):
    """Two gaussian peaks on a linear background
    """
    peak0 = totalarea*ratio*truncnorm.cdf(x, xmin, xmax, x0, σ0)
    peak1 = totalarea*(1-ratio)*truncnorm.cdf(x, xmin, xmax, x0-separation, σ1)
    background = linear(x, slope, offset, xmin, xmax)
    return np.array([background, peak0, peak1])

def peaks_multiple(
        x, x0, separation, σ0, σ1, refarea, relarea, ratio, slope, offset, xmin, xmax):
    """Two gaussian peaks on a linear background, with relference area.

    Usefull for fitting multiple peaks, by making ref_area a spectrum
    parameter and rel_area a peak parameter.
    """
    peak0 = refarea*relarea*ratio*truncnorm.cdf(x, xmin, xmax, x0, σ0)
    peak1 = refarea*relarea*(1-ratio)*truncnorm.cdf(x, xmin, xmax, x0-separation, σ1)
    background = linear(x, slope, offset, xmin, xmax)
    return np.array([background, peak0, peak1])


@njit(parallel=True, fastmath=True)
def linear(x, slope, offset, xmin, xmax) -> np.ndarray:
    """cdf for a truncated linear distribution"""
    x_from_Emin = x - xmin
    belowrange = xmin > x
    aboverange = x > xmax
    integral = (
        (slope/2*x_from_Emin*x_from_Emin + offset*x_from_Emin)
        *(1 - belowrange)*(1 - aboverange) # only inside the range
        + (slope/2*(xmax - xmin)**2 + offset*(xmax - xmin))*aboverange
        )
    return  integral


