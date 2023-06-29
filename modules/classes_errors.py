"""Custom Error Messages"""


class NotFoundError(Exception):
    """Error Message if an entry is not found"""

    def __init__(self, entry: str, where: str) -> None:
        """Initiate"""
        super().__init__(f"Error: requested object '{entry}' not found in '{where}'.")


class NoDWDParameterError(Exception):
    """Error Message if a given meteorological parameter
    is not a valid DWD parameter name.
    """

    def __init__(self, parameter: str) -> None:
        """Initiate"""
        super().__init__(f"'{parameter}' is not a valid DWD-Parameter name!")


class NotAvailableInResolutionError(Exception):
    """Error Message if a given meteorological parameter
    is not available in the requested temporal resolution.
    """

    def __init__(
        self, parameter: str, resolution: str, available_resolutions: list[str]
    ) -> None:
        """Initiate"""
        super().__init__(
            f"Parameter '{parameter}' not available in '{resolution}' resolution! \n"
            f"Available resolutions are: {available_resolutions}"
        )
