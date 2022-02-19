from iminuit.util import describe
import numpy as np
import simfit.UI as fitUI

# Advanced use of the simfit package.
# NOTE: Not quite finished yet

# A list of spectrum files. See documentation for format details. 
path = './example_spectra/Set1/'
files = [f'{path}spec{d}.asc' for d in range(1,6)]

# Run UI functions manually to have full control over the fit
UI = fitUI(files)
UI.get_input()
UI.scout_savepath()
UI.make_Gaussian()
print(UI.function_string)
exec(UI.function_string)
UI.make_chi2(fit_function2)
UI.set_initial_values()
UI.fit()
UI.save()

# The Minuit object can be accessed by UI.m to get final values, errors, etc. 
# For more information see the iminuit documentation
# Example: write peak areas to file
fmt = '\t'.join(['%8.3f '] + 2*UI.N_peaks*['%10.4f '])
header = '\t'.join( ["distance"] + [f"    A{i}\t    err{i}" for i in range(1,UI.N_peaks+1)] )
Adata = np.zeros([UI.N_spec,2*UI.N_peaks+1])
Adata[:,0] = np.linspace(1, 5, 5)
for i in range(UI.N_spec):
    for j in range(UI.N_peaks):
        Adata[i,2*j+1] = UI.m.values[f'A{j+1}_{i}']
        Adata[i,2*j+2] = UI.m.errors[f'A{j+1}_{i}']
np.savetxt(f'{UI.savename}.tsv',Adata,fmt=fmt,header=header)

""" Example run:

>>> python example.py "[350,390]" "[363,368]" example_fits/Set1/custom
"""
