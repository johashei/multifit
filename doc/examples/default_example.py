import simfit.UI as fitUI

# The simplest use of the simfit package.

# A list of spectrum files. See documentation for format details. 
path = './example_spectra/Mo104/'
spec_names = [30,52,89,155,264,450,780,1170,1776,2650]
files = [f'{path}{d}um.asc' for d in spec_names]

UI = fitUI(files)
UI() # run the fitting program with default configuration 

# The Minuit object can be accessed by UI.m to get final values, errors, etc. 
# For more information see the iminuit documentation
# Example: iterate over values and errors:
for key, value, error in zip(UI.m.parameters, UI.m.values, UI.m.errors):
    print(f"{key} = {value} ± {error}")

