from iminuit import Minuit
from iminuit.util import describe
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
import sys

from .fitting import Spectrum, MakeChi2

class UI(object):
    
    def __init__(self,files):
        self.files = files
        self.N_spec = len(files)
        self.spec_names = [file.rpartition('/')[-1].rpartition('.')[0] for file in self.files]

    def __call__(self):
        # Default usage, made for the RDDS measurements with reasonably clean spectra.
        self.get_input()
        self.scout_savepath()
        self.make_Gaussian()
        print("\nFit function:")
        print(self.function_string)
        exec(self.function_string)
        self.make_chi2(eval(self.function_name))
        self.set_initial_values()
        self.fit()
        self.save()

    def get_input(self):
        # Get fit interval, approximate peak positions and save location from user.
        try:
            self.interval = eval(sys.argv[1])
            self.m_init = eval(sys.argv[2])
            self.savename = sys.argv[3]
        except IndexError:
            # TODO: Let user select interval and initial values in interactive graph GUI
            self.interval = eval(input("input fit interval "))
            self.m_init = eval(input("input peak positions "))
            self.savename = input("input save name ")
        self.N_peaks = len(self.m_init)

    def scout_savepath(self):
        # Create savename path if it doesn't exist and check for inuse names
        validname = False
        while not validname:
            if os.path.isfile(f'{self.savename}.txt'):
                print(f"The file {self.savename}.txt already exists. Please input a new save name, or press enter to overwrite the existing files.")
                newname = input()
                if newname == '':
                    validname = True
                else:
                    self.savename = newname
            else:
                validname = True
        savepath = self.savename.rpartition('/')[0]
        Path(savepath).mkdir(parents=True,exist_ok=True)

    def listall(self,param: str):
        return([f'{param}{i}' for i in range(1,self.N_peaks+1)])

    def make_chi2(self, fit_function: callable):
        self.spectra = [Spectrum(file) for file in self.files]
        self.Fit = MakeChi2(self.spectra)
        # Create the combined chi2 minimisation function. The list indicates which parameters should be fitted individually for each spectrum.
        self.Chi2 = self.Fit.Chi2(self.interval,fit_function,[*self.listall('A'),'slope','offset'])

    def set_initial_values(self):
        # Set Initial Values
        self.initial_values = {}
        ## parameters which are the same for all spectra
        for i in range(1,self.N_peaks+1):
            self.initial_values[f'm{i}'] = self.m_init[i-1]
            self.initial_values[f's{i}'] = 1
        ## parameters which are fitted individually
        self.initial_values.update(dict.fromkeys([kw for kw in self.Fit.keywords if kw.startswith('A')],1e3))
        self.initial_values.update(dict.fromkeys([kw for kw in self.Fit.keywords if kw.startswith('slope')],-1))
        self.initial_values.update(dict.fromkeys([kw for kw in self.Fit.keywords if kw.startswith('offset')],1000))

    def fit(self):
        self.m = Minuit(self.Chi2,**self.initial_values)
        ## set fixed parameters and parameter limits
        for i in range(self.N_spec):
            for j in range(1,self.N_peaks+1):
                self.m.limits[f'A{j}_{i}'] = (0,None) 
        self.m.migrad(iterate=20)
        ## Inform user of fit status.
        if self.m.valid:
            print(f"Fit complete. Remember to check the Migrad output in {self.savename}.txt.\n")
        else:
            raise UserWarning(f"Fit failed. Check the Migrad output in {self.savename}.txt for specifics.\n")

    def save(self, display=True):
        # Write Migrad output to .txt file
        with open(f"{self.savename}.txt",'w') as outfile:
            print(f"{self.interval = } \t {self.m_init = }\n", file=outfile)
            print(self.m.fmin, file=outfile)
            print(self.m.params, file=outfile)
            print(self.m.covariance, file=outfile)
        # Make and save plots of the fits as .eps files
        for i, (spec, spec_name) in enumerate(zip(self.spectra,self.spec_names)):
            fig,ax = plt.subplots()
            data = spec()
            ax.step(data[0],data[1],where='mid')
            x = np.linspace(self.interval[0],self.interval[1],300)
            kwargs = dict(zip(self.m.parameters[:],self.m.values[:]))
            self.plot_fit2(ax,x,i,kwargs)
            ax.set_xlim(self.interval)
            ax.set_xlabel("Energy [keV]")
            ax.set_ylabel("counts per 0.5 keV")
            plt.savefig(f'{self.savename}_{spec_name}um.eps',format='eps')
            if display:
                plt.show()

    def make_Gaussian(self):
        # return a string which can be executed as a fit function with a give number of gaussian peaks
        args = []
        peaks = []
        total = []
        newlinetab = '\n    ' # f-string expression part cannot include a backslash
        for i in range(1,self.N_peaks+1):
            args += [f'A{i},s{i},m{i}']
            peaks += [f'y{i} = (A{i}/(s{i}*np.sqrt(2*np.pi)) * np.exp(-0.5*(x-m{i})**2/s{i}**2)) ']
            total += [f'y{i}']
        self.function_name = f"fit_function{self.N_peaks}"
        self.function_string = f"""def {self.function_name}(x, slope,offset, {', '.join(args)}):
    background = slope*x + offset
    {newlinetab.join(peaks)}
    total = background + {'+'.join(total)}
    return(total)
        """

    def plot_fit2(self,ax,x,spc,kwargs: dict):
        # Plot fit for an arbitrary number of peaks
        # NOTE : only reads specific keys from kwargs. Other values are ignored
        background = kwargs[f'slope_{spc}']*x + kwargs[f'offset_{spc}']
        peaks = np.zeros([self.N_peaks,len(x)])
        for i in range(self.N_peaks):
            A = kwargs[f'A{i+1}_{spc}']
            s = kwargs[f's{i+1}']
            m = kwargs[f'm{i+1}'] # m is the mean, not a Minuit object. TODO: consistent naming and indexing
            peaks[i,:] = A/(s*np.sqrt(2*np.pi)) * np.exp(-0.5*(x-m)**2/s**2)
            ax.plot(x,peaks[i,:])
        total = background + np.sum(peaks,axis=0)
        ax.plot(x,background)
        ax.plot(x,total)
        data = self.spectra[spc]()
        ax.step(data[0],data[1],where='mid')
        ax.set_ylim(top=1.2*max(total))
