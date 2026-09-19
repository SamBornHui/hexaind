from enum import Enum, auto
from typing import Any, List


class VisualizationType(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    DISTRIBUTION = auto()
    SPLINEFIT = auto()
    LINEARFIT = auto()
    CONTOUR = auto()
    BOX_PLOT = auto()
    SCATTER_PLOT = auto()
    HISTOGRAM = auto()
    IQR_PLOT = auto()
