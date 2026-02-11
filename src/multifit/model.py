from itertools import chain
from typing import Self

from iminuit.util import describe, make_with_signature
import numpy as np
import pytest

from .interface import import_cdf

class Model:
    """ Manage independent and shared parameters.

    Public attributes:
    independent_params: set -- parameters which are not shared
    unique_params: set -- parameters which are shared accross all peaks
        and spectra.
    spectrum_params: set -- parameters which are shared between peaks
        within, but not accross, spectra.
    peak_params: set -- parameters which are shared accross spectra, but
        are different for each peak number.
    """
    def __init__(self, cdf, *, spectrum_params, peak_params):
        """Constructor for the Model class.

        Keyword arguments:
        cdf -- Cumulative density function for the model distribution.
            Of the form f(x, par0, par1, ...)

        Keyword only arguments:
        spectrum_params -- Parameters to be shared by all peaks using
            this model within a single spectrum. Must match parameter
            names in cdf.
        peak_params -- Parameters to be shared by each peak of the same
            number accross all spectra. Must match parameter names in cdf.
        """
        self.cdf = cdf
        spectrum_params = set(spectrum_params)
        peak_params = set(peak_params)

        signature = describe(self.cdf, annotations=True)
        if not signature:
            raise ValueError(
                "Could not detect the signature for cdf. Signatures can"
                "be defined manually through obj._parameters.")
        all_params = set(signature)
        if (missing := (spectrum_params | peak_params) - all_params):
            raise ValueError(
                f"The parameters {missing} were not found in the signature "
                "for cdf. If the signature was not detected correctly "
                "try defining it manually through obj._parameters. "
                "The detected signature was:\n"
                f"{signature}")


        self.independent_params = all_params - spectrum_params - peak_params
        self.unique_params = spectrum_params & peak_params
        self.spectrum_params = spectrum_params - self.unique_params
        self.peak_params = peak_params - self.unique_params
#        print(f"{self.independent_params = }")
#        print(f"{self.unique_params = }")
#        print(f"{self.peak_params = }")
#        print(f"{self.spectrum_params = }")


    @classmethod
    def from_config(cls, config: dict) -> Self:
        return cls(
            import_cdf(config),
            spectrum_params=config['model']['spectrum_params'],
            peak_params=config['model']['peak_params']
            )

    def make_cdf(
            self, *,
            peak_number: int,
            spectrum_number: int
            ) -> callable:
        """Return the cdf with the proper signature.

        Define a function to be used by iminuit.cost.ExtendedBinnedNLL,
        with a signature ensuring the correct sharing of parameters.

        Arguments:
        peak_number -- number identifying a specific peak. Peaks with
            the same peak_number will share peak_params.
        spectrum_number -- number identifying a specific spectrum. Peaks
            with the same spectrum number will share spectrum_params.
        """
        replacements = {}
        for param in chain(
            self.unique_params, self.independent_params, self.spectrum_params,
            self.peak_params):
            replacements[param] = self.match_param(
                param, peak_number, spectrum_number)[0] # unpack from list
        return make_with_signature(self.cdf, **replacements)

    def match_param(self, string, peak_numbers, spectrum_numbers) -> list[str]:
        """List parameters matching string given peak and spectrum numbers.

        Arguments:
        string -- see expand_and_list()
        peak_numbers -- numbers of the peaks against which string is matched.
        spectrum_numbers -- numbers of the spectra against which string is matched.

        Returns:
        A list of valid parameter names to the function returned by
        make_integral for each combination of peak and spectrum number.
        """
        peak_numbers = np.atleast_1d(peak_numbers)
        spectrum_numbers = np.atleast_1d(spectrum_numbers)
        elements = self.expand_and_list(string)

        name = elements[0]
        if elements[1] == slice(None):
            selected_p = peak_numbers
        else:
            selected_p = [elements[1]]
        if elements[2] == slice(None):
            selected_s = spectrum_numbers
        else:
            selected_s = [elements[2]]

        if name in self.unique_params:
            return [f'{name}_*_*']
        if name in self.spectrum_params:
            return [f'{name}_*_{s}' for s in selected_s]
        if name in self.peak_params:
            return [f'{name}_{p}_*' for p in selected_p]
        if name in self.independent_params:
            return [f'{name}_{p}_{s}'
                    for p in selected_p for s in selected_s]

        raise ValueError(f"Expression {string} doesn’t match any parameters.")

    def expand_and_list(self, string) -> list:
        """Expand a parameter name as a list [name, peak, spectrum].

        Argument:
        string -- On the form <name> or <name>_<peak>_<spectrum>, where
            <peak> and <spectrum> can be numbers or wildcard '*'.
            The input <name> is equivalent to <name>_*_*

        Returns:
        A list [
            name: str,
            peak: int | slice(None),
            spectrum: int | slice(None) ]
        corresponding to the input string.
        """
        elements = string.split('_')
        if '' in elements or len(elements) not in (1, 3):
            raise ValueError(
                f"Cannot parse expression {string}. "
                "Format sould be either 'name_peak_spectrum' or 'name' "
                "(equivalent to 'name_*_*'. The wildcard '*' is allowed.")
        if (name := elements[0]) == '*':
            raise NotImplementedError(
                "Wildcards are not supported for the parameter name.")

        # Expand the list so all three selections are explicit
        if len(elements) == 1:
            elements += ['*']*2

        # Replace '*' with slice(None) so the output can be used for indexing.
        name = elements[0]
        selections = [slice(None) if e == '*' else int(e) for e in elements[1:]]
        return [name] + selections




