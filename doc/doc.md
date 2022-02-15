#

## The fit function

In order to fit an arbitrary number of peaks, the fit function is generated at runtime. This is necessary when sharing parameters between fits, as these are identified by name. 

The fit function is written as a string which is then executed to define the function. 