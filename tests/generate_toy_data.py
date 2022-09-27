import json
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import default_rng
import pandas as pd
import seaborn as sns

def main():

    with open("toy_data_config.json", 'r') as infile:
        config = json.load(infile)
    
    spc = ToySpectrum(config['spectrum']['min'], config['spectrum']['max'], config['spectrum']['nbins'])
    for peak in config['peaks']:
        spc.add_gaussian_peak(peak['area'], peak['mean'], peak['stddev'])
    spc.add_polynomial_background(config['background']['start'], config['background']['stop'], *config['background']['coefficients'])
    spc.apply_random_noise()
    spc.write_asc_file("toy_spectrum.asc")
    

    inspc = pd.read_csv("toy_spectrum.asc")
    inspc.rename(columns=lambda s: s.strip("#").strip(), inplace=True)
    fig,ax = plt.subplots()
    sns.relplot(data=inspc, x="value", y="counts", kind="line", drawstyle='steps-post')
    plt.show()

class ToySpectrum(object):
    def __init__(self, lower_limit, upper_limit, nbins):
        self.start_value = lower_limit
        self.bin_width = (upper_limit-lower_limit)/nbins
        self.spectrum = np.zeros([2,nbins])
        self.spectrum[0,:] = np.arange(lower_limit, upper_limit, self.bin_width)

    def add_gaussian_peak(self, area, mean, stddev):
        self.spectrum[1,:] += (area/(stddev*np.sqrt(2*np.pi)) * np.exp(-0.5*(self.spectrum[0,:]-mean)**2/stddev**2))

    def add_polynomial_background(self, start, stop, *coefficients):
        start_bin = int(np.floor((start - self.start_value)/self.bin_width))
        stop_bin = int(np.ceil((stop - self.start_value)/self.bin_width))
        self.spectrum[1, start_bin:stop_bin] += np.polynomial.polynomial.Polynomial(coefficients)(self.spectrum[0,:]) 

    def apply_random_noise(self):
        rng = default_rng()
        self.spectrum[1,:] = rng.poisson(self.spectrum[1,:])


    def write_asc_file(self, filename):
        np.savetxt(filename, self.spectrum.transpose(), fmt="%10.5f,%10d", header="   value,    counts")

if __name__ == '__main__':
    main()
