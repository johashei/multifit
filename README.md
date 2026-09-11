Multifit version 2 is a breaking rewrite of the code.

# multifit

A program for fitting the same distribution to multiple data sets simultaneously, with
the possibility of shared and independant parameters.

_This program is in developement, always sanity check your results.
Please use the issues page for bug reports, feature requests and questions.
A detailed documentation is coming ~~soon~~ eventually._

## Installation

multifit requires python 3.11 or higher.

Install multifit from PyPI with

```
pip install multifit
```

or install it in editable mode by cloning this repository and running
```
pip install -e .
```

## Usage

Use the multifit command line interface to make fits and view the results.
```
Usage: multifit [--version] [--copying] [--help] COMMAND [ARGS...]

Options:
    -h --help       Print the help screen for the given command and exit.
    --version       Print version number and exit.
    --copying       Print copyright notice and exit.

List of commands:
    config          Generate a new config file.
    fit             Fit a set of spectra.
    gate            Run a GUI for gating on coincidence spectra.
    plot            Plot a set of spectra, optionally including a fit result.
```

### The `fit` command
```
Usage: multifit fit CONFIG LOG [-v] [-r | -a] [--minos PARAM...]
                    [--strategy N] [--tries N] [--retries N]

    CONFIG              yaml configuration file.
    LOG                 json log file. By default, raises an error if
                        the file already exists.

    -h --help           Show this help screen and exit.
    -v --verbose        Print runtime information.
    -r --recreate       Replace an existing log file .
    -a --append         Append to an existing log file.
    --tries N           Number of times to run the migrad minimiser
                        before giving up. [default: 5]
    --strategy N        Strategy to use for the minimisation. Choices are
                        0 (fast), 1,  2 (careful). See the iminuit
                        documentation for details. [default: 1]
    --minos PARAM...    Calculate minos errors for the given parameters,
                        or use 'all' for all parameters (not usually
                        necessary). This can take several minutes.
    --retries N         Rerun migrad this number of times after a minimum
                        has been found. [default: 0]
```

### The `plot` command
```
Usage: multifit plot CONFIG [LOG] [--color MAP [--import MODULE]]
                     [--xlabel LABEL] [--ylabel LABEL]
                     [--callnumber N] [--background INDEX]

    -h --help           Print this help screen and exit.

Plotting options:
    -x --xlabel LABEL   Label on the x axis. [default: value]
    -y --ylabel LABEL   Label on the y axis. [default: counts per bin]
    -c --color MAP      Name of the colormap to use. [default: viridis]
    -i --import MODULE  Use a third party colormap from MODULE.

Fit selection options (only relevant if LOG is provided):
    --callnumber N      Number of the migrad iteration to plot. Starts
                        at 1, supports reverse indexing. [default: -1]
    -b --background INDEX
                        Use this component of the model cdf as the
                        background when plotting.
```
