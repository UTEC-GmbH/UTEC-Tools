"""play with ChatGPT"""

# sourcery skip: avoid-global-variables

"""
I'm trying to get a list of available parameters from the python module 'wetterdienst'.
My code works, but the parameter names are in English. Is there a way to get them in German?
"""

from wetterdienst.provider.dwd.observation import DwdObservationRequest


def list_all_parameters() -> list[str]:
    """List of all availabel DWD-parameters

    (including parameters that a specific station might not have data for)
    """

    pars: list[str] = []
    for val in DwdObservationRequest.discover().values():
        pars += list(val.keys())
    pars = list(set(pars))

    return pars
