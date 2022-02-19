import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.insert(0,'../GammaPeakFit')
from .fitting import Spectrum, MakeChi2
from iminuit import Minuit
from iminuit.util import describe
from pathlib import Path
import os

# Inputs
# TODO: read this from an input file
spc_names = [30,52,89,155,264,450,780,1170,1776,2650]
dist_values = np.array([29.8,51.6,89.9,155,264,449,776,1170,1776,2651]) + 25.89/2
path = './spectra/'
files = [path+f'{d}um.asc' for d in spc_names]
N_spc = len(spc_names)

try:
    interval = eval(sys.argv[1])
    m_init = eval(sys.argv[2])
    savename = sys.argv[3]
except IndexError:
    # TODO: Let user select interval and initial values in iteractive graph GUI
    interval = eval(input("input fit interval "))
    m_init = eval(input("input peak positions "))
    savename = input("input save name ")
N_peaks = len(m_init)

# Create savename path if it doesn't exist and check for inuse names
validname = False
while not validname:
    if os.path.isfile(f'{savename}.txt'):
        print(f"The file {savename}.txt already exists. Please input a new save name, or press enter to overwrite the existing files.")
        newname = input()
        if newname == '':
            validname = True
        else:
            savename = newname
    else:
        validname = True
savepath = savename.rpartition('/')[0]
Path(savepath).mkdir(parents=True,exist_ok=True)


# Fit functions.

def make_fit_function(N_peaks):
    # return a string which can be executed as a fit function with a give number of gaussian peaks
    args = []
    peaks = []
    total = []
    newlinetab = '\n    ' # f-string expression part cannot include a backslash
    for i in range(1,N_peaks+1):
        args += [f'A{i},s{i},m{i}']
        peaks += [f'y{i} = (A{i}/(s{i}*np.sqrt(2*np.pi)) * np.exp(-0.5*(x-m{i})**2/s{i}**2)) ']
        total += [f'y{i}']
    function_string = f"""def fit_function{N_peaks}(x, slope,offset, {', '.join(args)}):
    background = slope*x + offset
    {newlinetab.join(peaks)}
    total = background + {'+'.join(total)}
    return(total)
    """
    return(function_string)

function_string = make_fit_function(N_peaks)
print("\nFit function:")
print(function_string)
exec(function_string)


spectra = [Spectrum(file) for file in files]
Fit = MakeChi2(spectra)
# Create the combined chi2 minimisation function. The list indicates which parameters should be fitted individually for each spectrum.
# Any change in this list must be reflected in the 'args' dict in the Plotting Loop.
def listall(param: str):
    return([f'{param}{i}' for i in range(1,N_peaks+1)])

Chi2 = Fit.Chi2(interval,eval(f'fit_function{N_peaks}'),[*listall('A'),'slope','offset'])

# Set Initial Values
initial_values = {}
## parameters which are the same for all spectra
for i in range(1,N_peaks+1):
    initial_values[f'm{i}'] = m_init[i-1]
    initial_values[f's{i}'] = 1
## parameters which are fitted individually
initial_values.update(dict.fromkeys([kw for kw in Fit.keywords if kw.startswith('A')],1e3))
initial_values.update(dict.fromkeys([kw for kw in Fit.keywords if kw.startswith('slope')],-1))
initial_values.update(dict.fromkeys([kw for kw in Fit.keywords if kw.startswith('offset')],1000))
#initial_values.update(dict.fromkeys([kw for kw in Fit.keywords if kw.startswith('m2')],651))
#initial_values.update(dict.fromkeys([kw for kw in Fit.keywords if kw.startswith('s2')],2))



# Fitting


## create and initialise minuit object
m = Minuit(Chi2,**initial_values)

## set fixed parameters and parameter limits
for i in range(N_spc):
    for j in range(1,N_peaks+1):
        m.limits[f'A{j}_{i}'] = (0,None)
    #m.fixed[f'slope_{i}'] = True ; m.values[f'slope_{i}'] = 0
    #m.fixed[f'A1_{i}'] = True ; m.values[f'A1_{i}'] = 0
    #m.fixed['m1'] = True ; m.fixed['s1'] = True



def plot_fit2(ax,x,N_peaks,spc,kwargs: dict):
    # Plot fit for an arbitrary number of peaks
    # NOTE : only reads specific keys from kwargs. Other values are ignored
    background = kwargs[f'slope_{spc}']*x + kwargs[f'offset_{spc}']
    peaks = np.zeros([N_peaks,len(x)])
    for i in range(N_peaks):
        A = kwargs[f'A{i+1}_{spc}']
        s = kwargs[f's{i+1}']
        m = kwargs[f'm{i+1}'] # m is the mean, not a Minuit object. TODO: consistent naming and indexing
        peaks[i,:] = A/(s*np.sqrt(2*np.pi)) * np.exp(-0.5*(x-m)**2/s**2)
        ax.plot(x,peaks[i,:])
    total = background + np.sum(peaks,axis=0)
    ax.plot(x,background)
    ax.plot(x,total)
    data = spectra[spc]()
    ax.step(data[0],data[1],where='mid')
    ax.set_ylim(top=1.2*max(total))

## perform fit and write results to file
m.migrad(iterate=20)
with open(f"{savename}.txt",'w') as outfile:
    print(f"{interval = } \t {m_init = }\n", file=outfile)
    print(m.fmin, file=outfile)
    print(m.params, file=outfile)
    print(m.covariance, file=outfile)
    outfile.close()

if m.valid:
    print(f"Fit complete. Remember to check the Migrad output in {savename}.txt.\n")
else:
    raise UserWarning(f"Fit failed. Check the Migrad output in {savename}.txt for specifics.\n")

# Write peak areas to file
fmt = '\t'.join(['%8.3f '] + 2*N_peaks*['%10.4f '])
header = '\t'.join( ["distance"] + [f"    A{i}\t    err{i}" for i in range(1,N_peaks+1)] )
Adata = np.zeros([N_spc,2*N_peaks+1])
Adata[:,0] = dist_values
for i in range(N_spc):
    for j in range(N_peaks):
        Adata[i,2*j+1] = m.values[f'A{j+1}_{i}']
        Adata[i,2*j+2] = m.errors[f'A{j+1}_{i}']
np.savetxt(f'{savename}.tsv',Adata,fmt=fmt,header=header)

# Plotting Loop
for i in range(N_spc):
    fig,ax = plt.subplots()

    data = spectra[i]()
    ax.step(data[0],data[1],where='mid')

    x = np.linspace(interval[0],interval[1],300)
    kwargs = dict(zip(m.parameters[:],m.values[:]))
    plot_fit2(ax,x,N_peaks,i,kwargs)

    ax.set_xlim(interval)
    ax.set_xlabel("Energy [keV]")
    ax.set_ylabel("counts per 0.5 keV")
    plt.savefig(f'{savename}_{spc_names[i]}um.eps',format='eps')
    
    plt.show()

