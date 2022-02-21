# multifit

The goal of Multifit is to provide a convenient way of calculating fits with shared parameters over multiple data sets. 

The actual fitting is all done using the `iminuit` package, and I recommend that you familiarise yourself with [their basic tutorial](https://iminuit.readthedocs.io/en/stable/tutorial/basic_tutorial.html).

## Installation

Install from PyPI repository (recommended)

```
pip install multifit
```

To install the developement version, clone this repository, `cd` to its root directory and run

```
pip install .
```

## Usage

Import the `UI` class and initialise it with a list containing the paths to the spectrum files.

```python
import multifit.UI as fitUI
paths_to_spectra = ['path/to/spectrum1/spec1.asc', 'path/to/spectrum2/spec2.asc']
UI = fitUI(paths_to_spectra)
```

Then, either call `UI()` to run the program with the default configuration, or call the methods in `UI` manually to have full control over the fit. This will be discussed below.

If the `get_input` method is called, the program will attempt to read certain arguments from the command line, and prompt the user to enter them if this fails. These are
`interval`: the interval of the data to fit. 
`m_init`: approximate values for the peak positions. 
`savename`: the location to save the results, with no file extention. 

Once the fit is complete, the results are contained in the Minuit object `UI.m`. See the _iminuit_ documentation for information on how to extract it.
Working examples are given in [doc/examples/](./doc/examples/).

#### The default configuration

In the default configuration, *multifit* can fit any number of peaks using Gaussian functions on a linear background. The mean and standard deviation of each peak is constant across all spectra. The peak areas and background parameters are fitted independently for each spectrum.

#### Configuring the fit manually

Each step of the fit, as well as the variables involved, can be accessed through the `UI` class. The following contains a description of some variables you may want to change. For more details, see [doc/reference.md](https://github.com/johashei/multifit/doc/reference.md)

<details>
<summary>clik to expand</summary>
<p>

- `self.function_string` : 
  This is a string which, when executed, defines the function to be fitted to the data. The function should take `x` as the first argument, followed by single parameters to fit. The program does not support array parameters, because the selection of common parameters is name based.
  The default string is created in `make_Gaussian(self)`. This method may be usefull as a template when creating your own fit functions.  

-  `self.Chi2`:
  This is the  χ<sup>2</sup> cost function which is minimised by `Migrad`. It is defined in `make_chi2(self, fit_function: callable`) as
  
  ```python
  self.Chi2 = self.Fit.Chi2(self.interval, fit_function, [*self.listall('A'),'slope','offset'])
  ```
  You will only want to change the last parameter, which is a list of the parameters to be fitted independently for each spectrum. By default these are the areas of all peaks and the background parameters.
  
- `self.initial_values`:
  This is a `dict` containing the initial values for all parameters of the fit. For those parameters which are fitted independantly, that is one value for each spectrum.
  The default is defined in `set_initial_values(self)`. It is recommended to copy and modify this function to generate custom initial values. 

- `self.m` attributes:
  `self.m.limits`: the limits of the fitted parameters, by default the peak areas are positive.
  `self.m.fixed`: can be used to fix the value of fitted parameters. `False` by default.
  `self.m.values`: the current values of the fitted parameters.
  See the *iminuit* documentation for more information.

</p>
</details>

 

