from enum import Enum, auto
from typing import Any, List


class DataType(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    CSV = auto()
    PARQUET = auto()
    EXCEL = auto()
