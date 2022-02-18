import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc
from iminuit import Minuit
from iminuit.cost import LeastSquares
from iminuit.util import make_with_signature, describe


class Spectrum(object):
    """
    Read spectra from ascii file,
    Place counts and energy of bins in 1d arrays,
    Add spectra together,
    """
    def __init__(self,filename,keV_per_channel=0.5,energy_offset=0):
        self.channel,self.counts = np.loadtxt(filename,unpack=True,delimiter=',')
        self.N_bins = len(self.channel)
        # Place energy value at the centre of each channel
        self.keV_per_channel = keV_per_channel
        self.energy = (self.channel + 0.5)*keV_per_channel
    
    def __call__(self,energy_range=None,channel_range=None):
        counts_err = np.sqrt(self.counts) # Assumes poisson distributed counting process
        if energy_range == None:
            if channel_range == None: 
                return_range = [None,None]
            else:
                return_range = channel_range
        elif channel_range == None: 
           return_range = (np.array(energy_range)/self.keV_per_channel).astype(int)
        else:
            raise ValueError("Specify energy range or channel range, not both.")
        return(self.energy[return_range[0]:return_range[1]],
               self.counts[return_range[0]:return_range[1]],
               counts_err[return_range[0]:return_range[1]],)

    def Add_spectrum(self,filename,weight):
        channel,counts = np.loadtxt(filename,unpack=True,delimiter=',')
        N_bins = len(channel)
        if N_bins != self.N_bins:
            raise RuntimeError(f"Cannot add spectrum from file {filename} with {N_bins} \
                                 bins to spectrum with {self.N_bins}. Spectra must have \
                                 the same number of bins.")

        self.counts += weight*counts



class MakeChi2(object):
    """
    Define fit function;
    Create combined chi squared function for fitting multiple spectra simultaneously; <- only does this so far
    Initialise parameters and perform fit
    """
    def __init__(self,spectra: list[Spectrum]):
        self.spectra = spectra
        self.N_spectra = len(spectra)
    

    def Chi2(self,energy_range,fit_function: callable,independent_params: list[str]):
        """
        Construct a combined chi squared function for fitting a fit function to all spectra.
        The fit function sould have separate scalar parameters. 
        Independent parameters are renamed for each spectrum.
        """
        chi2 = 0
        self.keywords = set()
        for i in range(self.N_spectra):
            new_names = [name+f'_{i}' for name in independent_params]
            self.keywords.update(new_names)
            name_changes = dict(zip(independent_params,new_names))           
            fit = make_with_signature(fit_function, **name_changes)
            energy,counts,counts_err = self.spectra[i](energy_range=energy_range)
            chi2 += LeastSquares(energy,counts,counts_err,fit)
        return(chi2)
  
        
