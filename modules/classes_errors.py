"""Custom Error Messages"""


class NoYearsError(Exception):
    """Error Message if there are no years in the metadata"""

    def __init__(self) -> None:
        """Initiate"""
        super().__init__("No list of years found in meta data.")


class MultipleLinesFoundError(Exception):
    """Error Message if multiple lines were found (e.g. get_line_by_name)"""

    def __init__(self, line_name: str) -> None:
        """Initiate"""
        super().__init__(f"Multiple lines with name '{line_name}' found.")


class LineNotFoundError(Exception):
    """Error Message if Line not found (e.g. change_line_attribute)"""

    def __init__(self, line_name: str) -> None:
        """Initiate"""
        super().__init__(f"Line '{line_name}' not found.")


class NotInSessionStateError(Exception):
    """Error Message if an entry is not found in the streamlit session state"""

    def __init__(self, entry: str) -> None:
        """Initiate"""
        super().__init__(f"Entry '{entry}' not found in Streamlit's Session State.")


class SecretNotFoundError(Exception):
    """Error Message if an entry is not found in the secrets"""

    def __init__(self, entry: str) -> None:
        """Initiate"""
        super().__init__(f"Entry '{entry}' not found in Secrets.")


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
