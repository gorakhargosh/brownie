# coding: utf-8
"""
    brownie.functional
    ~~~~~~~~~~~~~~~~~~

    Implements functions known from functional programming languages and other
    things which are useful when dealing with functions.

    :copyright: 2010 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from inspect import getargspec
from functools import wraps

from brownie.pycompat import reduce


def compose(*functions):
    """
    Returns a function which acts as a composition of several `functions`. If
    one function is given it is returned if no function is given a
    :exc:`TypeError` is raised.

    >>> from brownie.functional import compose
    >>> compose(lambda x: x + 1, lambda x: x * 2)(1)
    3

    .. note:: Each function (except the last one) has to take the result of the
              last function as argument.
    """
    if not functions:
        raise TypeError('expected at least 1 argument, got 0')
    elif len(functions) == 1:
        return functions[0]
    return reduce(lambda f, g: lambda *a, **kws: f(g(*a, **kws)), functions)


def flip(function):
    """
    Returns a function which behaves like `function` but gets the given
    positional arguments reversed; keyword arguments are passed through.

    >>> from brownie.functional import flip
    >>> def f(a, b): return a
    >>> f(1, 2)
    1
    >>> flip(f)(1, 2)
    2
    """
    @wraps(function)
    def wrap(*args, **kwargs):
        return function(*reversed(args), **kwargs)
    return wrap


def get_signature(func):
    """
    Takes a function or method and returns the signature as a tuple containing
    the following items:

    1. A list of required positional parameters.
    2. A list containing the keyword arguments, each as a tuple containing the
       name and default value, in order of their appearance in the function
       definition.
    3. The name used for arbitrary positional arguments or `None`.
    4. The name used for arbitary keyword arguments or `None`.

    .. versionadded:: 0.5
    """
    func = getattr(func, 'im_func', func)
    params, varargs, varkwargs, defaults = getargspec(func)
    defaults = [] if defaults is None else defaults
    index = 0 if len(defaults) == len(params) else len(defaults) or len(params)
    return (
        params[:index],
        zip(params[index:], defaults),
        varargs,
        varkwargs
    )


def bind_arguments(func, args=(), kwargs=None):
    """
    Returns a dictionary with the names of the parameters as keys with
    their arguments as values.

    Raises a :exc:`ValueError` if there are too many `args` and/or `kwargs`
    that are missing or repeated.

    .. versionadded:: 0.5
    """
    kwargs = {} if kwargs is None else kwargs
    positionals, kwparams, varargs, varkwargs = get_signature(func)

    required = set(positionals)
    overwritable = set(name for name, default in kwparams)
    settable = required | overwritable

    positional_count = len(positionals)
    kwparam_count = len(kwparams)
    arg_count = len(args)

    result = dict(kwparams, **dict(zip(positionals, args)))

    remaining = args[positional_count:]
    for (param, _), arg in zip(kwparams, remaining):
        result[param] = arg
        overwritable.discard(param)
    if len(remaining) > kwparam_count:
        if varargs is None:
            raise ValueError(
                'expected at most %d positional arguments, got %d' % (
                    positional_count + kwparam_count,
                    len(args)
                )
            )
        else:
            result[varargs] = tuple(remaining[kwparam_count:])

    remaining = {}
    unexpected = []
    for key, value in kwargs.iteritems():
        if key in result and key not in overwritable:
            raise ValueError("got multiple values for '%s'" % key)
        elif key in settable:
            result[key] = value
        elif varkwargs:
            result_kwargs = result.setdefault('kwargs', {})
            result_kwargs[key] = value
        else:
            unexpected.append(key)
    if len(unexpected) == 1:
        raise ValueError(
            "got unexpected keyword argument '%s'" % unexpected[0]
        )
    elif len(unexpected) == 2:
        raise ValueError(
            "got unexpected keyword arguments '%s' and '%s'" % tuple(unexpected)
        )
    elif unexpected:
        raise ValueError("got unexpected keyword arguments %s and '%s'" % (
            ', '.join("'%s'" % arg for arg in unexpected[:-1]), unexpected[-1]
        ))

    if set(result) < set(positionals):
        missing = set(result) ^ set(positionals)
        if len(missing) == 1:
            raise ValueError("'%s' is missing" % missing.pop())
        elif len(missing) == 2:
            raise ValueError("'%s' and '%s' are missing" % tuple(missing))
        else:
            missing = tuple(missing)
            raise ValueError("%s and '%s' are missing" % (
                ', '.join("'%s'" % name for name in missing[:-1]), missing[-1]
            ))
    if varargs:
        result.setdefault(varargs, ())
    if varkwargs:
        result.setdefault(varkwargs, {})
    return result


__all__ = ['compose', 'flip', 'get_signature', 'bind_arguments']
