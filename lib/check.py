import numpy as np
from exceptions import UnequalLengthError

def same_length(array1, array2):
    if len(array1) == len(array2):
        return 
    else:

        raise UnequalLengthError()

