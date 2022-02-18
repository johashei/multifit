import simfit.UI as fitUI

"""
How I want the package to be used at the simplest level
"""

files = ['example_spectrum0.asc']

UI = fitUI(files)
UI.set_fitfunction('linear_Gaussian')

# some way to set common and independent parameters

UI.run() # What peakfit does now


