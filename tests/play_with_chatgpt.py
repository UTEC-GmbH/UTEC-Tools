"""play with ChatGPT"""

# sourcery skip: avoid-global-variables, name-type-suffix
# pylint: disable=W0105,C0413
# ruff: noqa: E402, E501, RUF100


# I have a dictionary, that stores parameters and their units for every resolution:

resolutions: dict = {
    "resoltuion_1": {
        "parameter_1": {"unit": "unit_1", "alt_unit": "alt_unit_1"},
        "parameter_2": {"unit": "unit_2", "alt_unit": "alt_unit_2"},
    },
    "resoltuion_2": {
        "parameter_1": {"unit": "unit_1", "alt_unit": "alt_unit_1"},
        "parameter_2": {"unit": "unit_2", "alt_unit": "alt_unit_2"},
        "parameter_3": {"unit": "unit_3", "alt_unit": "alt_unit_3"},
    },
}

# I want to convert the resolutions dictionary to a dictionary that stores
# the parameters instead like this:

parameter: dict = {
    "parameter_1": {
        "resoltuion": {"resoltuion_1", "resoltuion_2"},
        "unit": "unit_1",
        "alt_unit": "alt_unit_1",
    },
    "parameter_2": {
        "resoltuion": {"resoltuion_1", "resoltuion_2"},
        "unit": "unit_2",
        "alt_unit": "alt_unit_2",
    },
    "parameter_3": {
        "resoltuion": {"resoltuion_2"},
        "unit": "unit_3",
        "alt_unit": "alt_unit_3",
    },
}

# How can I do this in python?
