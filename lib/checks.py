import numpy as np

from exceptions import *

def same_length(array1, array2):
    if len(array1) == len(array2):
        return True
    else:
        raise ValueError("Arrays do not have the same length")