# --------------------------------TESTS---------------------------------

@pytest.fixture
def simple_model():
    model = Model(
            lambda x, a, b, c, d: x > a,
            spectrum_params=('a', 'd'),
            peak_params=('b', 'd')
            )
    return model

def test_parameter_identification(simple_model):
    assert simple_model.spectrum_params == set(['a'])
    assert simple_model.peak_params == set(['b'])
    assert simple_model.independent_params == set(['c', 'x'])
    assert simple_model.unique_params == set(['d'])

''' Test for an older version, no longer valid.
def test_match_params(simple_model):
    inputs = list(chain.from_iterable(
        [[f'{y}', f'{y}_1', f'{y}_*', f'{y}_*_1',
          f'{y}_1_*', f'{y}_1_1', f'{y}_*_*']
         for y in ['a', 'b', 'c', 'd']]))
    sn = [1, 2, 3]
    pn = [4, 5, 6]
    expected = {}
    expected.update(dict.fromkeys(
        ['a', 'a_*', 'a_1_*', 'a_*_*'], [f'a_*_{s}' for s in sn]))
    expected.update(dict.fromkeys(['a_1', 'a_1_1', 'a_*_1'], ['a_*_1']))
    expected.update(dict.fromkeys(
        ['b', 'b_*', 'b_*_1', 'b_*_*'], [f'b_{p}' for p in pn]))
    expected.update(dict.fromkeys(['b_1', 'b_1_1', 'b_1_*'], ['b_1']))
    expected.update(dict.fromkeys(
        ['c', 'c_*', 'c_*_*'], [f'c_{p}_{s}' for p in pn for s in sn]))
    expected.update(dict.fromkeys(
        ['c_1', 'c_1_*'], [f'c_1_{s}' for s in sn]))
    expected['c_*_1'] = [f'c_{p}_1' for p in pn]
    expected['c_1_1'] = ['c_1_1']
    expected.update(dict.fromkeys([i for i in inputs if i.startswith('d')], ['d']))

    result = {}
    for i in inputs:
        result[i] = simple_model.match_param(
            i, spectrum_numbers=sn, peak_numbers=pn)
    assert result == expected
'''
