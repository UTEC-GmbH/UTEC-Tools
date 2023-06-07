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
