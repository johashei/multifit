import multifit.UI as fitUI

# The simplest use of the multifit package.

# A list of spectrum files. See documentation for format details. 
path = './example_spectra/Set1/'
files = [f'{path}spec{d}.asc' for d in range(1,6)]

UI = fitUI(files)
UI() # run the fitting program with default configuration 

# The Minuit object can be accessed by UI.m to get final values, errors, etc. 
# For more information see the iminuit documentation
# Example: iterate over values and errors:
for key, value, error in zip(UI.m.parameters, UI.m.values, UI.m.errors):
    print(f"{key} = {value} ± {error}")


""" Exapmles:
With command line arguments:
> python default_example.py "[350,390]" "[363,368]" example_fits/Set1/default

Without command line arguments:
> python default_example.py
input fit interval [350,390] 
input peak positions [363,368]
input save name example_fits/Set1/default

In both cases, the result is the same:

Fit function:
def fit_function2(x, slope,offset, A1,s1,m1, A2,s2,m2):
    background = slope*x + offset
    y1 = (A1/(s1*np.sqrt(2*np.pi)) * np.exp(-0.5*(x-m1)**2/s1**2))
    y2 = (A2/(s2*np.sqrt(2*np.pi)) * np.exp(-0.5*(x-m2)**2/s2**2))
    total = background + y1+y2
    return(total)

Fit complete. Remember to check the Migrad output in example_fits/Set1/default.txt.

slope_0 = -2.3005498110277465 ± 0.3105539649406107
offset_0 = 1768.7915905346078 ± 115.76175239855863
A1_0 = 2190.700972578853 ± 76.9826568259682
s1 = 1.8499353307638684 ± 0.016709838774444524
m1 = 362.4063708787371 ± 0.015847938540785023
A2_0 = 8284.974553335034 ± 91.04750698969929
s2 = 1.3698320214990352 ± 0.012625323888316307
m2 = 367.67381780344533 ± 0.012613678493807904
slope_1 = -3.0946676038689964 ± 0.31067382214456307
offset_1 = 2053.009715416164 ± 115.87158238237863
A1_1 = 3699.0891323168294 ± 83.62849593382657
A2_1 = 5785.366189489763 ± 81.82951387249204
slope_2 = -3.6471311475122716 ± 0.32301865169103006
offset_2 = 2317.6105118669557 ± 120.52959378135205
A1_2 = 5870.282694463294 ± 94.73407668549999
A2_2 = 4814.13923905114 ± 79.9966950493158
slope_3 = -4.048945750560593 ± 0.3364718804759673
offset_3 = 2536.135611346107 ± 125.59234360883256
A1_3 = 8468.851125824796 ± 107.01874296258211
A2_3 = 3154.5263900112964 ± 74.9819827066467
slope_4 = -4.029097554789109 ± 0.3275712742393478
offset_4 = 2468.242457861727 ± 122.3032197337261
A1_4 = 9525.022535358125 ± 108.1361070679086
A2_4 = 1472.568782973582 ± 65.28697190702337

"""
