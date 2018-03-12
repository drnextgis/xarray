"""Base classes implementing arithmetic for xarray objects."""
from __future__ import absolute_import, division, print_function

import numbers

import numpy as np

from .options import OPTIONS
from .pycompat import bytes_type, dask_array_type, unicode_type
from .utils import not_implemented


class SupportsArithmetic(object):
    """Base class for xarray types that support arithmetic.

    Used by Dataset, DataArray, Variable and GroupBy.
    """

    # TODO: implement special methods for arithmetic here rather than injecting
    # them in xarray/core/ops.py. Ideally, do so by inheriting from
    # numpy.lib.mixins.NDArrayOperatorsMixin.

    # TODO: allow extending this with some sort of registration system
    _HANDLED_TYPES = (np.ndarray, np.generic, numbers.Number, bytes_type,
                      unicode_type) + dask_array_type

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        from .computation import apply_ufunc

        # See the docstring example for numpy.lib.mixins.NDArrayOperatorsMixin.
        out = kwargs.get('out', ())
        for x in inputs + out:
            if not isinstance(x, self._HANDLED_TYPES + (SupportsArithmetic,)):
                return NotImplemented

        if ufunc.signature is not None:
            raise NotImplementedError(
                '{} not supported: xarray objects do not directly implement '
                'generalized ufuncs. Instead, use xarray.apply_ufunc.'
                .format(ufunc))

        if method != '__call__':
            # TODO: support other methods, e.g., reduce and accumulate.
            raise NotImplementedError(
                '{} method for ufunc {} is not implemented on xarray objects, '
                'which currently only support the __call__ method.'
                .format(method, ufunc))

        if any(isinstance(o, SupportsArithmetic) for o in out):
            # TODO: implement this with logic like _inplace_binary_op. This
            # will be necessary to use NDArrayOperatorsMixin.
            raise NotImplementedError(
                'xarray objects are not yet supported in the `out` argument '
                'for ufuncs.')

        join = dataset_join = OPTIONS['arithmetic_join']

        return apply_ufunc(ufunc, *inputs,
                           input_core_dims=((),) * ufunc.nin,
                           output_core_dims=((),) * ufunc.nout,
                           join=join,
                           dataset_join=dataset_join,
                           dataset_fill_value=np.nan,
                           kwargs=kwargs,
                           dask='allowed')

    # this has no runtime function - these are listed so IDEs know these
    # methods are defined and don't warn on these operations
    __lt__ = __le__ = __ge__ = __gt__ = __add__ = __sub__ = __mul__ = \
        __truediv__ = __floordiv__ = __mod__ = __pow__ = __and__ = __xor__ = \
        __or__ = __div__ = __eq__ = __ne__ = not_implemented
