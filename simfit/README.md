## New in version 0.3

Only `peakfit.py` has been modified.

- The program can now fit more than two peaks simultaneously
- The `.tsv` output file now includes a header
- The ordering of the areas in the `.tsv` output file corresponds to the order of the peak energies in the input
- Minor changes to terminal output

#### Example:

In the example spectra from <sup>110</sup>Ru, fit the peaks at 462, 472, 506 and 516 keV on the interval [454,525]

```
python peakfit.py "[454,525]" "[462,472,506,516]" Example/fit
```
If you leave out the arguments you will be prompted to enter them by the program.

This will create a directory "Example" and save figures of the ten fits as  `fit_30um.eps` ... `fit_2650um.eps`, the output of Migrad as `fit.txt` and the distance, area and standard deviation of the peaks as `fit.tsv`.   



