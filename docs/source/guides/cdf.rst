Writing density functions
=========================

The `multifit` utility lets you fit multiple instances of a model to a
dataset, with control over shared and independent parameters. The model
itself depends on the process being described and as such is left to the
user.

Because `multifit` is intended to fit binned data, the model must take
the form of a cumulative density function (CDF). The `numba-stats`_ package
implements jit-compiled CDFs for a number of common distributions, and is
a good place to start.

:Note: `multifit` plans to provide CDFs for some additional distributions,
       such as polynomials between limits.

.. _numba stats: https://github.com/scikit-hep/numba-stats


Use different models in the same dataset
----------------------------------------

If the data contains structures with different functional forms, but which
nevertheless gain from simultaneous fitting, one can introduce a switching
parameter selecting which function will be calculated, as for example

::

    def cdf_with_switching(x, c, p1, p2, p3):
        if c == 1:
            return cdf_1(x, p1, p2)
        else:
            return cdf_2(x, p1, p3)

Here, the switching parameter ``c`` determines which functional form is
used. This parameter can the be fixed in the input file for each instance
of a peak structure.




