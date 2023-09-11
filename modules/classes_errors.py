"""Custom Error Messages"""


class NotFoundError(Exception):
    """Error Message if an entry is not found"""

    def __init__(self, entry: str, where: str) -> None:
        """Initiate"""
        super().__init__(f"Error: requested object '{entry}' not found in '{where}'.")


class WrongColumnNamesError(Exception):
    """Error Message if a DataFrame doesn't have the expected columns"""

    def __init__(self, column_name: str | None) -> None:
        """Initiate"""
        if column_name:
            super().__init__(f"Error: column '{column_name}' not found in DataFrame.")
        else:
            super().__init__("Error: wrong columns in DataFrame.")


class NoDWDParameterError(Exception):
    """Error Message if a given meteorological parameter
    is not a valid DWD parameter name.
    """

    def __init__(self, parameter: str) -> None:
        """Initiate"""
        super().__init__(f"'{parameter}' is not a valid DWD-Parameter name!")


class NoValuesForParameterError(Exception):
    """Error Message if no values for a given meteorological parameter
    can be found.
    """

    def __init__(self, **kwargs) -> None:
        """Initiate"""
        err_msg: str = "No values found."
        for key, value in kwargs.items():
            err_msg += f" \n{key}: '{value}'"

        super().__init__(err_msg)
